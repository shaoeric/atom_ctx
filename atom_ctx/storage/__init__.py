# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Storage layer interfaces and implementations."""

from atom_ctx.storage.errors import (
    CollectionNotFoundError,
    ConnectionError,
    DuplicateKeyError,
    RecordNotFoundError,
    SchemaError,
    StorageException,
)
from atom_ctx.storage.observers import BaseObserver, QueueObserver
from atom_ctx.storage.queuefs import QueueManager, get_queue_manager, init_queue_manager
from atom_ctx.storage.ctx_fs import VikingFS, get_ctx_fs, init_ctx_fs
from atom_ctx.storage.viking_vector_index_backend import VikingVectorIndexBackend
from atom_ctx.storage.vikingdb_manager import VikingDBManager, VikingDBManagerProxy

__all__ = [
    # Exceptions
    "StorageException",
    "CollectionNotFoundError",
    "RecordNotFoundError",
    "DuplicateKeyError",
    "ConnectionError",
    "SchemaError",
    # Backend
    "VikingVectorIndexBackend",
    "VikingDBManager",
    "VikingDBManagerProxy",
    # QueueFS
    "QueueManager",
    "init_queue_manager",
    "get_queue_manager",
    # VikingFS
    "VikingFS",
    "init_ctx_fs",
    "get_ctx_fs",
    # Observers
    "BaseObserver",
    "QueueObserver",
]
