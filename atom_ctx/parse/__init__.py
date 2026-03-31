# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Document parsers for various formats."""

from atom_ctx.parse.base import NodeType, ParseResult, ResourceNode, create_parse_result
from atom_ctx.parse.converter import DocumentConverter
from atom_ctx.parse.custom import CallbackParserWrapper, CustomParserProtocol, CustomParserWrapper
from atom_ctx.parse.directory_scan import (
    CLASS_PROCESSABLE,
    CLASS_UNSUPPORTED,
    ClassifiedFile,
    DirectoryScanResult,
    scan_directory,
)
from atom_ctx.parse.parsers.base_parser import BaseParser
from atom_ctx.parse.parsers.code import CodeRepositoryParser
from atom_ctx.parse.parsers.html import HTMLParser
from atom_ctx.parse.parsers.markdown import MarkdownParser
from atom_ctx.parse.parsers.pdf import PDFParser
from atom_ctx.parse.parsers.text import TextParser
from atom_ctx.parse.registry import ParserRegistry, get_registry, parse
from atom_ctx.parse.tree_builder import TreeBuilder
from atom_ctx.parse.vlm import VLMProcessor

__all__ = [
    # Base classes and helpers
    "BaseParser",
    "ResourceNode",
    "NodeType",
    "ParseResult",
    "create_parse_result",
    # Document parsers (core)
    "TextParser",
    "MarkdownParser",
    "PDFParser",
    "HTMLParser",
    "CodeRepositoryParser",
    "DocumentConverter",
    # Custom parser support
    "CustomParserProtocol",
    "CustomParserWrapper",
    "CallbackParserWrapper",
    # Registry
    "ParserRegistry",
    "get_registry",
    "parse",
    # Tree builder
    "TreeBuilder",
    "BuildingTree",
    # VLM
    "VLMProcessor",
    # Directory scan (phase-one validation)
    "CLASS_PROCESSABLE",
    "CLASS_UNSUPPORTED",
    "ClassifiedFile",
    "DirectoryScanResult",
    "scan_directory",
]
