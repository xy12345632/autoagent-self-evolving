import time
import functools
from typing import Optional, Type, Callable, Any, TypeVar

from .logger import get_logger

T = TypeVar("T")


class AutoAgentError(Exception):
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class APIError(AutoAgentError):
    def __init__(self, message: str, code: Optional[str] = None, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message, code)


class MemoryError(AutoAgentError):
    pass


class SkillError(AutoAgentError):
    pass


class ToolError(AutoAgentError):
    pass


class GatewayError(AutoAgentError):
    pass


def handle_error(error: Exception, logger: Optional[Any] = None) -> AutoAgentError:
    if logger is None:
        logger = get_logger("error_handler")

    if isinstance(error, AutoAgentError):
        logger.error(f"[{error.code}] {error.message}")
        return error

    logger.error(f"Unknown error: {str(error)}")
    return AutoAgentError(str(error), code="UNKNOWN_ERROR")


def retry_with_backoff(
    max_attempts: int = 3,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = backoff ** attempt
                    time.sleep(wait_time)
            raise RuntimeError("Unexpected exit from retry loop")
        return wrapper
    return decorator


def error_to_user_message(error: Exception) -> str:
    if isinstance(error, APIError):
        if error.status_code == 401:
            return "认证失败，请检查API密钥是否正确"
        elif error.status_code == 429:
            return "请求过于频繁，请稍后重试"
        elif error.status_code >= 500:
            return "服务器内部错误，请稍后重试"
        return f"API调用失败：{error.message}"

    if isinstance(error, MemoryError):
        return f"记忆系统错误：{error.message}"

    if isinstance(error, SkillError):
        return f"技能执行失败：{error.message}"

    if isinstance(error, ToolError):
        return f"工具执行失败：{error.message}"

    if isinstance(error, GatewayError):
        return f"网关错误：{error.message}"

    return f"发生未知错误：{str(error)}"
