from typing import Dict, List, Optional, Any
from datetime import datetime
from .nudge_types import Nudge, NudgeType, NudgePriority
from .trigger_manager import TriggerManager
import uuid


class NudgeEngine:
    def __init__(self, memory_manager=None, skill_manager=None):
        self.memory_manager = memory_manager
        self.skill_manager = skill_manager
        self.trigger_manager = TriggerManager()
        self._nudge_queue: List[Nudge] = []
        self._nudge_history: List[Nudge] = []
        self._pending_skill_suggestions: List[Dict] = []
        self._init_triggers()

    def _init_triggers(self):
        pass

    async def check_and_generate_nudges(self) -> List[Nudge]:
        triggered_ids = self.trigger_manager.check_time_triggers()
        new_nudges = []

        for trigger_id in triggered_ids:
            pass

        return new_nudges

    def add_nudge(self, nudge: Nudge):
        self._nudge_queue.append(nudge)

    def get_pending_nudges(self) -> List[Nudge]:
        pending = [
            n for n in self._nudge_queue
            if not n.shown and not n.dismissed
        ]
        return sorted(pending, key=lambda x: x.priority.value, reverse=True)

    def dismiss_nudge(self, nudge_id: str):
        for nudge in self._nudge_queue:
            if nudge.id == nudge_id:
                nudge.dismissed = True
                self._nudge_history.append(nudge)
                break

    def mark_nudge_shown(self, nudge_id: str):
        for nudge in self._nudge_queue:
            if nudge.id == nudge_id:
                nudge.shown = True
                break

    def generate_skill_suggestion(
        self, task_description: str, confidence: float
    ) -> Optional[Nudge]:
        if not self.skill_manager or confidence < 0.6:
            return None

        nudge_id = str(uuid.uuid4())
        return Nudge(
            id=nudge_id,
            type=NudgeType.SKILL_SUGGESTION,
            title="技能建议",
            content=f"根据您的任务 '{task_description}'，建议使用相关技能来提高效率",
            priority=NudgePriority.MEDIUM if confidence < 0.8 else NudgePriority.HIGH,
            created_at=datetime.now().isoformat(),
            trigger_condition={"task": task_description, "confidence": confidence},
            metadata={"suggestion_type": "skill", "confidence": confidence}
        )

    def generate_memory_nudge(
        self, related_topic: str, memory_content: str
    ) -> Optional[Nudge]:
        if not self.memory_manager:
            return None

        nudge_id = str(uuid.uuid4())
        return Nudge(
            id=nudge_id,
            type=NudgeType.MEMORY_BASED,
            title=f"关于 '{related_topic}' 的记忆",
            content=memory_content[:200] + "..." if len(memory_content) > 200 else memory_content,
            priority=NudgePriority.LOW,
            created_at=datetime.now().isoformat(),
            trigger_condition={"topic": related_topic},
            metadata={"memory_topic": related_topic}
        )

    def generate_time_nudge(
        self, title: str, content: str, priority: NudgePriority
    ) -> Nudge:
        nudge_id = str(uuid.uuid4())
        return Nudge(
            id=nudge_id,
            type=NudgeType.TIME_BASED,
            title=title,
            content=content,
            priority=priority,
            created_at=datetime.now().isoformat(),
            trigger_condition={"type": "scheduled"},
            metadata={}
        )

    def generate_behavior_nudge(
        self, title: str, content: str, behavior_type: str
    ) -> Nudge:
        nudge_id = str(uuid.uuid4())
        return Nudge(
            id=nudge_id,
            type=NudgeType.BEHAVIOR_BASED,
            title=title,
            content=content,
            priority=NudgePriority.MEDIUM,
            created_at=datetime.now().isoformat(),
            trigger_condition={"behavior_type": behavior_type},
            metadata={"behavior_type": behavior_type}
        )

    def generate_event_nudge(
        self, title: str, content: str, event_name: str
    ) -> Nudge:
        nudge_id = str(uuid.uuid4())
        return Nudge(
            id=nudge_id,
            type=NudgeType.EVENT_BASED,
            title=title,
            content=content,
            priority=NudgePriority.HIGH,
            created_at=datetime.now().isoformat(),
            trigger_condition={"event_name": event_name},
            metadata={"event_name": event_name}
        )

    def get_nudge_stats(self) -> Dict[str, Any]:
        total = len(self._nudge_history) + len(self._nudge_queue)
        shown = sum(1 for n in self._nudge_history if n.shown)
        dismissed = sum(1 for n in self._nudge_history if n.dismissed)
        pending = len(self.get_pending_nudges())

        return {
            "total_nudges": total,
            "shown": shown,
            "dismissed": dismissed,
            "pending": pending,
            "by_type": {
                nt.value: sum(1 for n in self._nudge_history if n.type == nt)
                for nt in NudgeType
            },
            "by_priority": {
                np.name: sum(1 for n in self._nudge_history if n.priority == np)
                for np in NudgePriority
            }
        }