from typing import Dict, List, Callable, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import time


class TriggerManager:
    def __init__(self):
        self._time_triggers: List[Dict] = []
        self._behavior_patterns: deque = deque(maxlen=100)
        self._event_listeners: Dict[str, List[Callable]] = {}
        self._last_check: Optional[datetime] = None

    def add_time_trigger(self, trigger_id: str, callback: Callable, interval_seconds: int):
        self._time_triggers.append({
            "id": trigger_id,
            "callback": callback,
            "interval_seconds": interval_seconds,
            "last_triggered": None,
            "next_trigger": datetime.now() + timedelta(seconds=interval_seconds)
        })

    def check_time_triggers(self) -> List[str]:
        triggered_ids = []
        current_time = datetime.now()

        for trigger in self._time_triggers:
            if current_time >= trigger["next_trigger"]:
                triggered_ids.append(trigger["id"])
                trigger["last_triggered"] = current_time
                trigger["next_trigger"] = current_time + timedelta(
                    seconds=trigger["interval_seconds"]
                )

        self._last_check = current_time
        return triggered_ids

    def record_behavior(self, behavior_type: str, data: Dict[str, Any]):
        self._behavior_patterns.append({
            "type": behavior_type,
            "data": data,
            "timestamp": datetime.now()
        })

    def detect_pattern(self, pattern: List[str]) -> bool:
        if len(self._behavior_patterns) < len(pattern):
            return False

        pattern_types = [p if isinstance(p, str) else p.get("type") for p in pattern]
        recent_types = [
            b["type"] for b in list(self._behavior_patterns)[-len(pattern):]
        ]

        return recent_types == pattern_types

    def register_event(self, event_name: str, callback: Callable):
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = []
        self._event_listeners[event_name].append(callback)

    def trigger_event(self, event_name: str, data: Dict[str, Any]):
        if event_name in self._event_listeners:
            for callback in self._event_listeners[event_name]:
                callback(data)

    def get_behavior_history(self, limit: int = 50) -> List[Dict]:
        return list(self._behavior_patterns)[-limit:]

    def clear_behavior_history(self):
        self._behavior_patterns.clear()