from datetime import datetime
from unittest.mock import patch, AsyncMock

import pytest

from app.models.ssh_response import SSHResponse
from app.services.device_service import _parse_neigh_output, _ping, get_device_status_by_ip
from tests.conftest import TEST_MAC, TEST_IP

REACHABLE_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","lladdr":"{TEST_MAC}","state":["REACHABLE"]}}]'
STALE_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","lladdr":"{TEST_MAC}","state":["STALE"]}}]'
INCOMPLETE_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","state":["INCOMPLETE"]}}]'
FAILED_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","state":["FAILED"]}}]'
EMPTY_RAW = "[]"


@pytest.mark.parametrize("state, has_mac, expected_mac", [
    ("REACHABLE", True,
     TEST_MAC),
    ("STALE", True, TEST_MAC),
    ("INCOMPLETE", False, None),
    ("FAILED", False, None),
])
def test_parse_known_states(state, has_mac, expected_mac):
    lladdr_field = f',"lladdr":"{TEST_MAC}"' if has_mac else ""
    raw = (
        f'[{{"dst":"{TEST_IP}","dev":"br-lan"'
        f'{lladdr_field},"state":["{state}"]}}]'
    )
    result_state, result_mac = _parse_neigh_output(raw, TEST_IP)
    assert result_state == state
    assert result_mac == expected_mac


@pytest.mark.parametrize("raw", [
    "",
    "[]",
    "not json",
])
def test_parse_invalid_input_returns_none(raw):
    state, mac = _parse_neigh_output(raw, TEST_IP)
    assert state is None
    assert mac is None


def test_parse_ip_not_in_results():
    other_ip = "203.0.113.99"
    raw = (
        f'[{{"dst":"{other_ip}","dev":"br-lan",'
        f'"lladdr":"{TEST_MAC}","state":["REACHABLE"]}}]'
    )
    state, mac = _parse_neigh_output(raw, TEST_IP)
    assert state is None
    assert mac is None


@pytest.mark.parametrize("code, reachable", [(0, True), (1, False), (22, False)])
async def test_ping_returns_bool_on_exit_code_0(code, reachable):
    with patch(
            "app.services.device_service.ssh_manager.run_command",
            new=AsyncMock(return_value=SSHResponse(success=True, output="", exit_code=code)),
    ):
        assert await _ping(TEST_IP) is reachable


async def test_status_reachable_is_online():
    with patch("app.services.device_service.ssh_manager.run_command",
               new=AsyncMock(return_value=SSHResponse(True, REACHABLE_RAW, 0))):
        result = await get_device_status_by_ip(TEST_IP)

    assert result.online is True
    assert result.state == "REACHABLE"
    assert result.mac == TEST_MAC
    assert isinstance(result.checked_at, datetime)


async def test_status_failed_is_offline():
    with patch("app.services.device_service.ssh_manager.run_command",
               new=AsyncMock(return_value=SSHResponse(True, FAILED_RAW, 0))):
        result = await get_device_status_by_ip(TEST_IP)

    assert result.online is False
    assert result.state == "FAILED"


async def test_status_not_in_arp_table_is_offline():
    with patch("app.services.device_service.ssh_manager.run_command",
               new=AsyncMock(return_value=SSHResponse(True, EMPTY_RAW, 0))):
        result = await get_device_status_by_ip(TEST_IP)

    assert result.online is False
    assert result.state is None


@pytest.mark.parametrize("state_raw, ping_status, expected_state, expected_online", [
    (STALE_RAW, True, "STALE", True),
    (STALE_RAW, False, "STALE", False),
    (INCOMPLETE_RAW, True, "INCOMPLETE", True),
    (INCOMPLETE_RAW, False, "INCOMPLETE", False),
])
async def test_online_state_based_on_status_and_ping(state_raw, ping_status, expected_state, expected_online):
    with (
        patch("app.services.device_service.ssh_manager.run_command",
              new=AsyncMock(return_value=SSHResponse(True, state_raw, 0))),
        patch("app.services.device_service._ping", new=AsyncMock(return_value=ping_status)),
    ):
        result = await get_device_status_by_ip(TEST_IP)

    assert result.online is expected_online
    assert result.state == expected_state


@pytest.mark.parametrize("state", [REACHABLE_RAW, FAILED_RAW])
async def test_ping_not_called_for_(state):
    with (
        patch("app.services.device_service.ssh_manager.run_command",
              new=AsyncMock(return_value=SSHResponse(True, state, 0))),
        patch("app.services.device_service._ping", new=AsyncMock()) as mock_ping,
    ):
        await get_device_status_by_ip(TEST_IP)

    mock_ping.assert_not_called()
