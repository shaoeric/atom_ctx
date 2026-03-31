# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Tests for client-side temp uploads when using localhost URLs."""

import pytest

from atom_ctx_cli.client.http import AsyncHTTPClient


class _FakeHTTPClient:
    def __init__(self):
        self.calls = []

    async def post(self, path, json=None, files=None):
        self.calls.append({"path": path, "json": json, "files": files})
        return object()


@pytest.mark.asyncio
async def test_add_skill_uploads_local_file_even_when_url_is_localhost(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("---\nname: demo\ndescription: demo\n---\n\n# Demo\n")

    client = AsyncHTTPClient(url="http://localhost:1933")
    fake_http = _FakeHTTPClient()
    client._http = fake_http

    async def fake_upload(_path: str) -> str:
        return "upload_skill.md"

    client._upload_temp_file = fake_upload
    client._handle_response_data = lambda _response: {"result": {"status": "ok"}}

    await client.add_skill(str(skill_file))

    call = fake_http.calls[-1]
    assert call["path"] == "/api/v1/skills"
    assert call["json"]["temp_file_id"] == "upload_skill.md"
    assert "data" not in call["json"]


@pytest.mark.asyncio
async def test_add_resource_uploads_local_file_even_when_url_is_localhost(tmp_path):
    resource_file = tmp_path / "demo.md"
    resource_file.write_text("# Demo\n")

    client = AsyncHTTPClient(url="http://127.0.0.1:1933")
    fake_http = _FakeHTTPClient()
    client._http = fake_http

    async def fake_upload(_path: str) -> str:
        return "upload_resource.md"

    client._upload_temp_file = fake_upload
    client._handle_response_data = lambda _response: {
        "result": {"root_uri": "ctx://resources/demo"}
    }

    await client.add_resource(str(resource_file), reason="test")

    call = fake_http.calls[-1]
    assert call["path"] == "/api/v1/resources"
    assert call["json"]["temp_file_id"] == "upload_resource.md"
    assert "path" not in call["json"]


@pytest.mark.asyncio
async def test_import_ctxpack_uploads_local_file_even_when_url_is_localhost(tmp_path):
    pack_file = tmp_path / "demo.ctxpack"
    pack_file.write_bytes(b"ctxpack")

    client = AsyncHTTPClient(url="http://localhost:1933")
    fake_http = _FakeHTTPClient()
    client._http = fake_http

    async def fake_upload(_path: str) -> str:
        return "upload_pack.ctxpack"

    client._upload_temp_file = fake_upload
    client._handle_response = lambda _response: {"uri": "ctx://resources/imported"}

    await client.import_ctxpack(str(pack_file), parent="ctx://resources/")

    call = fake_http.calls[-1]
    assert call["path"] == "/api/v1/pack/import"
    assert call["json"]["temp_file_id"] == "upload_pack.ctxpack"
    assert "file_path" not in call["json"]


@pytest.mark.asyncio
async def test_import_ctxpack_fails_fast_when_local_file_is_missing(tmp_path):
    client = AsyncHTTPClient(url="http://localhost:1933")
    fake_http = _FakeHTTPClient()
    client._http = fake_http

    missing_path = tmp_path / "missing.ctxpack"

    with pytest.raises(FileNotFoundError, match="Local ctxpack file not found"):
        await client.import_ctxpack(str(missing_path), parent="ctx://resources/")

    assert fake_http.calls == []


@pytest.mark.asyncio
async def test_import_ctxpack_fails_fast_when_path_is_directory(tmp_path):
    client = AsyncHTTPClient(url="http://localhost:1933")
    fake_http = _FakeHTTPClient()
    client._http = fake_http

    pack_dir = tmp_path / "pack_dir"
    pack_dir.mkdir()

    with pytest.raises(ValueError, match="is not a file"):
        await client.import_ctxpack(str(pack_dir), parent="ctx://resources/")

    assert fake_http.calls == []
