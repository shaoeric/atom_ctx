# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Pack Service for AtomCtx.

Provides ctxpack export/import operations.
"""

from typing import Optional

from atom_ctx.server.identity import RequestContext
from atom_ctx.storage.local_fs import export_ctxpack as local_export_ctxpack
from atom_ctx.storage.local_fs import import_ctxpack as local_import_ctxpack
from atom_ctx.storage.ctx_fs import VikingFS
from atom_ctx_cli.exceptions import NotInitializedError
from atom_ctx_cli.utils import get_logger

logger = get_logger(__name__)


class PackService:
    """OVPack export/import service."""

    def __init__(self, ctx_fs: Optional[VikingFS] = None):
        self._ctx_fs = ctx_fs

    def set_ctx_fs(self, ctx_fs: VikingFS) -> None:
        """Set VikingFS instance (for deferred initialization)."""
        self._ctx_fs = ctx_fs

    def _ensure_initialized(self) -> VikingFS:
        """Ensure VikingFS is initialized."""
        if not self._ctx_fs:
            raise NotInitializedError("VikingFS")
        return self._ctx_fs

    async def export_ctxpack(self, uri: str, to: str, ctx: RequestContext) -> str:
        """Export specified context path as .ctxpack file.

        Args:
            uri: Ctx URI
            to: Target file path

        Returns:
            Exported file path
        """
        ctx_fs = self._ensure_initialized()
        return await local_export_ctxpack(ctx_fs, uri, to, ctx=ctx)

    async def import_ctxpack(
        self,
        file_path: str,
        parent: str,
        ctx: RequestContext,
        force: bool = False,
        vectorize: bool = True,
    ) -> str:
        """Import local .ctxpack file to specified parent path.

        Args:
            file_path: Local .ctxpack file path
            parent: Target parent URI (e.g., ctx://user/alice/resources/references/)
            force: Whether to force overwrite existing resources
            vectorize: Whether to trigger vectorization

        Returns:
            Imported root resource URI
        """
        ctx_fs = self._ensure_initialized()
        return await local_import_ctxpack(
            ctx_fs, file_path, parent, force=force, vectorize=vectorize, ctx=ctx
        )
