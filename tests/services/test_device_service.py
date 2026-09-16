from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models.ssh_response import SSHResponse
from app.services.device_service import (
    _parse_neigh_output_by_ip,
    _parse_neigh_output_by_mac,
    _ping,
    get_device_status_by_ip,
    get_device_status_by_mac,
)
from tests.conftest import TEST_IP, TEST_MAC

REACHABLE_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","lladdr":"{TEST_MAC}","state":["REACHABLE"]}}]'
STALE_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","lladdr":"{TEST_MAC}","state":["STALE"]}}]'
INCOMPLETE_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","state":["INCOMPLETE"]}}]'
FAILED_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","state":["FAILED"]}}]'

EMPTY_RAW = "[]"

FULL_TABLE_RAW = REACHABLE_RAW
FULL_TABLE_STALE_RAW = STALE_RAW
FULL_TABLE_NO_MAC_RAW = f'[{{"dst":"{TEST_IP}","dev":"br-lan","state":["REACHABLE"]}}]'


@pytest.mark.parametrize(
    "state, has_mac, expected_mac",
    [
        ("REACHABLE", True, TEST_MAC),
        ("STALE", True, TEST_MAC),
        ("INCOMPLETE", False, None),
        ("FAILED", False, None),
    ],
)
def test_parse_known_states(state, has_mac, expected_mac):
    lladdr_field = f',"lladdr":"{TEST_MAC}"' if has_mac else ""
    raw = f'[{{"dst":"{TEST_IP}","dev":"br-lan"{lladdr_field},"state":["{state}"]}}]'
    result_state, result_mac = _parse_neigh_output_by_ip(raw, TEST_IP)
    assert result_state == state
    assert result_mac == expected_mac


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "[]",
        "not json",
    ],
)
def test_parse_invalid_input_returns_none(raw):
    state, mac = _parse_neigh_output_by_ip(raw, TEST_IP)
    assert state is None
    assert mac is None


def test_parse_ip_not_in_results():
    other_ip = "203.0.113.99"
    raw = f'[{{"dst":"{other_ip}","dev":"br-lan","lladdr":"{TEST_MAC}","state":["REACHABLE"]}}]'
    state, mac = _parse_neigh_output_by_ip(raw, TEST_IP)
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
    with patch(
        "app.services.device_service.ssh_manager.run_command",
        new=AsyncMock(return_value=SSHResponse(True, REACHABLE_RAW, 0)),
    ):
        result = await get_device_status_by_ip(TEST_IP)

    assert result.online is True
    assert result.state == "REACHABLE"
    assert result.mac == TEST_MAC
    assert isinstance(result.checked_at, datetime)


async def test_status_failed_is_offline():
    with patch(
        "app.services.device_service.ssh_manager.run_command",
        new=AsyncMock(return_value=SSHResponse(True, FAILED_RAW, 0)),
    ):
        result = await get_device_status_by_ip(TEST_IP)

    assert result.online is False
    assert result.state == "FAILED"


async def test_status_not_in_arp_table_is_offline():
    with patch(
        "app.services.device_service.ssh_manager.run_command",
        new=AsyncMock(return_value=SSHResponse(True, EMPTY_RAW, 0)),
    ):
        result = await get_device_status_by_ip(TEST_IP)

    assert result.online is False
    assert result.state is None


@pytest.mark.parametrize(
    "state_raw, ping_status, expected_state, expected_online",
    [
        (STALE_RAW, True, "STALE", True),
        (STALE_RAW, False, "STALE", False),
        (INCOMPLETE_RAW, True, "INCOMPLETE", True),
        (INCOMPLETE_RAW, False, "INCOMPLETE", False),
    ],
)
async def test_online_state_based_on_status_and_ping(state_raw, ping_status, expected_state, expected_online):
    with (
        patch(
            "app.services.device_service.ssh_manager.run_command",
            new=AsyncMock(return_value=SSHResponse(True, state_raw, 0)),
        ),
        patch("app.services.device_service._ping", new=AsyncMock(return_value=ping_status)),
    ):
        result = await get_device_status_by_ip(TEST_IP)

    assert result.online is expected_online
    assert result.state == expected_state


