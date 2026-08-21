import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ssh_manager import SSHManager
from tests.conftest import TEST_IP


@pytest.fixture
def manager():
    return SSHManager()


@pytest.fixture
def connected_manager():
    manager = SSHManager()
    mock_conn = AsyncMock()
    mock_conn.is_closed = MagicMock(return_value=False)
    mock_conn.close = MagicMock()
    manager._connection = mock_conn
    return manager, mock_conn


async def test_is_connected_false_by_default(manager):
    assert manager.is_connected() is False


async def test_is_connected_false_when_connection_is_closed(manager):
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = True
    manager._connection = mock_conn

    assert manager.is_connected() is False


async def test_is_connected_true_when_connection_is_open(manager):
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False
    manager._connection = mock_conn

    assert manager.is_connected() is True


async def test_connect_handles_timeout_gracefully(manager):
    with patch(
            "app.services.ssh_manager.asyncssh.connect",
            side_effect=TimeoutError,
    ):
        await manager.connect()

    assert manager._connection is None


async def test_run_command_triggers_connect_when_disconnected(manager):
    mock_result = MagicMock()
    mock_result.stdout = "REACHABLE"

    mock_conn = AsyncMock()
    mock_conn.is_closed = MagicMock(return_value=False)
    mock_conn.run = AsyncMock(return_value=mock_result)

    with patch("app.services.ssh_manager.asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        output = await manager.run_command(f"ip neigh show {TEST_IP}")

    assert output.success is True
    assert output.output == "REACHABLE"
    assert manager.is_connected() is True


async def test_run_command_does_not_reconnect_when_already_connected(connected_manager):
    manager, mock_conn = connected_manager

    mock_result = MagicMock()
    mock_result.stdout = "pong"
    mock_conn.run = AsyncMock(return_value=mock_result)

    with patch("app.services.ssh_manager.asyncssh.connect") as mock_connect:
        await manager.run_command("ping")
        mock_connect.assert_not_called()


async def test_reconnects_when_connection_lost(manager):
    mock_result = MagicMock()
    mock_result.stdout = "ok"

    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=mock_result)
    mock_conn.is_closed = MagicMock(return_value=True)
    manager._connection = mock_conn

    async def fake_connect(**kwargs):
        mock_conn.is_closed.return_value = False
        return mock_conn

    with patch("app.services.ssh_manager.asyncssh.connect", side_effect=fake_connect) as mock_connect:
        await manager.run_command("echo ok")
        mock_connect.assert_called_once()


async def test_reconnect_count_increments_on_each_reconnect(manager):
    mock_result = MagicMock()
    mock_result.stdout = "ok"

    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=mock_result)
    mock_conn.is_closed = MagicMock(return_value=False)

    assert manager.reconnect_count == 0

    with patch("app.services.ssh_manager.asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        await manager.run_command("cmd1")
        assert manager.reconnect_count == 1

        manager._connection = None
        await manager.run_command("cmd2")
        assert manager.reconnect_count == 2


async def test_run_command_returns_failure_when_cannot_connect(manager):
    with patch(
            "app.services.ssh_manager.asyncssh.connect",
            side_effect=TimeoutError,
    ):
        output = await manager.run_command("any command")

    assert output.success is False
    assert output.output == ""


async def test_disconnect_closes_connection(connected_manager):
    manager, mock_conn = connected_manager

    await manager.disconnect()

    mock_conn.close.assert_called_once()
    mock_conn.wait_closed.assert_awaited_once()
    assert manager._connection is None
    assert manager.is_connected() is False


async def test_disconnect_is_noop_when_not_connected(manager):
    await manager.disconnect()
    assert manager._connection is None


async def test_is_connected_false_after_disconnect(connected_manager):
    manager, _ = connected_manager

    assert manager.is_connected() is True
    await manager.disconnect()
    assert manager.is_connected() is False


async def test_run_command_is_thread_safe_under_concurrent_calls(manager):
    call_count = 0

    async def fake_connect(**kwargs):
        nonlocal call_count
        call_count += 1
        mock_conn = AsyncMock()
        mock_conn.is_closed = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.stdout = "ok"
        mock_conn.run = AsyncMock(return_value=mock_result)
        return mock_conn

    with patch("app.services.ssh_manager.asyncssh.connect", side_effect=fake_connect):
        await asyncio.gather(*[manager.run_command("echo ok") for _ in range(10)])

    assert call_count == 1
