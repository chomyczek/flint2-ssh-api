from datetime import datetime

from app.models.cachable_response import CachableResponse


class DeviceStatusResponse(CachableResponse):
    ip: str
    online: bool
    state: str | None
    mac: str | None
    checked_at: datetime
