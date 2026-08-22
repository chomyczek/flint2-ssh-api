from datetime import datetime

from pydantic import BaseModel


class DeviceStatusResponse(BaseModel):
    ip: str
    online: bool
    state: str| None
    mac: str | None
    checked_at: datetime
