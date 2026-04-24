from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class MemoryType(Enum):
    KNOWLEDGE = "knowledge"
    PREFERENCE = "preference"
    CONTEXT = "context"
    SKILL = "skill"


@dataclass
class MemoryEntry:
    id: Optional[int] = None
    content: str = ""
    memory_type: MemoryType = MemoryType.CONTEXT
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: int = 5
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_archived: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "metadata": self.metadata,
            "importance": self.importance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_archived": self.is_archived,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        memory_type = MemoryType(data.get("memory_type", "context"))
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get("id"),
            content=data.get("content", ""),
            memory_type=memory_type,
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 5),
            created_at=created_at,
            updated_at=updated_at,
            is_archived=data.get("is_archived", False),
        )
