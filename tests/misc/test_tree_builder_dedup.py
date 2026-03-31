#!/usr/bin/env python3
# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Tests for TreeBuilder._resolve_unique_uri — duplicate filename auto-rename."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _make_ctx_fs_mock(existing_uris: set[str]):
    """Create a mock VikingFS whose stat() raises for non-existing URIs."""
    fs = MagicMock()

    async def _stat(uri, **kwargs):
        if uri in existing_uris:
            return {"name": uri.split("/")[-1], "isDir": True}
        raise FileNotFoundError(f"Not found: {uri}")

    fs.stat = AsyncMock(side_effect=_stat)
    return fs


class TestResolveUniqueUri:
    @pytest.mark.asyncio
    async def test_no_conflict(self):
        """When the URI is free, return it unchanged."""
        from atom_ctx.parse.tree_builder import TreeBuilder

        fs = _make_ctx_fs_mock(set())
        builder = TreeBuilder()

        with patch("atom_ctx.parse.tree_builder.get_ctx_fs", return_value=fs):
            result = await builder._resolve_unique_uri("ctx://resources/report")

        assert result == "ctx://resources/report"

    @pytest.mark.asyncio
    async def test_single_conflict(self):
        """When base name exists, should return name_1."""
        from atom_ctx.parse.tree_builder import TreeBuilder

        existing = {"ctx://resources/report"}
        fs = _make_ctx_fs_mock(existing)
        builder = TreeBuilder()

        with patch("atom_ctx.parse.tree_builder.get_ctx_fs", return_value=fs):
            result = await builder._resolve_unique_uri("ctx://resources/report")

        assert result == "ctx://resources/report_1"

    @pytest.mark.asyncio
    async def test_multiple_conflicts(self):
        """When _1 and _2 also exist, should return _3."""
        from atom_ctx.parse.tree_builder import TreeBuilder

        existing = {
            "ctx://resources/report",
            "ctx://resources/report_1",
            "ctx://resources/report_2",
        }
        fs = _make_ctx_fs_mock(existing)
        builder = TreeBuilder()

        with patch("atom_ctx.parse.tree_builder.get_ctx_fs", return_value=fs):
            result = await builder._resolve_unique_uri("ctx://resources/report")

        assert result == "ctx://resources/report_3"

    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self):
        """When all candidate names are taken, raise FileExistsError."""
        from atom_ctx.parse.tree_builder import TreeBuilder

        existing = {"ctx://resources/report"} | {
            f"ctx://resources/report_{i}" for i in range(1, 6)
        }
        fs = _make_ctx_fs_mock(existing)
        builder = TreeBuilder()

        with patch("atom_ctx.parse.tree_builder.get_ctx_fs", return_value=fs):
            with pytest.raises(FileExistsError, match="Cannot resolve unique name"):
                await builder._resolve_unique_uri("ctx://resources/report", max_attempts=5)

    @pytest.mark.asyncio
    async def test_gap_in_sequence(self):
        """If _1 exists but _2 does not, should return _2 (not skip to _3)."""
        from atom_ctx.parse.tree_builder import TreeBuilder

        existing = {
            "ctx://resources/report",
            "ctx://resources/report_1",
        }
        fs = _make_ctx_fs_mock(existing)
        builder = TreeBuilder()

        with patch("atom_ctx.parse.tree_builder.get_ctx_fs", return_value=fs):
            result = await builder._resolve_unique_uri("ctx://resources/report")

        assert result == "ctx://resources/report_2"
