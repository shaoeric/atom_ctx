# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Session Compressor V2 for AtomCtx.

Uses the new Memory Templating System with ReAct orchestrator.
Maintains the same interface as compressor.py for backward compatibility.
"""

import os
from typing import List, Optional

from atom_ctx.core.context import Context
from atom_ctx.message import Message
from atom_ctx.server.identity import RequestContext
from atom_ctx.session.memory import ExtractLoop, MemoryUpdater
from atom_ctx.storage import VikingDBManager
from atom_ctx.storage.ctx_fs import get_ctx_fs
from atom_ctx.telemetry import get_current_telemetry
from atom_ctx_cli.session.user_id import UserIdentifier
from atom_ctx_cli.utils import get_logger
from atom_ctx_cli.utils.config import get_atom_ctx_config

logger = get_logger(__name__)


class SessionCompressorV2:
    """Session memory extractor with v2 templating system."""

    def __init__(
        self,
        vikingdb: VikingDBManager,
    ):
        """Initialize session compressor."""
        self.vikingdb = vikingdb
        # registry 现在由 provider 负责加载，这里不再初始化
        # MemoryUpdater 会在 apply_operations 时从 provider 获取 registry
        pass

    def _get_or_create_react(
        self,
        ctx: Optional[RequestContext] = None,
        messages: Optional[List] = None,
        latest_archive_overview: str = "",
    ) -> ExtractLoop:
        """Create new ExtractLoop instance with current ctx.

        Note: Always create new instance to avoid cross-session isolation issues.
        The ctx contains request-scoped state that must not be shared across requests.
        """
        config = get_atom_ctx_config()
        vlm = config.vlm.get_vlm_instance()
        ctx_fs = get_ctx_fs()

        # Create context provider with messages (provider 负责加载 schema)
        from atom_ctx.session.memory.session_extract_context_provider import SessionExtractContextProvider
        context_provider = SessionExtractContextProvider(
            messages=messages,
            latest_archive_overview=latest_archive_overview,
        )

        return ExtractLoop(
            vlm=vlm,
            ctx_fs=ctx_fs,
            ctx=ctx,
            context_provider=context_provider,
        )

    def _get_or_create_updater(self, registry, transaction_handle=None) -> MemoryUpdater:
        """Create new MemoryUpdater instance for each request.

        Always create new instance to avoid cross-request state pollution.
        """
        return MemoryUpdater(
            registry=registry,
            vikingdb=self.vikingdb,
            transaction_handle=transaction_handle
        )

    async def extract_long_term_memories(
        self,
        messages: List[Message],
        user: Optional["UserIdentifier"] = None,
        session_id: Optional[str] = None,
        ctx: Optional[RequestContext] = None,
        strict_extract_errors: bool = False,
        latest_archive_overview: str = "",
    ) -> List[Context]:
        """Extract long-term memories from messages using v2 templating system.

        Note: Returns empty List[Context] because v2 directly writes to storage.
        The list length is used for stats in session.py.
        """
        if not messages:
            return []

        if not ctx:
            logger.warning("No RequestContext provided, skipping memory extraction")
            return []

        logger.info("Starting v2 memory extraction from conversation")

        # Initialize telemetry to 0 (matching v1 pattern)
        telemetry = get_current_telemetry()
        telemetry.set("memory.extract.candidates.total", 0)
        telemetry.set("memory.extract.candidates.standard", 0)
        telemetry.set("memory.extract.candidates.tool_skill", 0)
        telemetry.set("memory.extract.created", 0)
        telemetry.set("memory.extract.merged", 0)
        telemetry.set("memory.extract.deleted", 0)
        telemetry.set("memory.extract.skipped", 0)

        from atom_ctx.storage.transaction import get_lock_manager, init_lock_manager
        from atom_ctx.storage.ctx_fs import get_ctx_fs

        # 初始化锁管理器（仅在有 AGFS 时使用锁机制）
        ctx_fs = get_ctx_fs()
        lock_manager = None
        transaction_handle = None
        if ctx_fs and hasattr(ctx_fs, 'agfs') and ctx_fs.agfs:
            init_lock_manager(ctx_fs.agfs)
            lock_manager = get_lock_manager()
            transaction_handle = lock_manager.create_handle()
        else:
            logger.warning("VikingFS or AGFS not available, running without lock mechanism")


        try:
            # 获取所有记忆 schema 目录并加锁（仅在有锁管理器时）
            orchestrator = self._get_or_create_react(
                ctx=ctx,
                messages=messages,
                latest_archive_overview=latest_archive_overview,
            )
            if lock_manager:
                # 基于 provider 的 schemas 生成目录列表
                schemas = orchestrator.context_provider.get_memory_schemas(ctx)
                memory_schema_dirs = []
                for schema in schemas:
                    if not schema.directory:
                        continue
                    user_space = ctx.user.user_space_name() if ctx and ctx.user else "default"
                    agent_space = ctx.user.agent_space_name() if ctx and ctx.user else "default"
                    dir_path = schema.directory.replace("{user_space}", user_space).replace("{agent_space}", agent_space)
                    dir_path = ctx_fs._uri_to_path(dir_path, ctx)
                    if dir_path not in memory_schema_dirs:
                        memory_schema_dirs.append(dir_path)
                logger.debug(f"Memory schema directories to lock: {memory_schema_dirs}")

                # 循环等待获取锁（机制确保不会死锁）
                # 由于使用有序加锁法，可以安全地无限等待
                while True:
                    lock_acquired = await lock_manager.acquire_subtree_batch(
                        transaction_handle,
                        memory_schema_dirs,
                        timeout=None,
                    )
                    if lock_acquired:
                        break
                    logger.warning("Failed to acquire memory locks, retrying...")

            orchestrator._transaction_handle = transaction_handle  # 传递给 ExtractLoop

            # Run ReAct orchestrator
            operations, tools_used = await orchestrator.run()

            if operations is None:
                logger.info("No memory operations generated")
                return []

            # Convert to legacy format for logging and apply_operations
            if hasattr(operations, 'to_legacy_operations'):
                legacy = operations.to_legacy_operations()
                write_uris = legacy.get('write_uris', [])
                edit_uris = legacy.get('edit_uris', [])
            else:
                # Fallback for old format
                write_uris = operations.write_uris
                edit_uris = operations.edit_uris

            # 从 orchestrator 获取 registry（从 provider 获取）
            registry = orchestrator.context_provider._get_registry()
            updater = self._get_or_create_updater(registry, transaction_handle)

            logger.info(
                f"Generated memory operations: write={len(write_uris)}, "
                f"edit={len(edit_uris)}, edit_overview={len(operations.edit_overview_uris)}, "
                f"delete={len(operations.delete_uris)}"
            )

            # Create extract context from messages
            from atom_ctx.session.memory.memory_updater import ExtractContext
            extract_context = ExtractContext(messages)

            # Apply operations
            result = await updater.apply_operations(operations, ctx, registry=registry, extract_context=extract_context)

            logger.info(
                f"Applied memory operations: written={len(result.written_uris)}, "
                f"edited={len(result.edited_uris)}, deleted={len(result.deleted_uris)}, "
                f"errors={len(result.errors)}"
            )

            # Report telemetry stats (matching v1 pattern)
            telemetry = get_current_telemetry()
            telemetry.set("memory.extract.candidates.total", len(result.written_uris) + len(result.edited_uris))
            telemetry.set("memory.extract.created", len(result.written_uris))
            telemetry.set("memory.extract.merged", len(result.edited_uris))
            telemetry.set("memory.extract.deleted", len(result.deleted_uris))
            telemetry.set("memory.extract.skipped", len(result.errors))

            # Build Context objects for stats in session.py
            contexts: List[Context] = []

            # Written memories
            for uri in result.written_uris:
                contexts.append(Context(
                    uri=uri,
                    category="memory_write",
                    context_type="memory",
                ))

            # Edited memories
            for uri in result.edited_uris:
                contexts.append(Context(
                    uri=uri,
                    category="memory_edit",
                    context_type="memory",
                ))

            # Deleted memories
            for uri in result.deleted_uris:
                contexts.append(Context(
                    uri=uri,
                    category="memory_delete",
                    context_type="memory",
                ))

            return contexts

        except Exception as e:
            logger.error(f"Failed to extract memories with v2: {e}", exc_info=True)
            if strict_extract_errors:
                raise
            return []
        finally:
            # 确保释放所有锁（仅在有锁管理器时）
            if lock_manager and transaction_handle:
                try:
                    await lock_manager.release(transaction_handle)
                except Exception as e:
                    logger.warning(f"Failed to release transaction lock: {e}")
