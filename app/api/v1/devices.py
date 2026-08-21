from fastapi import APIRouter
from fastapi.params import Query

from app.models.device import DeviceStatusResponse
from app.services.device_service import get_device_status_by_ip
from app.utils.validators import validate_ip

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/status", response_model=DeviceStatusResponse)
async def get_status(ip:str = Query(description="IPv4 address of the device to check")):
    validate_ip(ip)
    return await get_device_status_by_ip(ip)
