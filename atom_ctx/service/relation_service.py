# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Relation Service for AtomCtx.

Provides relation management operations: relations, link, unlink.
"""

from typing import Any, Dict, List, Optional, Union

from atom_ctx.server.identity import RequestContext
from atom_ctx.storage.ctx_fs import VikingFS
from atom_ctx_cli.exceptions import NotInitializedError
from atom_ctx_cli.utils import get_logger

logger = get_logger(__name__)


class RelationService:
    """Relation management service."""

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

    async def relations(self, uri: str, ctx: RequestContext) -> List[Dict[str, Any]]:
        """Get relations (returns [{"uri": "...", "reason": "..."}, ...])."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.relations(uri, ctx=ctx)

    async def link(
        self,
        from_uri: str,
        uris: Union[str, List[str]],
        ctx: RequestContext,
        reason: str = "",
    ) -> None:
        """Create link (single or multiple).

        Args:
            from_uri: Source URI
            uris: Target URI or list of URIs
            reason: Reason for linking
        """
        ctx_fs = self._ensure_initialized()
        await ctx_fs.link(from_uri, uris, reason, ctx=ctx)

    async def unlink(self, from_uri: str, uri: str, ctx: RequestContext) -> None:
        """Remove link (remove specified URI from uris).

        Args:
            from_uri: Source URI
            uri: Target URI to remove
        """
        ctx_fs = self._ensure_initialized()
        await ctx_fs.unlink(from_uri, uri, ctx=ctx)