@pytest.mark.parametrize("state", [REACHABLE_RAW, FAILED_RAW])
async def test_ping_not_called_for_(state):
    with (
        patch(
            "app.services.device_service.ssh_manager.run_command",
            new=AsyncMock(return_value=SSHResponse(True, state, 0)),
        ),
        patch("app.services.device_service._ping", new=AsyncMock()) as mock_ping,
    ):
        await get_device_status_by_ip(TEST_IP)

    mock_ping.assert_not_called()


def test_parse_by_mac_finds_correct_entry():
    state, ip = _parse_neigh_output_by_mac(FULL_TABLE_RAW, TEST_MAC)
    assert ip == TEST_IP
    assert state == "REACHABLE"


def test_parse_by_mac_is_case_insensitive():
    state, ip = _parse_neigh_output_by_mac(FULL_TABLE_RAW, TEST_MAC.upper())
    assert ip == TEST_IP


def test_parse_by_mac_returns_none_when_not_found():
    state, ip = _parse_neigh_output_by_mac(FULL_TABLE_RAW, "00:00:00:00:00:00")
    assert ip is None
    assert state is None


@pytest.mark.parametrize("raw", ["", "[]", "not json"])
def test_parse_by_mac_invalid_input(raw):
    from app.services.device_service import _parse_neigh_output_by_mac

    state, ip = _parse_neigh_output_by_mac(raw, TEST_MAC)
    assert ip is None
    assert state is None


async def test_status_by_mac_online():
    with patch(
        "app.services.device_service.ssh_manager.run_command",
        new=AsyncMock(return_value=SSHResponse(True, FULL_TABLE_RAW, 0)),
    ):
        result = await get_device_status_by_mac(TEST_MAC)

    assert result.online is True
    assert result.mac == TEST_MAC
    assert result.ip == TEST_IP
    assert result.state == "REACHABLE"


async def test_status_by_mac_not_in_table_is_offline():
    with patch(
        "app.services.device_service.ssh_manager.run_command",
        new=AsyncMock(return_value=SSHResponse(True, "[]", 0)),
    ):
        result = await get_device_status_by_mac(TEST_MAC)

    assert result.online is False
    assert result.ip is None
    assert result.state is None


async def test_status_by_mac_stale_ping_success():
    with (
        patch(
            "app.services.device_service.ssh_manager.run_command",
            new=AsyncMock(return_value=SSHResponse(True, FULL_TABLE_STALE_RAW, 0)),
        ),
        patch("app.services.device_service._ping", new=AsyncMock(return_value=True)),
    ):
        result = await get_device_status_by_mac(TEST_MAC)

    assert result.online is True
    assert result.state == "STALE"


async def test_status_by_mac_stale_ping_fails():
    with (
        patch(
            "app.services.device_service.ssh_manager.run_command",
            new=AsyncMock(return_value=SSHResponse(True, FULL_TABLE_STALE_RAW, 0)),
        ),
        patch("app.services.device_service._ping", new=AsyncMock(return_value=False)),
    ):
        result = await get_device_status_by_mac(TEST_MAC)

    assert result.online is False


async def test_status_by_mac_stale_no_ip_is_offline():
    no_ip_stale = f'[{{"dev":"br-lan","lladdr":"{TEST_MAC}","state":["STALE"]}}]'

    with patch(
        "app.services.device_service.ssh_manager.run_command",
        new=AsyncMock(return_value=SSHResponse(True, no_ip_stale, 0)),
    ):
        result = await get_device_status_by_mac(TEST_MAC)

    assert result.online is False


async def test_ip_and_mac_cache_are_independent():
    with patch(
        "app.services.device_service.ssh_manager.run_command",
        new=AsyncMock(return_value=SSHResponse(True, FULL_TABLE_RAW, 0)),
    ) as mock_cmd:
        resp1 = await get_device_status_by_ip(TEST_IP)
        resp2 = await get_device_status_by_mac(TEST_MAC)

    assert mock_cmd.call_count == 2
    assert resp1.cached is False
    assert resp2.cached is False
