# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Import/export tests"""

import io
import zipfile
from pathlib import Path

import pytest

from atom_ctx import AsyncAtomCtx
from atom_ctx.storage.transaction import release_all_locks


class TestExportOvpack:
    """Test export_ctxpack"""

    async def test_export_success(self, client_with_resource, temp_dir: Path):
        """Test successful export"""
        client, uri = client_with_resource
        export_path = temp_dir / "export.ctxpack"

        result = await client.export_ctxpack(uri, str(export_path))

        assert isinstance(result, str)
        assert Path(result).exists()

    async def test_export_directory(
        self, client: AsyncAtomCtx, sample_directory: Path, temp_dir: Path
    ):
        """Test exporting directory"""
        # Add files from directory
        for f in sample_directory.glob("**/*.txt"):
            await client.add_resource(path=str(f), reason="Test export dir")

        # Export entire resource directory
        export_path = temp_dir / "dir_export.ctxpack"
        result = await client.export_ctxpack("ctx://resources/", str(export_path))

        assert isinstance(result, str)


class TestImportOvpack:
    """Test import_ctxpack"""

    async def test_import_success(self, client_with_resource, temp_dir: Path):
        """Test successful import"""
        client, uri = client_with_resource

        # Export first
        export_path = temp_dir / "import_test.ctxpack"
        await client.export_ctxpack(uri, str(export_path))

        # Import to new location
        import_uri = await client.import_ctxpack(
            str(export_path), "ctx://resources/imported/", vectorize=False
        )

        assert isinstance(import_uri, str)
        assert "imported" in import_uri

    async def test_import_with_force(self, client_with_resource, temp_dir: Path):
        """Test force overwrite import"""
        client, uri = client_with_resource

        # Export first
        export_path = temp_dir / "force_test.ctxpack"
        await client.export_ctxpack(uri, str(export_path))

        # First import
        await client.import_ctxpack(
            str(export_path), "ctx://resources/force_test/", vectorize=False
        )

        # Second force import (overwrite)
        import_uri = await client.import_ctxpack(
            str(export_path), "ctx://resources/force_test/", force=True, vectorize=False
        )

        assert isinstance(import_uri, str)

    async def test_import_export_roundtrip(
        self, client: AsyncAtomCtx, sample_markdown_file: Path, temp_dir: Path
    ):
        """Test export-import roundtrip"""
        # Add resource
        result = await client.add_resource(path=str(sample_markdown_file), reason="Roundtrip test")
        original_uri = result["root_uri"]

        # Read original content
        original_content = ""
        entries = await client.tree(original_uri)
        for e in entries:
            if not e["isDir"]:
                original_content = await client.read(e["uri"])

        # Export
        export_path = temp_dir / "roundtrip.ctxpack"
        await client.export_ctxpack(original_uri, str(export_path))

        # Delete original resource
        await release_all_locks()
        await client.rm(original_uri, recursive=True)

        # Import
        import_uri = await client.import_ctxpack(
            str(export_path), "ctx://resources/roundtrip/", vectorize=False
        )

        # Read imported content
        imported_content = ""
        entries = await client.tree(import_uri)
        for e in entries:
            if not e["isDir"]:
                imported_content = await client.read(e["uri"])

        # Verify content consistency
        assert original_content == imported_content

    @staticmethod
    def _build_ctxpack(zip_path: Path, entries: dict[str, str]) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            for name, content in entries.items():
                zf.writestr(name, content)
        zip_path.write_bytes(buffer.getvalue())

    @pytest.mark.parametrize(
        "entries,error_pattern",
        [
            (
                {
                    "pkg/_._meta.json": '{"uri": "ctx://resources/pkg"}',
                    "pkg/../../escape.txt": "pwned",
                },
                "Unsafe ctxpack entry path",
            ),
            (
                {
                    "pkg/_._meta.json": '{"uri": "ctx://resources/pkg"}',
                    "/abs/path.txt": "pwned",
                },
                "Unsafe ctxpack entry path",
            ),
            (
                {
                    "pkg/_._meta.json": '{"uri": "ctx://resources/pkg"}',
                    "C:/drive/path.txt": "pwned",
                },
                "Unsafe ctxpack entry path",
            ),
            (
                {
                    "pkg/_._meta.json": '{"uri": "ctx://resources/pkg"}',
                    "pkg\\windows\\path.txt": "pwned",
                },
                "Unsafe ctxpack entry path",
            ),
            (
                {
                    "pkg/_._meta.json": '{"uri": "ctx://resources/pkg"}',
                    "other/file.txt": "pwned",
                },
                "Invalid ctxpack entry root",
            ),
        ],
    )
    async def test_import_rejects_unsafe_entries(
        self, client: AsyncAtomCtx, temp_dir: Path, entries: dict[str, str], error_pattern: str
    ):
        ctxpack_path = temp_dir / "malicious.ctxpack"
        self._build_ctxpack(ctxpack_path, entries)

        with pytest.raises(ValueError, match=error_pattern):
            await client.import_ctxpack(
                str(ctxpack_path), "ctx://resources/security/", vectorize=False
            )
