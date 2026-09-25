import pytest
from fastapi import HTTPException

from app.utils.validators import validate_mac


@pytest.mark.parametrize(
    "mac",
    [
        "aa:bb:cc:dd:ee:ff",
        "AA:BB:CC:DD:EE:FF",
        "00:11:22:33:44:55",
    ],
)
def test_validate_mac_valid(mac):
    result = validate_mac(mac)
    assert result == mac.lower()


def test_validate_mac_lowercases():
    assert validate_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"


@pytest.mark.parametrize(
    "mac",
    [
        "not_a_mac",
        "aa:bb:cc:dd:ee",
        "aa:bb:cc:dd:ee:ff:11",
        "aa-bb-cc-dd-ee-ff",
        "",
    ],
)
def test_validate_mac_invalid(mac):
    with pytest.raises(HTTPException) as exc:
        validate_mac(mac)
    assert exc.value.status_code == 422
