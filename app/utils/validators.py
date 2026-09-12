import ipaddress

from fastapi import HTTPException


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
