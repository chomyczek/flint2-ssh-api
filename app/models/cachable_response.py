from pydantic import BaseModel


class CachableResponse(BaseModel):
    """Base response model supporting cache metadata."""

    cached: bool = False
