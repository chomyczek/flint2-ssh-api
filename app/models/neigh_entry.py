from typing import TypedDict


class NeighEntry(TypedDict, total=False):
    """Neighbor entry clas for ip neigh command output entries."""

    dst: str
    dev: str
    lladdr: str
    state: list[str]
