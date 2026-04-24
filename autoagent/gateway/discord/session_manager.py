from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import uuid

from ..utils.logger import get_logger

logger = get_logger("discord_session")


@dataclass
class DiscordSession:
    session_id: str
    guild_id: Optional[int]
    channel_id: int
    user_id: int
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: dict[str, Any]) -> None:
        self.messages.append({
            **message,
            "timestamp": datetime.now().isoformat(),
        })
        self.last_activity = datetime.now()

    def get_context(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "user_id": self.user_id,
            "platform": "discord",
            "history": self.messages,
            "metadata": self.metadata,
        }

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.messages[-limit:]

    def clear(self) -> None:
        self.messages.clear()
        self.last_activity = datetime.now()
        logger.debug(f"Session {self.session_id} cleared")

    def is_expired(self, ttl_minutes: int = 60) -> bool:
        delta = datetime.now() - self.last_activity
        return delta.total_seconds() > (ttl_minutes * 60)


class DiscordSessionManager:
    def __init__(self, max_sessions: int = 1000):
        self._sessions: dict[str, DiscordSession] = {}
        self._user_sessions: dict[int, list[str]] = {}
        self._channel_sessions: dict[int, list[str]] = {}
        self._max_sessions = max_sessions
        self._default_ttl = 60

    def _generate_session_id(self) -> str:
        return f"discord_{uuid.uuid4().hex[:12]}"

    def _get_channel_key(self, guild_id: Optional[int], channel_id: int) -> tuple:
        return (guild_id, channel_id)

    def get_or_create_session(
        self,
        guild_id: Optional[int],
        channel_id: int,
        user_id: int,
    ) -> DiscordSession:
        channel_key = self._get_channel_key(guild_id, channel_id)

        existing = self._find_session(channel_key, user_id)
        if existing and not existing.is_expired(self._default_ttl):
            return existing

        if len(self._sessions) >= self._max_sessions:
            self._cleanup_expired()

        session = DiscordSession(
            session_id=self._generate_session_id(),
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
        )

        self._sessions[session.session_id] = session

        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session.session_id)

        if channel_key not in self._channel_sessions:
            self._channel_sessions[channel_key] = []
        self._channel_sessions[channel_key].append(session.session_id)

        logger.debug(f"Created new session: {session.session_id} for user {user_id}")
        return session

    def _find_session(self, channel_key: tuple, user_id: int) -> Optional[DiscordSession]:
        session_ids = self._channel_sessions.get(channel_key, [])
        for sid in session_ids:
            session = self._sessions.get(sid)
            if session and session.user_id == user_id and not session.is_expired(self._default_ttl):
                return session
        return None

    def find_session_by_message_id(self, message_id: int) -> Optional[DiscordSession]:
        for session in self._sessions.values():
            for msg in session.messages:
                if msg.get("message_id") == message_id:
                    return session
        return None

    def get_user_sessions(self, user_id: int) -> list[DiscordSession]:
        session_ids = self._user_sessions.get(user_id, [])
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def get_channel_sessions(
        self,
        guild_id: Optional[int],
        channel_id: int,
    ) -> list[DiscordSession]:
        channel_key = self._get_channel_key(guild_id, channel_id)
        session_ids = self._channel_sessions.get(channel_key, [])
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def delete_session(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if not session:
            return False

        if session.user_id in self._user_sessions:
            self._user_sessions[session.user_id].remove(session_id)

        channel_key = self._get_channel_key(session.guild_id, session.channel_id)
        if channel_key in self._channel_sessions:
            self._channel_sessions[channel_key].remove(session_id)

        logger.debug(f"Deleted session: {session_id}")
        return True

    def _cleanup_expired(self) -> int:
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired(self._default_ttl)
        ]

        for sid in expired:
            self.delete_session(sid)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    def cleanup_inactive(self, channel_id: int, guild_id: Optional[int] = None) -> int:
        channel_key = self._get_channel_key(guild_id, channel_id)
        session_ids = list(self._channel_sessions.get(channel_key, []))

        deleted = 0
        for sid in session_ids:
            session = self._sessions.get(sid)
            if session and len(session.messages) == 0:
                self.delete_session(sid)
                deleted += 1

        return deleted

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_sessions": len(self._sessions),
            "active_users": len(self._user_sessions),
            "active_channels": len(self._channel_sessions),
            "expired_count": sum(
                1 for s in self._sessions.values() if s.is_expired(self._default_ttl)
            ),
        }
