import asyncio
import uuid
from typing import Any, Dict, List, Optional
import logging

from .subagent import Subagent, SubagentStatus

logger = logging.getLogger(__name__)


class SubagentManager:
    def __init__(self):
        self._subagents: Dict[str, Subagent] = {}
        self._lock = asyncio.Lock()

    async def create_subagent(self, task: str, config: Optional[Dict[str, Any]] = None) -> Subagent:
        async with self._lock:
            subagent_id = str(uuid.uuid4())
            subagent = Subagent(
                subagent_id=subagent_id,
                name=config.get("name", f"subagent_{subagent_id[:8]}") if config else f"subagent_{subagent_id[:8]}",
                config=config or {}
            )
            self._subagents[subagent_id] = subagent
            logger.info(f"Created subagent {subagent_id}")
            return subagent

    async def list_subagents(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return [s.to_dict() for s in self._subagents.values()]

    async def get_subagent(self, subagent_id: str) -> Optional[Subagent]:
        return self._subagents.get(subagent_id)

    async def terminate_subagent(self, subagent_id: str) -> bool:
        async with self._lock:
            subagent = self._subagents.get(subagent_id)
            if not subagent:
                return False
            subagent.terminate()
            del self._subagents[subagent_id]
            logger.info(f"Terminated and removed subagent {subagent_id}")
            return True

    async def terminate_all(self) -> int:
        async with self._lock:
            count = len(self._subagents)
            for subagent in self._subagents.values():
                subagent.terminate()
            self._subagents.clear()
            logger.info(f"Terminated {count} subagents")
            return count

    async def get_active_count(self) -> int:
        async with self._lock:
            return sum(1 for s in self._subagents.values() if s.status == SubagentStatus.RUNNING)

    async def cleanup_terminated(self) -> int:
        async with self._lock:
            terminated = [
                sid for sid, s in self._subagents.items()
                if s.status in (SubagentStatus.TERMINATED, SubagentStatus.COMPLETED, SubagentStatus.FAILED)
            ]
            for sid in terminated:
                del self._subagents[sid]
            if terminated:
                logger.info(f"Cleaned up {len(terminated)} terminated subagents")
            return len(terminated)