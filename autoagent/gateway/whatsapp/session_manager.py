import time
from typing import Dict, Optional, Any
from collections import defaultdict

from ..utils.logger import get_logger

logger = get_logger("whatsapp_session")


class WhatsAppSession:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
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
        logger.debug(f"Cleared session history for {self.phone_number}")

    def update_context(self, key: str, value: Any) -> None:
        self.context[key] = value
        self.last_activity = time.time()


class WhatsAppSessionManager:
    def __init__(self):
        self._sessions: Dict[str, WhatsAppSession] = {}
        self._session_timeout = 3600

    def get_or_create_session(self, phone_number: str) -> WhatsAppSession:
        if phone_number not in self._sessions:
            self._sessions[phone_number] = WhatsAppSession(phone_number)
            logger.debug(f"Created new session for {phone_number}")

        return self._sessions[phone_number]

    def get_session(self, phone_number: str) -> Optional[WhatsAppSession]:
        return self._sessions.get(phone_number)

    def get_all_sessions(self) -> list[WhatsAppSession]:
        return list(self._sessions.values())

    def cleanup_expired_sessions(self) -> int:
        current_time = time.time()
        expired_numbers = [
            phone_number
            for phone_number, session in self._sessions.items()
            if current_time - session.last_activity > self._session_timeout
        ]

        for phone_number in expired_numbers:
            del self._sessions[phone_number]

        if expired_numbers:
            logger.info(f"Cleaned up {len(expired_numbers)} expired sessions")

        return len(expired_numbers)

    def clear_session(self, phone_number: str) -> bool:
        if phone_number in self._sessions:
            self._sessions[phone_number].clear_history()
            return True
        return False

    def delete_session(self, phone_number: str) -> bool:
        if phone_number in self._sessions:
            del self._sessions[phone_number]
            return True
        return False
