from fastapi import APIRouter

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/status")
async def get_device_status():
    return {
        "message": "Device status endpoint — SSH not connected yet",
        "status": "not_implemented",
    }
