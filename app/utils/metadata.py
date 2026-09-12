from importlib.metadata import PackageNotFoundError, metadata

from app.models.metadata import Metadata

_PACKAGE_NAME = "FLINT2-SSH-API"


def get_app_metadata() -> Metadata:
    """Read application name and version from installed package metadata.

    Returns:
        Metadata object with values read from pyproject.toml.
    """
    try:
        meta = metadata(_PACKAGE_NAME)
        return Metadata(name=meta["Name"], version=meta["Version"])
    except PackageNotFoundError:
        return Metadata(name=_PACKAGE_NAME, version="unknown")
