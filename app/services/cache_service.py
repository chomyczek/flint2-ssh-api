import functools
import logging
import threading
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar, cast

from cachetools import TTLCache, keys

from app.config import settings
from app.models.cachable_response import CachableResponse

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T", bound=CachableResponse)

_cache: TTLCache[tuple[object, ...], CachableResponse] = TTLCache(maxsize=256, ttl=settings.cache_ttl_seconds)
_lock = threading.Lock()


def make_key(prefix: str, *args: object) -> tuple[object, ...]:
    """Generate a key used for caching data.

    Args:
        prefix: Namespace prefix for the cached value.
        *args: Arguments identifying the cache value

    Returns: Hashable cache key.
    """
    return keys.hashkey(prefix, *args)


def cached(key_prefix: str) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """A decorator for caching async functions. It uses the built-in cachetools mechanism with threading.Lock.

    Important: The function must return a CachableResponse object.

    Usage:
    @cached("device_status")
    async def get_device_status_by_ip(ip: str) -> CachableResponse:

    Args:
        key_prefix: Prefix used to namespace cache keys.

    Returns: Decorator for asynchronous functions returning CachableResponse object.
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            key = make_key(key_prefix, *args, *kwargs)
            with _lock:
                cached_value = _cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache HIT key={key}")
                cached_value.cached = True
                return cast(T, cached_value)
            logger.debug(f"Cache MISS key={key}")
            result = await func(*args, **kwargs)
            result.cached = False

            with _lock:
                _cache[key] = result
            return result

        return wrapper

    return decorator


def get_stats() -> dict:
    """Returns a dictionary with the statistics of the caching class instance."""
    with _lock:
        return {
            "cached_keys": len(_cache),
            "maxsize": _cache.maxsize,
            "ttl_seconds": _cache.ttl,
            "currsize": _cache.currsize,
        }
