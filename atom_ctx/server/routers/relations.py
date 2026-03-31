# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Relations endpoints for AtomCtx HTTP Server."""

from typing import List, Union

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from atom_ctx.server.auth import get_request_context
from atom_ctx.server.dependencies import get_service
from atom_ctx.server.identity import RequestContext
from atom_ctx.server.models import Response

router = APIRouter(prefix="/api/v1/relations", tags=["relations"])


class LinkRequest(BaseModel):
    """Request model for link."""

    from_uri: str
    to_uris: Union[str, List[str]]
    reason: str = ""


class UnlinkRequest(BaseModel):
    """Request model for unlink."""

    from_uri: str
    to_uri: str


@router.get("")
async def relations(
    uri: str = Query(..., description="Ctx URI"),
    _ctx: RequestContext = Depends(get_request_context),
):
    """Get relations for a resource."""
    service = get_service()
    result = await service.relations.relations(uri, ctx=_ctx)
    return Response(status="ok", result=result)


@router.post("/link")
async def link(
    request: LinkRequest,
    _ctx: RequestContext = Depends(get_request_context),
):
    """Create link between resources."""
    service = get_service()
    await service.relations.link(request.from_uri, request.to_uris, ctx=_ctx, reason=request.reason)
    return Response(status="ok", result={"from": request.from_uri, "to": request.to_uris})


@router.delete("/link")
async def unlink(
    request: UnlinkRequest,
    _ctx: RequestContext = Depends(get_request_context),
):
    """Remove link between resources."""
    service = get_service()
    await service.relations.unlink(request.from_uri, request.to_uri, ctx=_ctx)
    return Response(status="ok", result={"from": request.from_uri, "to": request.to_uri})
