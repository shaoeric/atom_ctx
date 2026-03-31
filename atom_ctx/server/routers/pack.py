# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Pack endpoints for AtomCtx HTTP Server."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from atom_ctx.server.auth import get_request_context
from atom_ctx.server.dependencies import get_service
from atom_ctx.server.identity import RequestContext
from atom_ctx.server.local_input_guard import resolve_uploaded_temp_file_id
from atom_ctx.server.models import Response
from atom_ctx_cli.utils.config.ctx_config import get_atom_ctx_config

router = APIRouter(prefix="/api/v1/pack", tags=["pack"])


class ExportRequest(BaseModel):
    """Request model for export."""

    uri: str
    to: str


class ImportRequest(BaseModel):
    """Request model for import.

    Attributes:
        temp_file_id: Temporary upload id returned by /api/v1/resources/temp_upload.
        parent: Parent URI under which the imported pack will be placed.
        force: Whether to overwrite existing content if needed.
        vectorize: Whether to build vectors for imported content.
    """

    model_config = ConfigDict(extra="forbid")

    temp_file_id: str
    parent: str
    force: bool = False
    vectorize: bool = True


@router.post("/export")
async def export_ctxpack(
    request: ExportRequest,
    _ctx: RequestContext = Depends(get_request_context),
):
    """Export context as .ctxpack file."""
    service = get_service()
    result = await service.pack.export_ctxpack(request.uri, request.to, ctx=_ctx)
    return Response(status="ok", result={"file": result})


@router.post("/import")
async def import_ctxpack(
    request: ImportRequest,
    _ctx: RequestContext = Depends(get_request_context),
):
    """Import .ctxpack file."""
    service = get_service()

    upload_temp_dir = get_atom_ctx_config().storage.get_upload_temp_dir()
    file_path = resolve_uploaded_temp_file_id(request.temp_file_id, upload_temp_dir)

    result = await service.pack.import_ctxpack(
        file_path,
        request.parent,
        ctx=_ctx,
        force=request.force,
        vectorize=request.vectorize,
    )
    return Response(status="ok", result={"uri": result})
