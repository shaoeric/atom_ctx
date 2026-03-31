# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
File System Service for AtomCtx.

Provides file system operations: ls, mkdir, rm, mv, tree, stat, read, abstract, overview, grep, glob.
"""

from typing import Any, Dict, List, Optional

from atom_ctx.server.identity import RequestContext
from atom_ctx.storage.ctx_fs import VikingFS
from atom_ctx_cli.exceptions import NotInitializedError
from atom_ctx_cli.utils import get_logger

logger = get_logger(__name__)


class FSService:
    """File system operations service."""

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

    async def ls(
        self,
        uri: str,
        ctx: RequestContext,
        recursive: bool = False,
        simple: bool = False,
        output: str = "original",
        abs_limit: int = 256,
        show_all_hidden: bool = False,
        node_limit: int = 1000,
        level_limit: int = 3,
    ) -> List[Any]:
        """List directory contents.

        Args:
            uri: Ctx URI
            recursive: List all subdirectories recursively
            simple: Return only relative path list
            output: str = "original" or "agent"
            abs_limit: int = 256 if output == "agent" else ignore
            show_all_hidden: bool = False (list all hidden files, like -a)
            node_limit: int = 1000 (maximum number of nodes to list)
        """
        ctx_fs = self._ensure_initialized()

        if simple:
            # Only return URIs — skip expensive abstract fetching to save tokens
            if recursive:
                entries = await ctx_fs.tree(
                    uri,
                    ctx=ctx,
                    output="original",
                    show_all_hidden=show_all_hidden,
                    node_limit=node_limit,
                    level_limit=level_limit,
                )
            else:
                entries = await ctx_fs.ls(
                    uri,
                    ctx=ctx,
                    output="original",
                    show_all_hidden=show_all_hidden,
                    node_limit=node_limit,
                )
            return [e.get("uri", "") for e in entries]

        if recursive:
            entries = await ctx_fs.tree(
                uri,
                ctx=ctx,
                output=output,
                abs_limit=abs_limit,
                show_all_hidden=show_all_hidden,
                node_limit=node_limit,
                level_limit=level_limit,
            )
        else:
            entries = await ctx_fs.ls(
                uri,
                ctx=ctx,
                output=output,
                abs_limit=abs_limit,
                show_all_hidden=show_all_hidden,
                node_limit=node_limit,
            )
        return entries

    async def mkdir(self, uri: str, ctx: RequestContext) -> None:
        """Create directory."""
        ctx_fs = self._ensure_initialized()
        await ctx_fs.mkdir(uri, ctx=ctx)

    async def rm(self, uri: str, ctx: RequestContext, recursive: bool = False) -> None:
        """Remove resource."""
        ctx_fs = self._ensure_initialized()
        await ctx_fs.rm(uri, recursive=recursive, ctx=ctx)

    async def mv(self, from_uri: str, to_uri: str, ctx: RequestContext) -> None:
        """Move resource."""
        ctx_fs = self._ensure_initialized()
        await ctx_fs.mv(from_uri, to_uri, ctx=ctx)

    async def tree(
        self,
        uri: str,
        ctx: RequestContext,
        output: str = "original",
        abs_limit: int = 128,
        show_all_hidden: bool = False,
        node_limit: int = 1000,
        level_limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get directory tree."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.tree(
            uri,
            ctx=ctx,
            output=output,
            abs_limit=abs_limit,
            show_all_hidden=show_all_hidden,
            node_limit=node_limit,
            level_limit=level_limit,
        )

    async def stat(self, uri: str, ctx: RequestContext) -> Dict[str, Any]:
        """Get resource status."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.stat(uri, ctx=ctx)

    async def read(self, uri: str, ctx: RequestContext, offset: int = 0, limit: int = -1) -> str:
        """Read file content."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.read_file(uri, offset=offset, limit=limit, ctx=ctx)

    async def abstract(self, uri: str, ctx: RequestContext) -> str:
        """Read L0 abstract (.abstract.md)."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.abstract(uri, ctx=ctx)

    async def overview(self, uri: str, ctx: RequestContext) -> str:
        """Read L1 overview (.overview.md)."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.overview(uri, ctx=ctx)

    async def grep(
        self,
        uri: str,
        pattern: str,
        ctx: RequestContext,
        case_insensitive: bool = False,
        node_limit: Optional[int] = None,
    ) -> Dict:
        """Content search."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.grep(
            uri, pattern, case_insensitive=case_insensitive, node_limit=node_limit, ctx=ctx
        )

    async def glob(
        self,
        pattern: str,
        ctx: RequestContext,
        uri: str = "ctx://",
        node_limit: Optional[int] = None,
    ) -> Dict:
        """File pattern matching."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.glob(pattern, uri=uri, node_limit=node_limit, ctx=ctx)

    async def read_file_bytes(self, uri: str, ctx: RequestContext) -> bytes:
        """Read file as raw bytes."""
        ctx_fs = self._ensure_initialized()
        return await ctx_fs.read_file_bytes(uri, ctx=ctx)
