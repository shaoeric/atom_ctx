# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Search Service for AtomCtx.

Provides semantic search operations: search, find.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from atom_ctx.server.identity import RequestContext
from atom_ctx.storage.ctx_fs import VikingFS
from atom_ctx_cli.exceptions import NotInitializedError
from atom_ctx_cli.utils import get_logger

if TYPE_CHECKING:
    from atom_ctx.session import Session

logger = get_logger(__name__)


class SearchService:
    """Semantic search service."""

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

    async def search(
        self,
        query: str,
        ctx: RequestContext,
        target_uri: str = "",
        session: Optional["Session"] = None,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter: Optional[Dict] = None,
    ) -> Any:
        """Complex search with session context.

        Args:
            query: Query string
            target_uri: Target directory URI
            session: Session object for context
            limit: Max results
            score_threshold: Score threshold
            filter: Metadata filters

        Returns:
            FindResult
        """
        ctx_fs = self._ensure_initialized()

        session_info = None
        if session:
            session_info = await session.get_context_for_search(query)

        result = await ctx_fs.search(
            query=query,
            ctx=ctx,
            target_uri=target_uri,
            session_info=session_info,
            limit=limit,
            score_threshold=score_threshold,
            filter=filter,
        )
        return result

    async def find(
        self,
        query: str,
        ctx: RequestContext,
        target_uri: str = "",
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter: Optional[Dict] = None,
    ) -> Any:
        """Semantic search without session context.

        Args:
            query: Query string
            target_uri: Target directory URI
            limit: Max results
            score_threshold: Score threshold
            filter: Metadata filters

        Returns:
            FindResult
        """
        ctx_fs = self._ensure_initialized()
        result = await ctx_fs.find(
            query=query,
            ctx=ctx,
            target_uri=target_uri,
            limit=limit,
            score_threshold=score_threshold,
            filter=filter,
        )
        return result
