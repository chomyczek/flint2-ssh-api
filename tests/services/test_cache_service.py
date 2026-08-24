from unittest.mock import AsyncMock, patch

from app.models.cachable_response import CachableResponse
from app.services.cache_service import make_key, cached, _lock, _cache, get_stats


def test_make_key():
    key = make_key("prefix", "some params", "other params")
    assert isinstance(key, tuple)


def test_make_key_same_args():
    assert make_key("prefix", "param") == make_key("prefix", "param")


def test_make_key_different_prefix():
    assert make_key("prefix1", "param") != make_key("prefix2", "param")


def test_make_key_different_args():
    assert make_key("prefix", "param 1") != make_key("prefix", "param 2")


async def test_cached_on_miss():
    mock_fn = AsyncMock(return_value=CachableResponse())

    @cached("test fn")
    async def fn(param: str):
        return await mock_fn(param)

    result = await fn("some param")

    mock_fn.assert_called_once_with("some param")
    assert result.cached is False


async def test_cached_stores_result_in_cache_after_miss():
    resp = CachableResponse()

    @cached("test")
    async def fn() -> CachableResponse:
        return resp

    with _lock:
        assert len(_cache) == 0

    await fn()

    with _lock:
        assert len(_cache) == 1
        assert _cache[("test",)] is resp


async def test_cached_on_hit():
    mock_fn = AsyncMock(return_value=CachableResponse())

    @cached("test fn")
    async def fn(param: str):
        return await mock_fn(param)

    await fn("some param")
    result = await fn("some param")

    mock_fn.assert_called_once_with("some param")
    assert result.cached is True


async def test_cached_miss_not_mutate_stored():
    call_count = 0

    @cached("test fn")
    async def fn():
        nonlocal call_count
        call_count += 1
        return CachableResponse()

    await fn()
    result = await fn()
    assert result.cached is True

    with _lock:
        _cache.clear()

    result = await fn()
    assert result.cached is False
    assert call_count == 2


async def test_cached_multiple():
    mock_a = AsyncMock(return_value=CachableResponse())
    mock_b = AsyncMock(return_value=CachableResponse())

    @cached("prefix_a")
    async def fn_a():
        return await mock_a()

    @cached("prefix_b")
    async def fn_b():
        return await mock_b()

    await fn_a()
    await fn_b()

    mock_a.assert_called_once()
    mock_b.assert_called_once()

    with _lock:
        assert len(_cache) == 2


async def test_entry_expires_after_ttl():
    from cachetools import TTLCache

    current_time = 1000.0

    def fake_timer():
        return current_time

    short_cache = TTLCache(maxsize=256, ttl=30, timer=fake_timer)

    with patch("app.services.cache_service._cache", short_cache):
        call_count = 0

        @cached("test")
        async def fn():
            nonlocal call_count
            call_count += 1
            return CachableResponse()

        await fn()
        assert call_count == 1

        # fake_timer increase
        current_time += 31

        await fn()
        assert call_count == 2


def test_get_stats():
    stats = get_stats()
    assert isinstance(stats, dict)
    assert stats["cached_keys"] == 0
    assert stats["currsize"] == 0
    assert stats["maxsize"] > 0
    assert stats["ttl_seconds"] > 0
