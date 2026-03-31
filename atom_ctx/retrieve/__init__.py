# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Retrieval module for AtomCtx.

Provides intent-driven hierarchical context retrieval.
"""

from atom_ctx.retrieve.hierarchical_retriever import HierarchicalRetriever
from atom_ctx.retrieve.intent_analyzer import IntentAnalyzer
from atom_ctx_cli.retrieve.types import (
    ContextType,
    FindResult,
    MatchedContext,
    QueryPlan,
    QueryResult,
    RelatedContext,
    TypedQuery,
)

__all__ = [
    # Types
    "ContextType",
    "TypedQuery",
    "QueryPlan",
    "RelatedContext",
    "MatchedContext",
    "QueryResult",
    "FindResult",
    # Retriever
    "HierarchicalRetriever",
    "IntentAnalyzer",
]
