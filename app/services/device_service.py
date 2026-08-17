import json
import logging
from datetime import datetime

from app.models.device import DeviceStatusResponse
from app.services.ssh_manager import ssh_manager

ONLINE_STATES = {"REACHABLE", "DELAY", "PROBE", "PERMANENT", "NOARP"}
logger = logging.getLogger(__name__)


async def get_device_status_by_ip(ip: str) -> DeviceStatusResponse:
    """
    Runs `ip neigh show <ip>` SSH command and returns `DeviceStatusResponse`
    """
    command = f"ip -json neigh show {ip}"
    logger.debug(f"Running command: {command}")

    resp = await ssh_manager.run_command(command)

    state, mac = _parse_neigh_output(resp.output, ip)
    online = state in ONLINE_STATES if state else False

    return DeviceStatusResponse(ip=ip, online=online, state=state, mac=mac, checked_at=datetime.now())


def _parse_neigh_output(output: str, ip: str) -> tuple[str | None, str | None]:
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
