#!/usr/bin/env python3
"""
RAG Pipeline - Retrieval-Augmented Generation using AtomCtx + LLM
Focused on querying and answer generation, not resource management
"""
import json
import time
import subprocess
from typing import Any, AsyncGenerator, Dict, List, Optional
import requests
import atom_ctx as ctx
from atom_ctx_cli.utils.config.ctx_config import AtomCtxConfig
from pydantic import BaseModel, Field
# Import AgentScope modules
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import Msg
from agentscope.plan import PlanNotebook
import asyncio

DEFAULT_SERVER_CONFIG_PATH = "ctx.conf"
DEFAULT_CLI_CONFIG_PATH = "ctx-cli.conf"
DEFAULT_DATA_PATH = "ctx-data"

class RecipeResponse(BaseModel):
    answer: str = Field(description="你的最终答案；若无法回答则为 `无法回答`")
    target_uri: List[str] = Field(description="与最终答案直接相关的 URI 列表；无法回答时必须为 `[]`", default=[])

class Recipe:
    """
    Recipe (Boring name is RAG Pipeline)
    Combines semantic search with LLM generation:
    1. Search AtomCtx database for relevant context
    2. Send context + query to LLM
    3. Return generated answer with sources
    """
    def __init__(self, config_path: str = "./ctx.conf", data_path: str = "./data"):
        """
        Initialize RAG pipeline
        Args:
            config_path: Path to config file with LLM settings
            data_path: Path to AtomCtx data directory
        """
        # Load configuration
        with open(config_path, "r") as f:
            self.config_dict = json.load(f)
        # Extract LLM config
        self.vlm_config = self.config_dict.get("vlm", {})
        self.api_base = self.vlm_config.get("api_base")
        self.api_key = self.vlm_config.get("api_key")
        self.model = self.vlm_config.get("model")
        # Initialize AtomCtx client
        config = AtomCtxConfig.from_dict(self.config_dict)
        self.port = self.config_dict.get("server", {}).get("port")
        self.client = ctx.AsyncHTTPClient(url=f"http://localhost:{self.port}")
        
        
        # Store data_path as instance variable
        self.data_path = data_path
        
    async def search(
        self,
        query: str,
        target_uri: Optional[List[str]] = None,
    ) -> List[Any]:
        """
        Search for relevant content using semantic search
        Args:
            query: Search query
            target_uri: Optional specific URI list to search in. If None, searches all resources. e.g. '[ctx://resources/directory, ctx://resources/file]'
        Returns:
            ToolResponse with search results, including uri, score and content
        """
        score_threshold = 0.2
        
        if target_uri is None:
            results = await self.client.search(query, score_threshold=score_threshold)
            results = [results]
        elif target_uri and isinstance(target_uri, str):
            results = await self.client.search(query, target_uri=target_uri, score_threshold=score_threshold)
            results = [results]
        elif target_uri and isinstance(target_uri, list):
            results = []
            for uri in target_uri:
                result = await self.client.search(query, target_uri=uri, score_threshold=score_threshold)
                results.append(result)
        # Extract top results
        search_results = []
        top_k = 5
        for res in results:
            for _i, resource in enumerate(
                res.resources[:top_k]
            ):  # ignore SKILLs for mvp
                try:
                    content = await self.client.read(resource.uri)
                    search_results.append(
                        {
                            "uri": resource.uri,
                            "score": resource.score,
                            "content": content,
                        }
                    )
                    # print(f"  {i + 1}. {resource.uri} (score: {resource.score:.4f})")
                except Exception as e:
                    # Handle directories - read their abstract instead
                    if "is a directory" in str(e):
                        try:
                            abstract = await self.client.abstract(resource.uri)
                            search_results.append(
                                {
                                    "uri": resource.uri,
                                    "score": resource.score,
                                    "content": f"[Directory Abstract] {abstract}",
                                }
                            )
                            # print(f"  {i + 1}. {resource.uri} (score: {resource.score:.4f}) [directory]")
                        except:
                            # Skip if we can't get abstract
                            continue
                    else:
                        # Skip other errors
                        continue
        result = ToolResponse(
            content=[{"type": "text", "text": f"搜索结果: \n{json.dumps(search_results, indent=2)}"}]
        )
        return result

    async def ls(self, uri: str) -> ToolResponse:
        """
        List the contents of a directory
        Args:
            uri: URI of the directory to list, e.g. 'ctx://resources/directory'
        Returns:
            ToolResponse with list of uri, isDir, abstract
        """
        try:
            result = ToolResponse(
                content=[{"type": "text", "text": f"目录内容: \n{json.dumps(await self.client.ls(uri), indent=2)}"}]
            )
        except Exception as e:
            result = ToolResponse(
                content=[{"type": "text", "text": f"Error listing directory {uri}: {str(e)}"}]
            )
        return result

    async def tree(self, uri: str) -> ToolResponse:
        """
        Get the 1-level tree of the specified uri directory
        Args:
            uri: URI of the directory to get the tree of, e.g. 'ctx://resources/directory'
        Returns:
            ToolResponse with 1-level tree of the directory, including uri, isDir, rel_path and abstract
        """
        try:    
            result = ToolResponse(
                content=[{"type": "text", "text": f"目录树: \n{json.dumps(await self.client.tree(uri, show_all_hidden=True, level_limit=1), indent=2)}"}],
            )
        except Exception as e:
            result = ToolResponse(
                content=[{"type": "text", "text": f"Error getting tree of directory {uri}"}],
            )
        return result

    async def overview(self, uri: str) -> ToolResponse:
        """
        Get the overview of the specified uri
        Args:
            uri: URI of the resource to get the overview of, e.g. 'ctx://resources/file' or 'ctx://resources/directory'
        Returns:
            ToolResponse with overview of the resource
        """
        try:
            result = ToolResponse(
                content=[{"type": "text", "text": await self.client.overview(uri)}]
            )
        except Exception as e:
            result = ToolResponse(
                content=[{"type": "text", "text": f"Error getting overview of directory {uri}"}],
            )
        return result

    async def read(self, uri: str) -> ToolResponse:
        """
        Read the raw content of the specified uri
        Args:
            uri: URI of the resource to read, e.g. 'ctx://resources/file' or 'ctx://resources/directory'
        Returns:
            ToolResponse with raw content of the resource
        """
        try:
            
            result = ToolResponse(
                content=[{"type": "text", "text": await self.client.read(uri)}]
            )
        except Exception as e:
            result = ToolResponse(
                content=[{"type": "text", "text": f"Error reading content of {uri} {str(e)}"}],
            )
        return result

    async def close(self):
        """Clean up resources"""
        await self.client.close()

