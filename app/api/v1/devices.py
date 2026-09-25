from ipaddress import IPv4Address
from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Query

from app.models.device import DeviceStatusResponse
from app.services.device_service import get_device_status_by_ip, get_device_status_by_mac
from app.utils.validators import validate_mac

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/status/ip", response_model=DeviceStatusResponse)
async def get_status_by_ip(
    ip: Annotated[IPv4Address, Query(description="IPv4 address of the device to check")],
) -> DeviceStatusResponse:
    """Return the connectivity status for a device identified by IP address.

    Args:
        ip: IPv4 address of the device to check.

    Returns: Current device connectivity status.
    """
    return await get_device_status_by_ip(str(ip))


@router.get("/status/mac", response_model=DeviceStatusResponse)
async def get_status_by_mac(
    mac: Annotated[str, Query(description="MAC address of the device to check")],
) -> DeviceStatusResponse:
    """Return the connectivity status for a device identified by MAC address.

    Args:
        mac: MAC address of the device to check.

    Returns: Current device connectivity status.
    """
    validate_mac(mac)
    return await get_device_status_by_mac(mac)
