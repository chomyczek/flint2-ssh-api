import pytest

from app.services.cache_service import _lock, _cache

TEST_IP = "203.0.113.42"
TEST_MAC = "aa:bb:cc:dd:ee:ff"


@pytest.fixture(autouse=True)
def clear_cache():
    with _lock:
        _cache.clear()
    yield
    with _lock:
        _cache.clear()
