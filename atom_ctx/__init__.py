# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
AtomCtx - An Agent-native context database

Data in, Context out.
"""

try:
    from ._version import version as __version__
except ImportError:
    try:
        from importlib.metadata import version

        __version__ = version("atom_ctx")
    except ImportError:
        __version__ = "0.0.0+unknown"

try:
    from atom_ctx.pyagfs import AGFSClient
except ImportError as exc:
    raise ImportError(
        "Bundled AtomCtx AGFS client is unavailable. "
        "Reinstall atom_ctx or run 'pip install -e .' from the project root."
    ) from exc


def __getattr__(name: str):
    if name == "AsyncAtomCtx":
        from atom_ctx.async_client import AsyncAtomCtx

        return AsyncAtomCtx
    if name == "SyncAtomCtx":
        from atom_ctx.sync_client import SyncAtomCtx

        return SyncAtomCtx
    if name == "AtomCtx":
        from atom_ctx.sync_client import SyncAtomCtx

        return SyncAtomCtx
    if name == "Session":
        from atom_ctx.session import Session

        return Session
    if name == "AsyncHTTPClient":
        from atom_ctx_cli.client.http import AsyncHTTPClient

        return AsyncHTTPClient
    if name == "SyncHTTPClient":
        from atom_ctx_cli.client.sync_http import SyncHTTPClient

        return SyncHTTPClient
    if name == "UserIdentifier":
        from atom_ctx_cli.session.user_id import UserIdentifier

        return UserIdentifier
    raise AttributeError(name)


__all__ = [
    "AtomCtx",
    "SyncAtomCtx",
    "AsyncAtomCtx",
    "SyncHTTPClient",
    "AsyncHTTPClient",
    "Session",
    "UserIdentifier",
]
