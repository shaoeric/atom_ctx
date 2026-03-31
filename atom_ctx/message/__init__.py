# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Message module - based on opencode Part design.

Message = role + parts
"""

from atom_ctx.message.message import Message
from atom_ctx.message.part import ContextPart, Part, TextPart, ToolPart

__all__ = [
    "Message",
    "Part",
    "TextPart",
    "ContextPart",
    "ToolPart",
]
