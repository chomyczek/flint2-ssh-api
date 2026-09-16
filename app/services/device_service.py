import json
import logging
from datetime import datetime

from app.models.device import DeviceStatusResponse
from app.models.neigh_entry import NeighEntry
from app.services.cache_service import cached
from app.services.ssh_manager import ssh_manager

ONLINE_STATES = {"REACHABLE", "DELAY", "PROBE", "PERMANENT", "NOARP"}
STALE_STATES = {"STALE", "INCOMPLETE"}
logger = logging.getLogger(__name__)


@cached("device_status_ip")
async def get_device_status_by_ip(ip: str) -> DeviceStatusResponse:
    """Checks if device is online by querying the router's ARP neighbour table.

    If state is in STALE_STATES, falls back to a ping check.

    Args:
        ip: IPv4 address of the device to check.

    Returns: Device connectivity status.
    """
    command = f"ip -json neigh show {ip}"
    logger.debug(f"Running command: {command}")

    resp = await ssh_manager.run_command(command)

    state, mac = _parse_neigh_output_by_ip(resp.output, ip)
    online = await _resolve_online_state(state, ip)

    return DeviceStatusResponse(ip=ip, online=online, state=state, mac=mac, checked_at=datetime.now())


@cached("device_status_mac")
async def get_device_status_by_mac(mac: str) -> DeviceStatusResponse:
    """Checks if device is online by querying the router's ARP neighbour table using MAC address.

    If state is in STALE_STATES, falls back to a ping check.

    Args:
        mac: MAC address of the device to check.

    Returns: Device connectivity status.
    """
    command = "ip -json neigh show"
    logger.debug(f"Running command: {command}")

    resp = await ssh_manager.run_command(command)

    state, ip = _parse_neigh_output_by_mac(resp.output, mac)
    online = await _resolve_online_state(state, ip)

    return DeviceStatusResponse(ip=ip, online=online, state=state, mac=mac, checked_at=datetime.now())


async def _resolve_online_state(state: str | None, ip: str | None) -> bool:
    """Resolve whether a device is online based on ARP state, with ping fallback for uncertain states.

    Args:
        state: ARP neighbour state string.
        ip: IPv4 address used for ping fallback when state is uncertain.

    Returns: True if device is considered online, False otherwise.
    """
    if state in ONLINE_STATES:
        return True
    elif state in STALE_STATES:
        if ip is None:
            logger.debug(f"State is {state} but IP is unknown - cannot ping, treating as offline")
            return False
        logger.debug(f"For IP {ip}, state detected: {state}")
        return await _ping(ip)
    return False


async def _ping(ip: str) -> bool:
    """Runs a single ping from the router to the target IP and return true if reachable."""
    command = f"ping -c 1 -W 1 {ip}"
    logger.debug(f"Running command: {command}")

    result = await ssh_manager.run_command(command)
    reachable = result.exit_code == 0

    logger.debug(f"IP {ip} is reachable: {reachable}")
    return reachable


def _parse_neigh_json(output: str) -> list[NeighEntry]:
    """Parse raw json output from ip neigh command into list of entries.

    Args:
        output: raw json output from ip neigh command.

    Returns:
        List of parsed ARP entries, empty list on failure.
    """
    if not output:
        return []
    try:
        return json.loads(output)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        logger.warning(f"Could not parse neigh output as JSON: {output!r}")
        return []


def _parse_neigh_output_by_mac(output: str, mac: str) -> tuple[str | None, str | None]:
    """Parse ARP neighbour output and find entry matching the given MAC.

    Args:
        output: Raw JSON output from ip neigh command.
        mac: MAC address to look up.

    Returns: Tuple of (state,ip) or (None, None) if not found.
    """
    entries = _parse_neigh_json(output)
    for entry in entries:
        if entry.get("lladdr", "").lower() == mac.lower():
            state, _ = _extract_state_and_mac(entry)
            ip = entry.get("dst")
            return state, ip
    return None, None


def _parse_neigh_output_by_ip(output: str, ip: str) -> tuple[str | None, str | None]:
    """Parse the output of an IPv4 neighbor command and return (state, mac) or (None, None) if device not found."""
    entries = _parse_neigh_json(output)
    for entry in entries:
        if entry.get("dst") == ip:
            states = entry.get("state", [])
            state = states[0] if states else None
            mac = entry.get("lladdr")
            return state, mac

    return None, None


def _extract_state_and_mac(entry: NeighEntry) -> tuple[str | None, str | None]:
    """Extract state and mac address from a single ARP entry.

    Args:
        entry: Single ARP entry dictionary

    Returns: Tuple of (state, mac)
    """
    states = entry.get("state", [])
    state = states[0] if states else None
    mac = entry.get("lladdr")
    return state, mac
