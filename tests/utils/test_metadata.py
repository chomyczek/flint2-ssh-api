from importlib.metadata import PackageNotFoundError
from unittest.mock import MagicMock, patch

from app.utils.metadata import get_app_metadata


def test_get_app_metadata_returns_package_metadata() -> None:
    package_metadata = MagicMock()
    package_metadata.__getitem__.side_effect = {
        "Name": "app-name",
        "Version": "1.2.3",
    }.__getitem__

    with patch(
            "app.utils.metadata.metadata",
            return_value=package_metadata,
    ):
        result = get_app_metadata()

    assert result.name == "app-name"
    assert result.version == "1.2.3"


def test_get_app_metadata_returns_fallback_when_package_is_not_installed() -> None:
    with patch(
            "app.utils.metadata.metadata",
            side_effect=PackageNotFoundError,
    ):
        result = get_app_metadata()

    assert result.name == "FLINT2-SSH-API"
    assert result.version == "unknown"
