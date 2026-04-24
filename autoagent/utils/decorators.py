import time
import functools
import asyncio
from typing import Any, Callable, Optional, TypeVar, Union

from .logger import get_logger

T = TypeVar("T")


def retry(max_attempts: int = 3, backoff: float = 2.0):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = backoff ** attempt
                    time.sleep(wait_time)
            raise RuntimeError("Unexpected exit from retry loop")
        return wrapper
    return decorator


def log_calls(logger=None):
    if logger is None:
        logger = get_logger("log_calls")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        return wrapper
    return decorator


def validate_args(schema):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if schema:
                schema(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def async_timeout(seconds: float):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"{func.__name__} timed out after {seconds} seconds")
        return wrapper
    return decorator
