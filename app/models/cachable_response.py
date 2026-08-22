from pydantic import BaseModel


class CachableResponse(BaseModel):
    cached: bool = False