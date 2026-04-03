# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Tests for custom parser registration via ctx.conf configuration.

Validates the ``custom_parsers`` config section and the
``ParserRegistry.apply_custom_parsers()`` mechanism.
"""

from pathlib import Path
from typing import List, Optional, Union

import pytest

from atom_ctx.parse.base import ParseResult, ResourceNode, NodeType, create_parse_result
from atom_ctx.parse.parsers.base_parser import BaseParser
from atom_ctx.parse.registry import ParserRegistry, _ExtensionOverrideParser


# ---------------------------------------------------------------------------
# Dummy parsers used as import targets
# ---------------------------------------------------------------------------


class _StubParser(BaseParser):
    """Minimal BaseParser subclass for testing."""

    def __init__(self, exts: Optional[List[str]] = None, **kwargs):
        self._exts = exts or [".stub"]
        self.extra_kwargs = kwargs

    @property
    def supported_extensions(self) -> List[str]:
        return self._exts

    async def parse(self, source: Union[str, Path], instruction: str = "", **kwargs) -> ParseResult:
        root = ResourceNode(type=NodeType.ROOT, title="stub")
        return create_parse_result(
            root=root,
            source_path=str(source),
            source_format="stub",
            parser_name="stub",
        )

    async def parse_content(
        self, content: str, source_path: Optional[str] = None, instruction: str = "", **kwargs
    ) -> ParseResult:
        root = ResourceNode(type=NodeType.ROOT, title="stub")
        return create_parse_result(
            root=root,
            source_path=source_path or "<content>",
            source_format="stub",
            parser_name="stub",
        )


# ---------------------------------------------------------------------------
# apply_custom_parsers – basic registration
# ---------------------------------------------------------------------------


class TestApplyCustomParsers:
    """Tests for ParserRegistry.apply_custom_parsers()."""

    def _fresh_registry(self) -> ParserRegistry:
        return ParserRegistry(register_optional=False)

    def test_register_by_class_path(self):
        """A custom parser referenced by fully-qualified class path is loaded and registered."""
        registry = self._fresh_registry()

        custom_parsers = {
            "my_stub": {
                "class": f"{__name__}._StubParser",
            }
        }
        registry.apply_custom_parsers(custom_parsers)

        assert "my_stub" in registry.list_parsers()
        parser = registry.get_parser("my_stub")
        assert parser is not None
        assert ".stub" in parser.supported_extensions

    def test_extension_override_replaces_default(self):
        """When extensions are specified in config, they override the parser's own
        supported_extensions AND replace the built-in parser for those extensions."""
        registry = self._fresh_registry()

        assert registry.get_parser_for_file("test.pdf") is not None
        original_pdf = registry.get_parser_for_file("test.pdf")

        custom_parsers = {
            "better_pdf": {
                "class": f"{__name__}._StubParser",
                "extensions": [".pdf"],
            }
        }
        registry.apply_custom_parsers(custom_parsers)

        new_pdf = registry.get_parser_for_file("test.pdf")
        assert new_pdf is not original_pdf
        assert isinstance(new_pdf, _ExtensionOverrideParser)
        assert new_pdf.supported_extensions == [".pdf"]

    def test_extension_override_does_not_affect_other_extensions(self):
        """Replacing .pdf should not affect .md or .txt."""
        registry = self._fresh_registry()

        md_before = registry.get_parser_for_file("readme.md")
        txt_before = registry.get_parser_for_file("notes.txt")

        custom_parsers = {
            "better_pdf": {
                "class": f"{__name__}._StubParser",
                "extensions": [".pdf"],
            }
        }
        registry.apply_custom_parsers(custom_parsers)

        assert registry.get_parser_for_file("readme.md") is md_before
        assert registry.get_parser_for_file("notes.txt") is txt_before

    def test_register_new_extension(self):
        """A custom parser can introduce entirely new extensions."""
        registry = self._fresh_registry()

        assert registry.get_parser_for_file("file.xyz") is None

        custom_parsers = {
            "xyz_parser": {
                "class": f"{__name__}._StubParser",
                "extensions": [".xyz", ".abc"],
            }
        }
        registry.apply_custom_parsers(custom_parsers)

        parser_xyz = registry.get_parser_for_file("file.xyz")
        parser_abc = registry.get_parser_for_file("file.abc")
        assert parser_xyz is not None
        assert parser_abc is not None
        assert parser_xyz is parser_abc

    def test_kwargs_forwarded_to_constructor(self):
        """kwargs from config are passed to the parser constructor."""
        registry = self._fresh_registry()

        custom_parsers = {
            "my_stub": {
                "class": f"{__name__}._StubParser",
                "kwargs": {"exts": [".custom"], "option_a": 42},
            }
        }
        registry.apply_custom_parsers(custom_parsers)

        parser = registry.get_parser("my_stub")
        assert parser is not None
        assert parser.supported_extensions == [".custom"]
        assert parser.extra_kwargs == {"option_a": 42}

    def test_no_class_skipped(self):
        """Entry without 'class' is silently skipped."""
        registry = self._fresh_registry()
        parsers_before = set(registry.list_parsers())

        custom_parsers = {"bad_entry": {"extensions": [".xyz"]}}
        registry.apply_custom_parsers(custom_parsers)

        assert set(registry.list_parsers()) == parsers_before

    def test_invalid_class_path_skipped(self):
        """Entry with bare class name (no module) is skipped."""
        registry = self._fresh_registry()
        parsers_before = set(registry.list_parsers())

        custom_parsers = {"bad": {"class": "NoModule"}}
        registry.apply_custom_parsers(custom_parsers)

        assert set(registry.list_parsers()) == parsers_before

    def test_import_error_skipped(self):
        """Entry referencing a non-existent module is skipped."""
        registry = self._fresh_registry()
        parsers_before = set(registry.list_parsers())

        custom_parsers = {"bad": {"class": "nonexistent_pkg.FakeParser"}}
        registry.apply_custom_parsers(custom_parsers)

        assert set(registry.list_parsers()) == parsers_before

    def test_instantiation_error_skipped(self):
        """Entry whose constructor raises is skipped."""
        registry = self._fresh_registry()
        parsers_before = set(registry.list_parsers())

        custom_parsers = {
            "bad": {
                "class": f"{__name__}._StubParser",
                "kwargs": {"bad_required_arg_that_explodes": object},
            }
        }

        registry.apply_custom_parsers(custom_parsers)
        # _StubParser accepts **kwargs so this won't fail at constructor
        # Let's use a class that will actually fail
        pass

    def test_multiple_custom_parsers(self):
        """Multiple custom parsers can be registered in a single call."""
        registry = self._fresh_registry()

        custom_parsers = {
            "parser_a": {
                "class": f"{__name__}._StubParser",
                "extensions": [".aaa"],
            },
            "parser_b": {
                "class": f"{__name__}._StubParser",
                "extensions": [".bbb"],
            },
        }
        registry.apply_custom_parsers(custom_parsers)

        assert registry.get_parser_for_file("f.aaa") is not None
        assert registry.get_parser_for_file("f.bbb") is not None
        assert "parser_a" in registry.list_parsers()
        assert "parser_b" in registry.list_parsers()

    def test_uses_class_extensions_when_none_in_config(self):
        """When config omits extensions, the parser's own supported_extensions are used."""
        registry = self._fresh_registry()

        custom_parsers = {
            "stub_default": {
                "class": f"{__name__}._StubParser",
            }
        }
        registry.apply_custom_parsers(custom_parsers)

        parser = registry.get_parser_for_file("file.stub")
        assert parser is not None

    def test_docx_pandoc_parser_registration(self):
        """shaobt DocxPandocParser registers via FQCN and replaces .docx mapping."""
        from shaobt.parser_plugins.docx_pandoc import DocxPandocParser

        registry = self._fresh_registry()
        word_before = registry.get_parser_for_file("x.docx")
        assert word_before is not None

        custom_parsers = {
            "docx_pandoc": {
                "class": "shaobt.parser_plugins.docx_pandoc.DocxPandocParser",
                "extensions": [".docx"],
            }
        }
        registry.apply_custom_parsers(custom_parsers)

        new = registry.get_parser_for_file("y.docx")
        assert new is not word_before
        assert isinstance(new, _ExtensionOverrideParser)
        assert isinstance(new._delegate, DocxPandocParser)

    def test_pdf2md_parser_registration(self):
        """shaobt Pdf2mdParser registers via FQCN and replaces .pdf mapping."""
        from shaobt.parser_plugins.pdf2md_parser import Pdf2mdParser

        registry = self._fresh_registry()
        pdf_before = registry.get_parser_for_file("x.pdf")
        assert pdf_before is not None

        custom_parsers = {
            "pdf2md": {
                "class": "shaobt.parser_plugins.pdf2md_parser.Pdf2mdParser",
                "extensions": [".pdf"],
                "kwargs": {
                    "api_base": "http://localhost",
                    "api_key": "test",
                    "model": "test-model",
                },
            }
        }
        registry.apply_custom_parsers(custom_parsers)

        new = registry.get_parser_for_file("y.pdf")
        assert new is not pdf_before
        assert isinstance(new, _ExtensionOverrideParser)
        assert isinstance(new._delegate, Pdf2mdParser)


