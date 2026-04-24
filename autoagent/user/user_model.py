from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class UserPreference:
    response_style: str = "balanced"
    communication_tone: str = "friendly"
    preferred_language: str = "zh"
    notification_preference: str = "smart"
    interaction_time_preference: Dict[str, List[int]] = field(default_factory=dict)


@dataclass
class UserBehavior:
    common_tasks: List[str] = field(default_factory=list)
    tool_usage_history: Dict[str, int] = field(default_factory=dict)
    conversation_topics: List[str] = field(default_factory=list)
    peak_interaction_hours: List[int] = field(default_factory=list)
    avg_session_length: float = 0.0
    total_interactions: int = 0


@dataclass
class UserModel:
    user_id: str
    created_at: str
    updated_at: str
    preferences: UserPreference
    behaviors: UserBehavior
    personality_traits: Dict[str, float] = field(default_factory=dict)
    learning_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
