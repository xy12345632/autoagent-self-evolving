import time
from typing import Dict, Optional, Any
from collections import defaultdict

from ..utils.logger import get_logger

logger = get_logger("slack_session")


class SlackSession:
    def __init__(self, workspace: str, user: str, channel_id: str):
        self.workspace = workspace
        self.user = user
        self.channel_id = channel_id
        self.messages: list[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.created_at = time.time()
        self.last_activity = time.time()

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time(),
        })
        self.last_activity = time.time()

    def get_conversation_history(self, limit: int = 50) -> list[Dict[str, Any]]:
        return self.messages[-limit:]

    def clear_history(self) -> None:
        self.messages.clear()
        logger.debug(f"Cleared session history for {self.user} in {self.channel_id}")


class SlackSessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, SlackSession]] = defaultdict(dict)
        self._session_timeout = 3600

    def _get_session_key(self, workspace: str, user: str, channel_id: str) -> str:
        return f"{workspace}:{channel_id}:{user}"

    def get_or_create_session(
        self, workspace: str, user: str, channel_id: str
    ) -> SlackSession:
        key = self._get_session_key(workspace, user, channel_id)

        if key not in self._sessions[workspace][user]:
            self._sessions[workspace][user][channel_id] = SlackSession(
                workspace, user, channel_id
            )
            logger.debug(f"Created new session for {user} in {channel_id}")

        return self._sessions[workspace][user][channel_id]

    def get_session(self, workspace: str, user: str, channel_id: str) -> Optional[SlackSession]:
        key = self._get_session_key(workspace, user, channel_id)
        return self._sessions.get(workspace, {}).get(user, {}).get(channel_id)

    def get_user_sessions(self, workspace: str, user: str) -> list[SlackSession]:
        return list(self._sessions.get(workspace, {}).get(user, {}).values())

    def cleanup_expired_sessions(self) -> int:
        current_time = time.time()
        removed = 0

        for workspace in self._sessions:
            for user in self._sessions[workspace]:
                expired_channels = [
                    channel_id
                    for channel_id, session in self._sessions[workspace][user].items()
                    if current_time - session.last_activity > self._session_timeout
                ]
                for channel_id in expired_channels:
                    del self._sessions[workspace][user][channel_id]
                    removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} expired sessions")

        return removed

    def clear_user_sessions(self, workspace: str, user: str) -> int:
        count = len(self._sessions.get(workspace, {}).get(user, {}))
        if workspace in self._sessions and user in self._sessions[workspace]:
            self._sessions[workspace][user].clear()
        return count