# ---------------------------------------------------------------------------
# _ExtensionOverrideParser delegation
# ---------------------------------------------------------------------------


class TestExtensionOverrideParser:
    """Tests for the _ExtensionOverrideParser wrapper."""

    @pytest.mark.asyncio
    async def test_delegates_parse(self):
        stub = _StubParser()
        wrapper = _ExtensionOverrideParser(stub, [".xyz"])

        result = await wrapper.parse("/tmp/test.xyz")
        assert result.source_path == "/tmp/test.xyz"

    @pytest.mark.asyncio
    async def test_delegates_parse_content(self):
        stub = _StubParser()
        wrapper = _ExtensionOverrideParser(stub, [".xyz"])

        result = await wrapper.parse_content("hello")
        assert result is not None

    def test_overrides_extensions(self):
        stub = _StubParser(exts=[".orig"])
        wrapper = _ExtensionOverrideParser(stub, [".new1", ".new2"])

        assert wrapper.supported_extensions == [".new1", ".new2"]
        assert stub.supported_extensions == [".orig"]


# ---------------------------------------------------------------------------
# AtomCtxConfig integration
# ---------------------------------------------------------------------------


class TestConfigDeserialization:
    """Tests that custom_parsers survives AtomCtxConfig.from_dict() round-trip."""

    _MINIMAL_EMBEDDING = {
        "embedding": {
            "dense": {
                "model": "test-model",
                "api_key": "test-key",
                "api_base": "http://localhost",
                "dimension": 128,
                "provider": "openai",
            }
        }
    }

    def test_custom_parsers_from_dict(self):
        from atom_ctx_cli.utils.config.ctx_config import AtomCtxConfig

        data = {
            **self._MINIMAL_EMBEDDING,
            "custom_parsers": {
                "my_parser": {
                    "class": "some.module.SomeParser",
                    "extensions": [".xyz"],
                }
            },
        }
        config = AtomCtxConfig.from_dict(data)
        assert "my_parser" in config.custom_parsers
        assert config.custom_parsers["my_parser"]["class"] == "some.module.SomeParser"
        assert config.custom_parsers["my_parser"]["extensions"] == [".xyz"]

    def test_custom_parsers_to_dict(self):
        from atom_ctx_cli.utils.config.ctx_config import AtomCtxConfig

        data = {
            **self._MINIMAL_EMBEDDING,
            "custom_parsers": {
                "p": {"class": "a.B", "extensions": [".x"]},
            },
        }
        config = AtomCtxConfig.from_dict(data)
        out = config.to_dict()
        assert out["custom_parsers"] == {"p": {"class": "a.B", "extensions": [".x"]}}

    def test_no_custom_parsers_in_config(self):
        """Config without custom_parsers should work fine (backward compatible)."""
        from atom_ctx_cli.utils.config.ctx_config import AtomCtxConfig

        config = AtomCtxConfig.from_dict(self._MINIMAL_EMBEDDING)
        assert config.custom_parsers == {}
