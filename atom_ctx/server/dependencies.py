# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Dependency injection for AtomCtx HTTP Server."""

from typing import Optional

from atom_ctx.service.core import AtomCtxService

_service: Optional[AtomCtxService] = None


def get_service() -> AtomCtxService:
    """Get the AtomCtxService instance.

    Returns:
        AtomCtxService instance

    Raises:
        RuntimeError: If service is not initialized
    """
    if _service is None:
        raise RuntimeError("AtomCtxService not initialized")
    return _service


def set_service(service: AtomCtxService) -> None:
    """Set the AtomCtxService instance.

    Args:
        service: AtomCtxService instance to set
    """
    global _service
    _service = service
