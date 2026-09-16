from datetime import datetime

from app.models.cachable_response import CachableResponse


class DeviceStatusResponse(CachableResponse):
    """Connectivity status returned for a network device."""

    ip: str | None
    online: bool
    state: str | None
    mac: str | None
    checked_at: datetime
