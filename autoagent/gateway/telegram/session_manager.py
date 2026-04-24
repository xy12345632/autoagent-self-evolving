import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from ..utils.logger import get_logger

logger = get_logger("session_manager")

SESSION_TIMEOUT = 3600


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class UserSession:
    user_id: int
    platform: str = "telegram"
    messages: list[Message] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        self.last_active = time.time()

    def is_expired(self, timeout: int = SESSION_TIMEOUT) -> bool:
        return (time.time() - self.last_active) > timeout

    def get_conversation_history(self, limit: int = 10) -> list[dict[str, str]]:
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [{"role": m.role, "content": m.content} for m in recent]


class SessionManager:
    def __init__(self, session_timeout: int = SESSION_TIMEOUT):
        self._sessions: dict[int, UserSession] = {}
        self._timeout = session_timeout
        self._cleanup_task: Optional[asyncio.Task] = None
        self._platform_sessions: dict[str, dict[int, int]] = {}

    def create_session(self, user_id: int, platform: str = "telegram", **kwargs) -> UserSession:
        session = UserSession(
            user_id=user_id,
            platform=platform,
            metadata=kwargs
        )
        self._sessions[user_id] = session

        if platform not in self._platform_sessions:
            self._platform_sessions[platform] = {}
        self._platform_sessions[platform][user_id] = user_id

        logger.debug(f"创建会话: user_id={user_id}, platform={platform}")
        return session

    def get_session(self, user_id: int) -> Optional[UserSession]:
        session = self._sessions.get(user_id)
        if session and session.is_expired(self._timeout):
            self.clear_session(user_id)
            return None
        return session

    def clear_session(self, user_id: int) -> None:
        if user_id in self._sessions:
            session = self._sessions[user_id]
            platform = session.platform
            del self._sessions[user_id]

            if platform in self._platform_sessions:
                self._platform_sessions[platform].pop(user_id, None)

            logger.debug(f"清除会话: user_id={user_id}")

    def update_context(self, user_id: int, key: str, value: Any) -> None:
        session = self.get_session(user_id)
        if session:
            session.context[key] = value
            session.last_active = time.time()

    def get_context(self, user_id: int, key: str) -> Optional[Any]:
        session = self.get_session(user_id)
        return session.context.get(key) if session else None

    def get_user_platform(self, user_id: int) -> Optional[str]:
        session = self.get_session(user_id)
        return session.platform if session else None

    def get_cross_platform_context(
        self, user_id: int, current_platform: str
    ) -> dict[str, Any]:
        context = {"current_platform": current_platform}
        session = self.get_session(user_id)
        if session:
            context.update(session.context)
        return context

    async def start_cleanup_task(self) -> None:
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            logger.info("会话清理任务已启动")

    async def stop_cleanup_task(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("会话清理任务已停止")

    async def _cleanup_expired_sessions(self) -> None:
        while True:
            try:
                await asyncio.sleep(300)
                expired_users = [
                    user_id for user_id, session in self._sessions.items()
                    if session.is_expired(self._timeout)
                ]
                for user_id in expired_users:
                    self.clear_session(user_id)
                    logger.debug(f"清理过期会话: user_id={user_id}")
            except asyncio.CancelledError:
                break

    def get_all_sessions(self) -> dict[int, UserSession]:
        return self._sessions.copy()

    def get_session_count(self) -> int:
        return len(self._sessions)
