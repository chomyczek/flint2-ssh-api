import ipaddress

from fastapi import HTTPException


def validate_ip(ip: str) -> str:
    try:
        ipaddress.IPv4Address(ip)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"'{ip}' is not a valid IPv4 address")
    return ip