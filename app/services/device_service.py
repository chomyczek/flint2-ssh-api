import json
import logging
from datetime import datetime

from app.models.device import DeviceStatusResponse
from app.services.ssh_manager import ssh_manager

ONLINE_STATES = {"REACHABLE", "DELAY", "PROBE", "PERMANENT", "NOARP"}
STALE_STATES = {"STALE", "INCOMPLETE"}
logger = logging.getLogger(__name__)


async def get_device_status_by_ip(ip: str) -> DeviceStatusResponse:
    """
    Checks if device is online by querying the router's ARP neighbour table.
    If state is in STALE_STATES, falls back to a ping check.
    """
    command = f"ip -json neigh show {ip}"
    logger.debug(f"Running command: {command}")
    online = False

    resp = await ssh_manager.run_command(command)

    state, mac = _parse_neigh_output(resp.output, ip)

    if state in ONLINE_STATES:
        online = True
    elif state in STALE_STATES:
        logger.debug(f"For IP {ip}, state detected: {state}")
        online = await _ping(ip)

    return DeviceStatusResponse(ip=ip, online=online, state=state, mac=mac, checked_at=datetime.now())


async def _ping(ip: str) -> bool:
    """
    Runs a single ping from the router to the target IP and return true if reachable.
    """
    command = f"ping -c 1 -W 1 {ip}"
    logger.debug(f"Running command: {command}")

    result = await ssh_manager.run_command(command)
    reachable = result.exit_code == 0

    logger.debug(f"IP {ip} is reachable: {reachable}")
    return reachable


def _parse_neigh_output(output: str, ip: str) -> tuple[str | None, str | None]:
    """
    Parse the output of an IPv4 neighbor command and return (state, mac) or (None, None) if device not found.
    """
    if not output:
        return None, None
    try:
        entries = json.loads(output)
    except json.JSONDecodeError:
        logger.warning(f"Could not parse output for {ip} as JSON: {output!r}")
        return None, None

    for entry in entries:
        if entry.get("dst") == ip:
            states = entry.get("state", [])
            state = states[0] if states else None
            mac = entry.get("lladdr")
            return state, mac

    return None, None
