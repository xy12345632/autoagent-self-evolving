from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class NudgeType(Enum):
    TIME_BASED = "time_based"
    BEHAVIOR_BASED = "behavior"
    EVENT_BASED = "event"
    MEMORY_BASED = "memory"
    SKILL_SUGGESTION = "skill"


class NudgePriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Nudge:
    id: str
    type: NudgeType
    title: str
    content: str
    priority: NudgePriority
    created_at: str
    trigger_condition: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    shown: bool = False
    dismissed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "content": self.content,
            "priority": self.priority.name,
            "created_at": self.created_at,
            "trigger_condition": self.trigger_condition,
            "metadata": self.metadata,
            "shown": self.shown,
            "dismissed": self.dismissed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Nudge":
        return cls(
            id=data["id"],
            type=NudgeType(data["type"]),
            title=data["title"],
            content=data["content"],
            priority=NudgePriority[data["priority"]],
            created_at=data["created_at"],
            trigger_condition=data["trigger_condition"],
            metadata=data.get("metadata", {}),
            shown=data.get("shown", False),
            dismissed=data.get("dismissed", False),
        )