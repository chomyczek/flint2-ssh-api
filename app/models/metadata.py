from dataclasses import dataclass


@dataclass
class Metadata:
    """Object for storing application metadata."""

    name: str
    version: str
