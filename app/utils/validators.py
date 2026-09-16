import ipaddress
import re

from fastapi import HTTPException

_MAC_PATTERN = re.compile(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


def validate_ip(ip: str) -> str:
    """Validate that a value is a valid IPv4 address.

    Args:
        ip: Value to validate.

    Returns: Valid IPv4 address.
    """
    try:
        ipaddress.IPv4Address(ip)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"'{ip}' is not a valid IPv4 address") from e
    return ip


def validate_mac(mac: str) -> str:
    """Validate that a value is a valid MAC address in format aa:bb:cc:dd:ee:ff.

    Args:
        mac: Value to validate.

    Returns: Valid lowercased MAC address.
    """
    if not _MAC_PATTERN.match(mac):
        raise HTTPException(
            status_code=422, detail=f"'{mac}' is not a valid MAC address. Expected format: aa:bb:cc:dd:ee:ff"
        )
    return mac.lower()
