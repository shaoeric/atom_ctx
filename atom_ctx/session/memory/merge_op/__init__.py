# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Merge operation implementations.
"""

from atom_ctx.session.memory.merge_op.base import (
    MergeOp,
    MergeOpBase,
    FieldType,
    SearchReplaceBlock,
    StrPatch,
)
from atom_ctx.session.memory.merge_op.patch import PatchOp
from atom_ctx.session.memory.merge_op.sum import SumOp
from atom_ctx.session.memory.merge_op.immutable import ImmutableOp
from atom_ctx.session.memory.merge_op.factory import MergeOpFactory
from atom_ctx.session.memory.merge_op.patch_handler import (
    MemoryPatchHandler,
    PatchParseError,
    apply_str_patch,
)

__all__ = [
    "MergeOp",
    "MergeOpBase",
    "FieldType",
    "SearchReplaceBlock",
    "StrPatch",
    "PatchOp",
    "SumOp",
    "ImmutableOp",
    "MergeOpFactory",
    "MemoryPatchHandler",
    "PatchParseError",
    "apply_str_patch",
]
