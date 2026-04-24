"""
工具学习器 - 从使用历史中学习工具推荐
"""

from typing import Dict, List, Any, Optional
from collections import deque, Counter
from datetime import datetime


class ToolLearner:
    """
    工具学习器

    功能:
    1. 追踪工具使用频率
    2. 检测工具使用模式
    3. 推荐常用工具
    4. 学习工具序列
    """

    def __init__(self):
        self._tool_usage_count: Counter = Counter()
        self._tool_sequences: deque = deque(maxlen=100)
        self._current_sequence: List[str] = []
        self._task_tool_map: Dict[str, List[str]] = {}
        self._last_tool: Optional[str] = None
        self._sequence_patterns: Dict[str, int] = {}

    def record_tool_usage(self, tool_name: str, task_context: Optional[str] = None):
        """
        记录工具使用

        Args:
            tool_name: 工具名称
            task_context: 任务上下文
        """
        self._tool_usage_count[tool_name] += 1

        if self._last_tool:
            sequence_key = f"{self._last_tool}->{tool_name}"
            self._sequence_patterns[sequence_key] = self._sequence_patterns.get(sequence_key, 0) + 1

        self._current_sequence.append(tool_name)
        self._last_tool = tool_name

        if task_context:
            if task_context not in self._task_tool_map:
                self._task_tool_map[task_context] = []
            if tool_name not in self._task_tool_map[task_context]:
                self._task_tool_map[task_context].append(tool_name)

    def end_task(self):
        """结束当前任务，记录序列"""
        if len(self._current_sequence) > 1:
            sequence_tuple = tuple(self._current_sequence)
            self._tool_sequences.append(sequence_tuple)
        self._current_sequence = []
        self._last_tool = None

    def get_top_tools(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最常用的工具

        Args:
            limit: 返回数量

        Returns:
            工具列表，包含使用次数和百分比
        """
        total = sum(self._tool_usage_count.values()) if self._tool_usage_count else 1

        return [
            {
                "tool": tool,
                "count": count,
                "percentage": round(count / total * 100, 1)
            }
            for tool, count in self._tool_usage_count.most_common(limit)
        ]

    def recommend_for_task(self, task: str) -> List[str]:
        """
        根据任务推荐工具

        Args:
            task: 任务描述

        Returns:
            推荐的工具列表
        """
        task_lower = task.lower()

        recommendations = []

        for context, tools in self._task_tool_map.items():
            if context.lower() in task_lower or task_lower in context.lower():
                recommendations.extend(tools)

        seen = set()
        unique_recs = []
        for tool in recommendations:
            if tool not in seen:
                seen.add(tool)
                unique_recs.append(tool)

        return unique_recs[:5]

    def get_next_tool_prediction(self, current_tool: Optional[str] = None) -> Optional[str]:
        """
        预测下一个可能使用的工具

        Args:
            current_tool: 当前使用的工具

        Returns:
            预测的工具名称
        """
        if current_tool:
            search_key = f"{current_tool}->"
        elif self._last_tool:
            search_key = f"{self._last_tool}->"
        else:
            return None

        candidates = [
            (key.split("->")[1], count)
            for key, count in self._sequence_patterns.items()
            if key.startswith(search_key)
        ]

        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return None

    def detect_sequence_pattern(self, sequence: List[str]) -> bool:
        """
        检测是否存在指定序列模式

        Args:
            sequence: 要检测的序列

        Returns:
            是否存在
        """
        sequence_tuple = tuple(sequence)
        return sequence_tuple in self._tool_sequences

    def get_sequence_suggestion(self, current_tools: List[str]) -> Optional[str]:
        """
        根据当前工具序列获取建议

        Args:
            current_tools: 当前已使用的工具列表

        Returns:
            建议的下一个工具
        """
        if not current_tools:
            return None

        current_tuple = tuple(current_tools)

        matches = [
            (seq, count)
            for seq, count in zip(self._tool_sequences, [1] * len(self._tool_sequences))
            if seq[:len(current_tuple)] == current_tuple and len(seq) > len(current_tuple)
        ]

        if matches:
            return matches[0][0][len(current_tuple)]

        return self.get_next_tool_prediction(current_tools[-1] if current_tools else None)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取工具学习统计

        Returns:
            统计信息
        """
        total_uses = sum(self._tool_usage_count.values())
        unique_tools = len(self._tool_usage_count)
        sequence_count = len(self._tool_sequences)

        return {
            "total_tool_uses": total_uses,
            "unique_tools_used": unique_tools,
            "recorded_sequences": sequence_count,
            "top_tools": self.get_top_tools(5),
            "common_patterns": self._get_common_patterns(3)
        }

    def _get_common_patterns(self, limit: int) -> List[Dict[str, Any]]:
        """获取常用工具序列模式"""
        sorted_patterns = sorted(
            self._sequence_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {"pattern": pattern, "count": count}
            for pattern, count in sorted_patterns
        ]