sys_prompt = """
你是一个面向文件系统资源的问答助手，主要负责企业内部知识库的问答。你的职责是基于工具检索到的内容回答用户问题，不要臆测。

## 资源与范围约定
1. 用户可以在问题中显式指定若干资源范围（文件或目录）。
2. 若用户未指定范围，默认搜索范围为：ctx://resources
3. 用户在问题里写 `['ctx://resources/...', 'ctx://resources/...']`，表示该 URI 是你应优先检索的目标资源。
4. 所有目录和子目录的同级一定存在 `.overview.md` 文件；对目录调用 `overview(uri)` 可获取该目录的相对概括信息。示例：
   overview('ctx://resources/directory') 返回 ctx://resources/directory/.overview.md 文件的内容

## 可用工具
- search: 语义搜索。优先用它获取与问题相关的候选信息。可指定搜索范围。
- read: 读取资源文件的原文内容。
- overview: 获取资源概览；仅支持对目录可获取该目录级别的概括信息。
- tree: 获取目录一层树结构（用于逐层定位子目录/文件）。

## 必须遵循的流程
1. 先执行一次 `search`：
   - 若用户指定了范围，则把这些 URI 作为 `target_uri`（初始候选列表）。
   - 若未指定，则在 `target_uri=ctx://resources` 下搜索。
2. 判断 search 结果是否足以回答（必须满足以下依据）：
   - 覆盖性：search 结果已覆盖问题中的核心实体与关键字段（如“谁/什么/多少/何时/是否”）。
   - 证据性：至少有 1 条高相关结果直接包含可引用事实，而非仅目录名或模糊摘要。
   - 一致性：若存在多条候选结果，结论不冲突；若冲突则视为“不足以回答”。
   - 可溯源性：拟输出结论可以明确映射到具体资源 URI（可形成 `target_uri` 列表）。
   - 完整性：对问题要求的答案粒度已足够（例如用户要“列出清单”，结果中确实能完整列出）。
   - 若以上条件全部满足：直接给出答案，并输出答案依据对应的 `target_uri` 列表。
   - 若任一条件不满足：进入“缩小范围-再搜索”的循环流程。
3. 循环流程（必须执行）：
   - 对当前候选目录调用 `overview` 与 `tree`，确定更相关的子目录/子文件范围。
   - 对缩小后的范围再次调用 `search`，并重复第 2 步判定。
   - 持续循环，直到出现以下任一终止条件：
     a) 已满足“足以回答”的全部条件；
     b) 新范围下 `search` 已无有效结果；
     c) 当前范围已全是文件（无可继续下钻子目录），此时仅可对候选文件调用 `read` 补充证据后给出最终判断。
4. 任何结论都要能映射到明确资源；最终必须记录答案依据的 `target_uri` 列表（可包含多个文件/目录 URI，去重）。
5. 若最终仍无法回答：
   - `target_uri` 列表必须是空数组 `[]`
   - 回答固定为：`无法回答`

## 输出要求
最终回复使用以下结构：
1) `answer`: 你的最终答案；若无法回答则为 `无法回答`
2) `target_uri`: 与最终答案直接相关的 URI 列表；无法回答时必须为 `[]`

除非问题明确要求，不要输出与结论无关的冗余过程细节。
"""

