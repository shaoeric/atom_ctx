# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Session management module."""

from typing import Optional

from atom_ctx.session.compressor import ExtractionStats, SessionCompressor
from atom_ctx.session.memory_archiver import (
    ArchivalCandidate,
    ArchivalResult,
    MemoryArchiver,
)
from atom_ctx.session.memory_deduplicator import (
    DedupDecision,
    DedupResult,
    ExistingMemoryAction,
    MemoryActionDecision,
    MemoryDeduplicator,
)
from atom_ctx.session.memory_extractor import (
    CandidateMemory,
    MemoryCategory,
    MemoryExtractor,
    ToolSkillCandidateMemory,
)
from atom_ctx.session.session import Session, SessionCompression, SessionMeta, SessionStats
from atom_ctx.storage import VikingDBManager
from atom_ctx_cli.utils import get_logger
from atom_ctx_cli.utils.config import get_atom_ctx_config

logger = get_logger(__name__)


def create_session_compressor(
    vikingdb: VikingDBManager,
    memory_version: Optional[str] = None,
) -> SessionCompressor:
    """
    Create a SessionCompressor instance based on configuration.

    Args:
        vikingdb: VikingDBManager instance
        memory_version: Optional memory version override ("v1" or "v2").
            If not provided, uses the version from config.

    Returns:
        SessionCompressor instance (v1 or v2 implementation)
    """
    # Determine which version to use
    if memory_version is None:
        try:
            config = get_atom_ctx_config()
            memory_version = config.memory.version
        except Exception as e:
            logger.warning(f"Failed to get memory version from config, defaulting to v1: {e}")
            memory_version = "v1"

    if memory_version == "v2":
        logger.info("Using v2 memory compressor (templating system)")
        try:
            from atom_ctx.session.compressor_v2 import SessionCompressorV2

            return SessionCompressorV2(vikingdb=vikingdb)
        except Exception as e:
            logger.warning(f"Failed to load v2 compressor, falling back to v1: {e}")
            return SessionCompressor(vikingdb=vikingdb)

    # Default to v1
    logger.info("Using v1 memory compressor (legacy)")
    return SessionCompressor(vikingdb=vikingdb)


__all__ = [
    # Session
    "Session",
    "SessionCompression",
    "SessionMeta",
    "SessionStats",
    # Compressor
    "SessionCompressor",
    "ExtractionStats",
    "create_session_compressor",
    # Memory Archiver
    "MemoryArchiver",
    "ArchivalCandidate",
    "ArchivalResult",
    # Memory Extractor
    "MemoryExtractor",
    "MemoryCategory",
    "CandidateMemory",
    "ToolSkillCandidateMemory",
    # Memory Deduplicator
    "MemoryDeduplicator",
    "DedupDecision",
    "MemoryActionDecision",
    "ExistingMemoryAction",
    "DedupResult",
]
