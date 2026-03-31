# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Client lifecycle tests"""

from pathlib import Path

from atom_ctx import AsyncAtomCtx


class TestClientInitialization:
    """Test Client initialization"""

    async def test_initialize_success(self, uninitialized_client: AsyncAtomCtx):
        """Test normal initialization"""
        await uninitialized_client.initialize()
        assert uninitialized_client._initialized is True

    async def test_initialize_idempotent(self, client: AsyncAtomCtx):
        """Test repeated initialization is idempotent"""
        await client.initialize()
        await client.initialize()
        assert client._initialized is True

    async def test_initialize_creates_client(self, uninitialized_client: AsyncAtomCtx):
        """Test initialization creates client"""
        await uninitialized_client.initialize()
        assert uninitialized_client._client is not None


class TestClientClose:
    """Test Client close"""

    async def test_close_success(self, test_data_dir: Path):
        """Test normal close"""
        await AsyncAtomCtx.reset()
        client = AsyncAtomCtx(path=str(test_data_dir))
        await client.initialize()

        await client.close()
        assert client._initialized is False

        await AsyncAtomCtx.reset()

    async def test_close_idempotent(self, test_data_dir: Path):
        """Test repeated close is safe"""
        await AsyncAtomCtx.reset()
        client = AsyncAtomCtx(path=str(test_data_dir))
        await client.initialize()

        await client.close()
        await client.close()  # Should not raise exception

        await AsyncAtomCtx.reset()


class TestClientReset:
    """Test Client reset"""

    async def test_reset_clears_singleton(self, test_data_dir: Path):
        """Test reset clears singleton"""
        await AsyncAtomCtx.reset()

        client1 = AsyncAtomCtx(path=str(test_data_dir))
        await client1.initialize()

        await AsyncAtomCtx.reset()

        client2 = AsyncAtomCtx(path=str(test_data_dir))
        # Should be new instance after reset
        assert client1 is not client2

        await AsyncAtomCtx.reset()


class TestClientSingleton:
    """Test Client singleton pattern"""

    async def test_embedded_mode_singleton(self, test_data_dir: Path):
        """Test embedded mode uses singleton"""
        await AsyncAtomCtx.reset()

        client1 = AsyncAtomCtx(path=str(test_data_dir))
        client2 = AsyncAtomCtx(path=str(test_data_dir))

        assert client1 is client2

        await AsyncAtomCtx.reset()
