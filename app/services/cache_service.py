import functools
import logging
import threading
from typing import Callable

from cachetools import TTLCache, keys

from app.config import settings
from app.models.cachable_response import CachableResponse

logger = logging.getLogger(__name__)

_cache = TTLCache(maxsize=256, ttl=settings.cache_ttl_seconds)
_lock = threading.Lock()


def make_key(prefix: str, *args) -> tuple:
    """
    Generate a key used for caching data
    """
    return keys.hashkey(prefix, *args)


def cached(key_prefix: str) -> Callable:
    """
    A decorator for caching async functions. It uses the built-in cachetools mechanism with threading.Lock.

    Important: The function must return a CachableResponse object.

    Usage:
    @cached("device_status")
    async def get_device_status_by_ip(ip: str) -> CachableResponse:
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> CachableResponse:
            key = make_key(key_prefix, *args, *kwargs)
            with _lock:
                cached_value = _cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache HIT key={key}")
                cached_value.cached = True
                return cached_value
            logger.debug(f"Cache MISS key={key}")
            result = await func(*args, **kwargs)
            result.cached = False

            with _lock:
                _cache[key] = result
            return result

        return wrapper

    return decorator


def get_stats() -> dict:
    """
    Returns a dictionary with the statistics of the caching class instance
    """
    with _lock:
        return {
            "cached_keys": len(_cache),
            "maxsize": _cache.maxsize,
            "ttl_seconds": _cache.ttl,
            "currsize": _cache.currsize
        }