async def main() -> None:
    """The main entry point for the plan example."""
    prompt = "['ctx://resources/专利/pdf/1-CN2025112112148', 'ctx://resources/专利/pdf/2-CN2025111533262'] 两篇专利创新的区别和联系"
    recipe, agent = await create_recipe_and_agent()
    try:
        async for event in iter_agent_events(agent=agent, prompt=prompt):
            event_type = event["type"]
            if event_type in ("text", "thinking"):
                print(event.get("text", ""))
            elif event_type == "tool_result":
                print(event.get("output", ""))
            elif event_type == "tool_use":
                print(
                    json.dumps(
                        {
                            "name": event.get("name"),
                            "input": event.get("input"),
                        },
                        ensure_ascii=False,
                    ),
                )
    finally:
        await recipe.close()


async def create_recipe_and_agent(
    server_config_path: str = DEFAULT_SERVER_CONFIG_PATH,
    cli_config_path: str = DEFAULT_CLI_CONFIG_PATH,
    data_path: str = DEFAULT_DATA_PATH,
) -> tuple[Recipe, ReActAgent]:
    """Create and initialize Recipe + ReActAgent for reuse."""
    import os

    os.environ["CTX_CONFIG_FILE"] = server_config_path
    os.environ["CTX_CLI_CONFIG_FILE"] = cli_config_path

    recipe = Recipe(
        config_path=server_config_path,
        data_path=data_path,
    )
    await recipe.client.initialize()

    toolkit = Toolkit()
    toolkit.register_tool_function(recipe.search)
    toolkit.register_tool_function(recipe.read)
    toolkit.register_tool_function(recipe.overview)
    toolkit.register_tool_function(recipe.tree)

    agent = ReActAgent(
        name="Friday",
        sys_prompt=sys_prompt,  # noqa
        model=OpenAIChatModel(
            model_name="qwen3.5-35b-a3b",
            api_key="sk-xxx",
            client_kwargs={
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            },
            stream=True,
        ),
        formatter=OpenAIChatFormatter(),
        toolkit=toolkit,
        parallel_tool_calls=True,
        enable_meta_tool=True,
        plan_notebook=PlanNotebook(),
        max_iters=20,
    )
    agent.set_console_output_enabled(False)
    return recipe, agent


def _normalize_msg_content(msg: Msg) -> list[dict[str, Any]]:
    """Normalize AgentScope Msg blocks for downstream streaming."""
    normalized: list[dict[str, Any]] = []
    for block in msg.get_content_blocks():
        block_type = block.get("type")
        if block_type == "text":
            normalized.append({"type": "text", "text": block.get("text", "")})
        elif block_type == "thinking":
            normalized.append({"type": "thinking", "text": block.get("thinking", "")})
        elif block_type == "tool_use":
            normalized.append(
                {
                    "type": "tool_use",
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": block.get("input", {}),
                },
            )
        elif block_type == "tool_result":
            normalized.append(
                {
                    "type": "tool_result",
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "output": block.get("output"),
                },
            )
    return normalized


async def iter_agent_messages(
    agent: ReActAgent,
    prompt: str,
) -> AsyncGenerator[tuple[Msg, bool], None]:
    """Yield raw AgentScope messages with chunk-finish flag."""
    from agentscope.pipeline import stream_printing_messages

    user_msg = Msg("user", prompt, "user")
    async for item_msg, last in stream_printing_messages(
        agents=[agent],
        coroutine_task=agent(user_msg),
    ):
        yield item_msg, last


async def iter_agent_events(
    agent: ReActAgent,
    prompt: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield normalized events for UI/transport layers."""
    async for raw_msg, last in iter_agent_messages(agent=agent, prompt=prompt):
        for event in _normalize_msg_content(raw_msg):
            yield {
                "message_id": raw_msg.id,
                "invocation_id": raw_msg.invocation_id,
                "is_last": last,
                **event,
            }


if __name__ == "__main__":
    asyncio.run(main())