# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Parser registry for AtomCtx.

Provides automatic parser selection based on file type.
"""

import importlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from atom_ctx.parse.base import ParseResult
from atom_ctx.parse.parsers.base_parser import BaseParser
from atom_ctx.parse.parsers.code import CodeRepositoryParser
from atom_ctx.parse.parsers.directory import DirectoryParser
from atom_ctx.parse.parsers.epub import EPubParser
from atom_ctx.parse.parsers.excel import ExcelParser

# Import will be handled dynamically to avoid dependency issues
from atom_ctx.parse.parsers.html import HTMLParser
from atom_ctx.parse.parsers.markdown import MarkdownParser
from atom_ctx.parse.parsers.media import AudioParser, ImageParser, VideoParser
from atom_ctx.parse.parsers.pdf import PDFParser
from atom_ctx.parse.parsers.powerpoint import PowerPointParser
from atom_ctx.parse.parsers.text import TextParser

# Import markitdown-inspired parsers
from atom_ctx.parse.parsers.legacy_doc import LegacyDocParser
from atom_ctx.parse.parsers.word import WordParser
from atom_ctx.parse.parsers.zip_parser import ZipParser

if TYPE_CHECKING:
    from atom_ctx.parse.custom import CustomParserProtocol

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Registry for document parsers, which is a singleton.

    Automatically selects appropriate parser based on file extension.
    """

    def __init__(self, register_optional: bool = True):
        """
        Initialize registry with default parsers.

        Args:
            register_optional: Whether to register optional parsers
                              that require extra dependencies
            parser_configs: Dictionary of parser configurations (from load_parser_configs_from_dict)
        """
        self._parsers: Dict[str, BaseParser] = {}
        self._extension_map: Dict[str, str] = {}

        # Register core parsers
        self.register("text", TextParser())
        self.register("markdown", MarkdownParser())
        self.register("pdf", PDFParser())
        self.register("html", HTMLParser())  # HTMLParser doesn't accept config yet

        # Register markitdown-inspired parsers (built-in)
        self.register("word", WordParser())
        self.register("legacy_doc", LegacyDocParser())
        self.register("powerpoint", PowerPointParser())
        self.register("excel", ExcelParser())
        self.register("epub", EPubParser())
        # CodeRepositoryParser also uses .zip; register it before ZipParser
        # so that .zip resolves to ZipParser (file) rather than code repo.
        self.register("code", CodeRepositoryParser())
        self.register("zip", ZipParser())
        self.register("directory", DirectoryParser())

        self.register("image", ImageParser())
        self.register("audio", AudioParser())
        self.register("video", VideoParser())

        # Optional: Feishu/Lark document parser (requires lark-oapi)
        try:
            from atom_ctx.parse.parsers.feishu import FeishuParser

            self.register("feishu", FeishuParser())
        except ImportError:
            pass

    def register(self, name: str, parser: BaseParser) -> None:
        """
        Register a parser.

        Args:
            name: Parser name
            parser: Parser instance
        """
        self._parsers[name] = parser

        # Map extensions to parser name
        for ext in parser.supported_extensions:
            self._extension_map[ext.lower()] = name

    def register_custom(
        self,
        handler: "CustomParserProtocol",
        extensions: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Register a custom parser (Protocol-based).

        Args:
            handler: Object implementing CustomParserProtocol
            extensions: Optional list of extensions (overrides handler's extensions)
            name: Optional parser name (default: "custom_N")

        Example:
            ```python
            class MyParser:
                @property
                def supported_extensions(self) -> List[str]:
                    return [".xyz"]

                def can_handle(self, source) -> bool:
                    return str(source).endswith(".xyz")

                async def parse(self, source, **kwargs) -> ParseResult:
                    ...

            registry.register_custom(MyParser(), name="xyz_parser")
            ```
        """
        from atom_ctx.parse.custom import CustomParserWrapper

        # Generate name if not provided
        if name is None:
            # Count existing custom parsers
            custom_count = sum(1 for n in self._parsers if n.startswith("custom_"))
            name = f"custom_{custom_count}"

        # Wrap and register
        wrapper = CustomParserWrapper(handler, extensions=extensions)
        self.register(name, wrapper)  # type: ignore
        logger.info(f"Registered custom parser '{name}' for {wrapper.supported_extensions}")

    def register_callback(
        self,
        extension: str,
        parse_fn: "Callable[[Union[str, Path]], ParseResult]",
        name: Optional[str] = None,
    ) -> None:
        """
        Register a callback function as a parser.

        Args:
            extension: File extension (e.g., ".xyz")
            parse_fn: Async function that parses and returns ParseResult
            name: Optional parser name (default: "callback_<ext>")

        Example:
            ```python
            async def my_parser(source: Union[str, Path], **kwargs) -> ParseResult:
                content = Path(source).read_text()
                return create_parse_result(
                    root=ResourceNode(type=NodeType.ROOT, content=content),
                    source_path=str(source),
                    source_format="custom",
                    parser_name="my_parser",
                )

            registry.register_callback(".xyz", my_parser)
            ```
        """
        from atom_ctx.parse.custom import CallbackParserWrapper

        # Generate name if not provided
        if name is None:
            name = f"callback{extension}"

        # Wrap and register
        wrapper = CallbackParserWrapper(extension, parse_fn, name=name)
        self.register(name, wrapper)  # type: ignore
        logger.info(f"Registered callback parser '{name}' for {extension}")

    def unregister(self, name: str) -> None:
        """Remove a parser from registry."""
        if name in self._parsers:
            parser = self._parsers[name]
            for ext in parser.supported_extensions:
                if self._extension_map.get(ext.lower()) == name:
                    del self._extension_map[ext.lower()]
            del self._parsers[name]

    def get_parser(self, name: str) -> Optional[BaseParser]:
        """Get parser by name."""
        return self._parsers.get(name)

    def get_parser_for_file(self, path: Union[str, Path]) -> Optional[BaseParser]:
        """
        Get appropriate parser for a file.

        Args:
            path: File path

        Returns:
            Parser instance or None if no suitable parser found
        """
        path = Path(path)
        ext = path.suffix.lower()
        parser_name = self._extension_map.get(ext)

        if parser_name:
            return self._parsers.get(parser_name)

        return None

    async def parse(self, source: Union[str, Path], **kwargs) -> ParseResult:
        """
        Parse a file or content string.

        Automatically selects parser based on file extension.
        Falls back to text parser for unknown types.

        Args:
            source: File path or content string
            **kwargs: Additional arguments passed to parser

        Returns:
            ParseResult with document tree
        """
        source_str = str(source)

        # First, check if it's a code repository URL
        code_parser = self._parsers.get("code")
        if code_parser:
            # Check if the parser has the is_repository_url method
            try:
                if hasattr(code_parser, "is_repository_url") and code_parser.is_repository_url(
                    source_str
                ):
                    logger.info(f"Detected code repository URL: {source_str}")
                    return await code_parser.parse(source_str, **kwargs)
            except Exception as e:
                logger.warning(f"Error checking if source is repository URL: {e}")
                # Continue with normal parsing flow

        # Check if source looks like a file path (short enough and no newlines)
        is_potential_path = len(source_str) <= 1024 and "\n" not in source_str

        if is_potential_path:
            path = Path(source)
            if path.exists():
                # Directory → route to DirectoryParser
                if path.is_dir():
                    dir_parser = self._parsers.get("directory")
                    if dir_parser:
                        return await dir_parser.parse(path, **kwargs)
                    raise ValueError(
                        f"Source is a directory but DirectoryParser is not registered: {path}"
                    )

                parser = self.get_parser_for_file(path)
                if parser:
                    return await parser.parse(path, **kwargs)
                else:
                    return await self._parsers["text"].parse(path, **kwargs)

        # Content string - use text parser
        return await self._parsers["text"].parse_content(source_str, **kwargs)

    def list_parsers(self) -> List[str]:
        """List registered parser names."""
        return list(self._parsers.keys())

    def list_supported_extensions(self) -> List[str]:
        """List all supported file extensions."""
        return list(self._extension_map.keys())

    def apply_custom_parsers(self, custom_parsers: Dict[str, Dict[str, Any]]) -> None:
        """Load and register custom parsers from configuration.

        Each entry in *custom_parsers* maps a parser name to a descriptor dict
        with the following keys:

        * ``class`` (required) – fully-qualified Python class path
          (e.g. ``"my_pkg.parsers.MyPDFParser"``).  The class must be a
          ``BaseParser`` subclass **or** implement ``CustomParserProtocol``.
        * ``extensions`` (optional) – list of file extensions this parser
          should handle (e.g. ``[".pdf"]``).  When provided, only these
          extensions are mapped to the parser; otherwise the class's own
          ``supported_extensions`` is used.
        * ``kwargs`` (optional) – keyword arguments forwarded to the class
          constructor.

        Because ``register()`` overwrites the extension mapping, calling this
        method *after* the built-in parsers are registered is enough to
        replace the default parser for any extension – no priority mechanism
        required.
        """
        for name, entry in custom_parsers.items():
            class_path = entry.get("class")
            if not class_path:
                logger.warning("custom_parsers.%s: missing 'class', skipped", name)
                continue

            module_path, _, class_name = class_path.rpartition(".")
            if not module_path:
                logger.warning(
                    "custom_parsers.%s: invalid class path '%s' "
                    "(expected 'module.ClassName')",
                    name,
                    class_path,
                )
                continue

            try:
                mod = importlib.import_module(module_path)
                cls_ = getattr(mod, class_name)
            except (ImportError, AttributeError) as exc:
                logger.error(
                    "custom_parsers.%s: failed to import '%s': %s",
                    name,
                    class_path,
                    exc,
                )
                continue

            kwargs = entry.get("kwargs", {})
            try:
                parser_instance = cls_(**kwargs)
            except Exception as exc:
                logger.error(
                    "custom_parsers.%s: failed to instantiate '%s': %s",
                    name,
                    class_path,
                    exc,
                )
                continue

            config_extensions: Optional[List[str]] = entry.get("extensions")

            if config_extensions and isinstance(parser_instance, BaseParser):
                wrapped = _ExtensionOverrideParser(parser_instance, config_extensions)
                self.register(name, wrapped)
            elif config_extensions:
                from atom_ctx.parse.custom import CustomParserWrapper

                wrapped = CustomParserWrapper(parser_instance, extensions=config_extensions)
                self.register(name, wrapped)  # type: ignore[arg-type]
            else:
                self.register(name, parser_instance)

            effective_exts = config_extensions or getattr(
                parser_instance, "supported_extensions", []
            )
            logger.info(
                "Registered custom parser '%s' (%s) for extensions %s",
                name,
                class_path,
                effective_exts,
            )


class _ExtensionOverrideParser(BaseParser):
    """Thin wrapper that delegates to another BaseParser but overrides
    ``supported_extensions`` with a caller-supplied list."""

    def __init__(self, delegate: BaseParser, extensions: List[str]) -> None:
        self._delegate = delegate
        self._extensions = extensions

    @property
    def supported_extensions(self) -> List[str]:
        return self._extensions

    async def parse(self, source, instruction: str = "", **kwargs):
        return await self._delegate.parse(source, instruction=instruction, **kwargs)

    async def parse_content(self, content, source_path=None, instruction: str = "", **kwargs):
        return await self._delegate.parse_content(
            content, source_path=source_path, instruction=instruction, **kwargs
        )


# Global registry instance
_default_registry: Optional[ParserRegistry] = None


def get_registry() -> ParserRegistry:
    """Get the default parser registry.

    On first call the registry is created with built-in parsers, then any
    ``custom_parsers`` entries found in the loaded ``AtomCtxConfig`` are
    applied (silently skipped if the config singleton is not yet initialised).
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = ParserRegistry()
        _try_load_custom_parsers(_default_registry)
    return _default_registry


def _try_load_custom_parsers(registry: ParserRegistry) -> None:
    """Apply custom parsers from AtomCtxConfig if available.

    Failures (config not loaded, import errors, etc.) are logged at debug
    level and silently ignored so that the registry remains usable even
    without a configuration file.
    """
    try:
        from atom_ctx_cli.utils.config.ctx_config import AtomCtxConfigSingleton

        config = AtomCtxConfigSingleton.get_instance()
        if config.custom_parsers:
            registry.apply_custom_parsers(config.custom_parsers)
    except Exception:
        logger.debug("custom_parsers: config not available, skipping", exc_info=True)


async def parse(source: Union[str, Path], **kwargs) -> ParseResult:
    """
    Parse a document using the default registry.

    Args:
        source: File path or content string
        **kwargs: Additional arguments passed to parser

    Returns:
        ParseResult with document tree
    """
    return await get_registry().parse(source, **kwargs)
