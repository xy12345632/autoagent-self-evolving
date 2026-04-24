"""
CLI Input Handling - CLI输入处理模块
"""

import sys
import asyncio
from typing import Optional, List


class CLIInput:
    def __init__(self):
        self._history: List[str] = []
        self._history_index: int = -1

    def prompt_input(self, prompt_text: str = ">>> ") -> str:
        try:
            user_input = input(prompt_text)
            if user_input.strip():
                self._history.append(user_input)
            self._history_index = -1
            return user_input
        except (KeyboardInterrupt, EOFError):
            return ""

    def multiline_input(self, prompt_text: str = ">> ") -> str:
        lines = []
        print("多行输入模式 (Ctrl+D 或 Ctrl+Z 结束输入):")
        try:
            while True:
                line = input(prompt_text)
                lines.append(line)
        except EOFError:
            pass
        return "\n".join(lines)

    def history_navigation(self, direction: str = "up") -> Optional[str]:
        if not self._history:
            return None

        if direction == "up":
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
        elif direction == "down":
            if self._history_index > 0:
                self._history_index -= 1
            elif self._history_index == 0:
                self._history_index = -1
                return ""

        if 0 <= self._history_index < len(self._history):
            return self._history[len(self._history) - 1 - self._history_index]
        return None

    def add_to_history(self, text: str) -> None:
        if text.strip():
            self._history.append(text)
        self._history_index = -1

    def clear_history(self) -> None:
        self._history = []
        self._history_index = -1

    def get_history(self) -> List[str]:
        return self._history.copy()

    def search_history(self, query: str) -> List[str]:
        query_lower = query.lower()
        return [item for item in self._history if query_lower in item.lower()]
