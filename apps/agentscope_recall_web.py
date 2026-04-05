#!/usr/bin/env python3
"""FastAPI web UI for streaming AgentScope recall messages."""

import json
import sys
from pathlib import Path
from typing import Any, AsyncGenerator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from recipe_agentscope_recall import (
    DEFAULT_CLI_CONFIG_PATH,
    DEFAULT_DATA_PATH,
    DEFAULT_SERVER_CONFIG_PATH,
    create_recipe_and_agent,
    iter_agent_events,
)


class StreamRequest(BaseModel):
    """Request body for stream endpoint."""

    prompt: str = Field(..., description="User input prompt")
    server_config_path: str = Field(default=DEFAULT_SERVER_CONFIG_PATH)
    cli_config_path: str = Field(default=DEFAULT_CLI_CONFIG_PATH)
    data_path: str = Field(default=DEFAULT_DATA_PATH)


app = FastAPI(title="AgentScope Recall Visualizer")
templates = Jinja2Templates(directory="apps/templates")
app.mount("/static", StaticFiles(directory="apps/static"), name="static")


def _to_sse(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


async def _stream_agent_events(
    request: Request,
    payload: StreamRequest,
) -> AsyncGenerator[str, None]:
    """Stream normalized events for frontend rendering."""
    recipe, agent = await create_recipe_and_agent(
        server_config_path=payload.server_config_path,
        cli_config_path=payload.cli_config_path,
        data_path=payload.data_path,
    )

    text_cache: dict[str, str] = {}
    thinking_cache: dict[str, str] = {}
    pending_tool_use: dict[str, dict[str, Any]] = {}
    pending_tool_result: dict[str, dict[str, Any]] = {}

    try:
        async for event in iter_agent_events(agent=agent, prompt=payload.prompt):
            if await request.is_disconnected():
                break

            event_type = event.get("type")
            message_id = str(event.get("message_id", ""))
            is_last = bool(event.get("is_last", False))

            if event_type in ("text", "thinking"):
                raw_text = str(event.get("text", ""))
                cache = text_cache if event_type == "text" else thinking_cache
                prev = cache.get(message_id, "")
                delta = raw_text[len(prev) :] if raw_text.startswith(prev) else raw_text
                cache[message_id] = raw_text

                if delta or is_last:
                    yield _to_sse(
                        f"{event_type}_delta",
                        {
                            "message_id": message_id,
                            "delta": delta,
                            "is_last": is_last,
                        },
                    )
                continue

            if event_type == "tool_use":
                tool_call_id = str(event.get("id") or message_id)
                pending_tool_use[tool_call_id] = event
                if is_last:
                    full_event = pending_tool_use.pop(tool_call_id, event)
                    yield _to_sse(
                        "tool_use",
                        {
                            "message_id": message_id,
                            "tool_call_id": tool_call_id,
                            "tool_name": full_event.get("name"),
                            "arguments": full_event.get("input", {}),
                            "is_last": True,
                        },
                    )
                continue

            if event_type == "tool_result":
                tool_call_id = str(event.get("id") or message_id)
                pending_tool_result[tool_call_id] = event
                if is_last:
                    full_event = pending_tool_result.pop(tool_call_id, event)
                    yield _to_sse(
                        "tool_result",
                        {
                            "message_id": message_id,
                            "tool_call_id": tool_call_id,
                            "tool_name": full_event.get("name"),
                            "output": full_event.get("output"),
                            "is_last": True,
                        },
                    )
                continue

        yield _to_sse("done", {"ok": True})
    except Exception as exc:  # noqa: BLE001
        yield _to_sse("error", {"message": str(exc)})
    finally:
        await recipe.close()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the visualization page."""
    return templates.TemplateResponse(
        request=request,
        name="agentscope_recall.html",
        context={},
    )


@app.get("/api/chat/stream")
async def chat_stream_get(
    request: Request,
    prompt: str,
) -> StreamingResponse:
    """SSE endpoint for EventSource (GET-based)."""
    payload = StreamRequest(prompt=prompt)
    return StreamingResponse(
        _stream_agent_events(request=request, payload=payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/chat/stream")
async def chat_stream_post(
    request: Request,
    payload: StreamRequest,
) -> StreamingResponse:
    """SSE endpoint for fetch-stream clients (POST-based)."""
    return StreamingResponse(
        _stream_agent_events(request=request, payload=payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.agentscope_recall_web:app", host="0.0.0.0", port=8010)
