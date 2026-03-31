# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Tests for CtxURI short-format URI normalization.

Verifies that CtxURI accepts short-format paths (e.g., '/resources',
'user/memories') in addition to full-format URIs ('ctx://resources').

Ref: https://github.com/volcengine/atom-ctx/issues/259
"""

import pytest

from atom_ctx_cli.utils.uri import CtxURI


class TestCtxURIShortFormat:
    """CtxURI should accept and auto-normalize short-format URIs."""

    def test_slash_prefix_path(self):
        """'/resources' should be normalized to 'ctx://resources'."""
        uri = CtxURI("/resources")
        assert uri.uri == "ctx://resources"
        assert uri.scope == "resources"

    def test_bare_path(self):
        """'resources' should be normalized to 'ctx://resources'."""
        uri = CtxURI("resources")
        assert uri.uri == "ctx://resources"
        assert uri.scope == "resources"

    def test_slash_prefix_nested(self):
        """'/user/memories/preferences' should normalize correctly."""
        uri = CtxURI("/user/memories/preferences")
        assert uri.uri == "ctx://user/memories/preferences"
        assert uri.scope == "user"

    def test_bare_nested_path(self):
        """'agent/skills/pdf' should normalize correctly."""
        uri = CtxURI("agent/skills/pdf")
        assert uri.uri == "ctx://agent/skills/pdf"
        assert uri.scope == "agent"

    def test_full_format_unchanged(self):
        """Full-format URIs should pass through unchanged."""
        uri = CtxURI("ctx://resources/my_project")
        assert uri.uri == "ctx://resources/my_project"

    def test_root_slash(self):
        """'/' should normalize to 'ctx://'."""
        uri = CtxURI("/")
        assert uri.uri == "ctx://"
        assert uri.scope == ""

    def test_full_root(self):
        """'ctx://' should work as before."""
        uri = CtxURI("ctx://")
        assert uri.uri == "ctx://"
        assert uri.scope == ""

    def test_join_after_short_format(self):
        """join() should work on auto-normalized URIs."""
        uri = CtxURI("/resources")
        joined = uri.join("my_project")
        assert joined.uri == "ctx://resources/my_project"

    def test_parent_after_short_format(self):
        """parent should work on auto-normalized URIs."""
        uri = CtxURI("/user/memories/preferences")
        parent = uri.parent
        assert parent is not None
        assert parent.uri == "ctx://user/memories"

    def test_is_valid_short_format(self):
        """is_valid should accept short-format URIs after normalization."""
        assert CtxURI.is_valid("/resources")
        assert CtxURI.is_valid("user/memories")

    def test_invalid_scope_still_rejected(self):
        """Invalid scopes should still raise ValueError."""
        with pytest.raises(ValueError, match="Invalid scope"):
            CtxURI("/invalid_scope/foo")

    def test_normalize_idempotent(self):
        """Normalizing an already-normalized URI should be idempotent."""
        original = "ctx://resources/docs"
        assert CtxURI.normalize(original) == original
        assert (
            CtxURI.normalize(CtxURI.normalize("/resources/docs")) == "ctx://resources/docs"
        )

    @pytest.mark.parametrize(
        "short,expected",
        [
            ("/resources", "ctx://resources"),
            ("/user", "ctx://user"),
            ("/agent/skills", "ctx://agent/skills"),
            ("/session/abc123", "ctx://session/abc123"),
            ("/queue", "ctx://queue"),
            ("/temp", "ctx://temp"),
            ("resources/images", "ctx://resources/images"),
        ],
    )
    def test_all_scopes(self, short, expected):
        """All valid scopes should work with short format."""
        uri = CtxURI(short)
        assert uri.uri == expected
