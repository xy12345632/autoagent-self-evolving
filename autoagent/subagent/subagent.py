import asyncio
import uuid
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class SubagentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class Subagent:
    subagent_id: str
    name: str
    config: Dict[str, Any]
    status: SubagentStatus = SubagentStatus.IDLE
    result: Optional[Any] = None
    error: Optional[str] = None
    _task: Optional[asyncio.Task] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.subagent_id:
            self.subagent_id = str(uuid.uuid4())

    async def run(self, task: str) -> Dict[str, Any]:
        self.status = SubagentStatus.RUNNING
        logger.info(f"Subagent {self.subagent_id} started task: {task[:50]}...")

        try:
            await asyncio.sleep(0.1)

            self.result = {"status": "success", "task": task, "output": f"Processed: {task}"}
            self.status = SubagentStatus.COMPLETED
            logger.info(f"Subagent {self.subagent_id} completed task")
            return self.result

        except Exception as e:
            self.error = str(e)
            self.status = SubagentStatus.FAILED
            logger.error(f"Subagent {self.subagent_id} failed: {e}")
            return {"status": "error", "error": self.error}

    def get_result(self) -> Optional[Dict[str, Any]]:
        if self.status == SubagentStatus.COMPLETED:
            return self.result
        elif self.status == SubagentStatus.FAILED:
            return {"status": "error", "error": self.error}
        return None

    def get_status(self) -> SubagentStatus:
        return self.status

    def terminate(self):
        if self._task and not self._task.done():
            self._task.cancel()
        self.status = SubagentStatus.TERMINATED
        logger.info(f"Subagent {self.subagent_id} terminated")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subagent_id": self.subagent_id,
            "name": self.name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "config": self.config
        }