from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
from .user_model import UserModel, UserBehavior


class BehaviorTracker:
    def __init__(self, user_model: UserModel):
        self.user_model = user_model
        self._recent_behaviors: deque = deque(maxlen=50)
        self._tool_sequences: deque = deque(maxlen=100)
        self._current_sequence: List[str] = []

    def record_interaction(self, interaction_type: str, data: Dict[str, Any]):
        self._recent_behaviors.append({
            'type': interaction_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })

        self.user_model.behaviors.total_interactions += 1

        if 'topic' in data:
            topics = self.user_model.behaviors.conversation_topics
            topic = data['topic']
            if topic not in topics:
                topics.append(topic)

        if 'session_length' in data:
            current_avg = self.user_model.behaviors.avg_session_length
            total = self.user_model.behaviors.total_interactions
            new_length = data['session_length']
            self.user_model.behaviors.avg_session_length = (
                (current_avg * (total - 1) + new_length) / total
            )

        self.user_model.updated_at = datetime.now().isoformat()

    def record_tool_usage(self, tool_name: str, context: Dict[str, Any]):
        self._current_sequence.append(tool_name)

        history = self.user_model.behaviors.tool_usage_history
        history[tool_name] = history.get(tool_name, 0) + 1

        self.user_model.updated_at = datetime.now().isoformat()

    def record_task_completion(self, task: str, tools_used: List[str], success: bool):
        tasks = self.user_model.behaviors.common_tasks
        if task not in tasks:
            tasks.append(task)

        for tool in tools_used:
            self.record_tool_usage(tool, {'task': task, 'success': success})

        if len(self._current_sequence) > 0:
            self._tool_sequences.append(self._current_sequence.copy())
            self._current_sequence.clear()

        self.user_model.updated_at = datetime.now().isoformat()

    def get_common_tasks(self, limit: int = 10) -> List[str]:
        tasks = self.user_model.behaviors.common_tasks
        return tasks[:limit]

    def get_tool_usage_stats(self) -> Dict[str, int]:
        return dict(self.user_model.behaviors.tool_usage_history)

    def detect_tool_pattern(self) -> Optional[List[str]]:
        if len(self._tool_sequences) < 3:
            return None

        sequences = list(self._tool_sequences)
        pattern = []

        for seq in sequences:
            if len(seq) > len(pattern):
                pattern = seq

        return pattern if len(pattern) > 0 else None

    def get_behavior_summary(self) -> Dict[str, Any]:
        return {
            'total_interactions': self.user_model.behaviors.total_interactions,
            'avg_session_length': self.user_model.behaviors.avg_session_length,
            'common_tasks': self.get_common_tasks(),
            'tool_usage_stats': self.get_tool_usage_stats(),
            'conversation_topics': self.user_model.behaviors.conversation_topics,
            'peak_interaction_hours': self.user_model.behaviors.peak_interaction_hours,
            'recent_behavior_count': len(self._recent_behaviors)
        }

    def predict_next_tool(self, current_task: str) -> Optional[str]:
        if len(self._tool_sequences) < 2:
            return None

        task_sequences: Dict[str, List[List[str]]] = {}

        for seq in self._tool_sequences:
            if len(seq) > 0:
                task_key = seq[0]
                if task_key not in task_sequences:
                    task_sequences[task_key] = []
                task_sequences[task_key].append(seq)

        if current_task in task_sequences:
            sequences = task_sequences[current_task]
            if len(sequences) >= 2:
                last_seq = sequences[-1]
                if len(last_seq) > 1:
                    return last_seq[-1]

        tool_freq: Dict[str, int] = {}
        for seq in self._tool_sequences:
            for tool in seq:
                tool_freq[tool] = tool_freq.get(tool, 0) + 1

        if tool_freq:
            return max(tool_freq, key=tool_freq.get)

        return None
