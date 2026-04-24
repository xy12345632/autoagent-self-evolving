import re
from typing import Any, Optional

DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"del\s+/[fqs]",
    r"format\s+",
    r"shutdown",
    r"reboot",
    r"drop\s+table",
    r"delete\s+from",
    r"exec\s*\(",
    r"eval\s*\(",
    r"__import__",
]


class ToolFilter:
    def __init__(self):
        self._dangerous_patterns = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

    def filter_tools(
        self,
        tools: list[dict[str, Any]],
        allowed_patterns: Optional[list[str]] = None,
        blocked_patterns: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        if not allowed_patterns and not blocked_patterns:
            return tools

        allowed_regex = [re.compile(p, re.IGNORECASE) for p in allowed_patterns] if allowed_patterns else None
        blocked_regex = [re.compile(p, re.IGNORECASE) for p in blocked_patterns] if blocked_patterns else None

        filtered = []
        for tool in tools:
            name = tool.get("name", "")
            if blocked_regex and any(p.search(name) for p in blocked_regex):
                continue
            if allowed_regex and not any(p.search(name) for p in allowed_regex):
                continue
            filtered.append(tool)
        return filtered

    def transform_tool_schema(self, tool_schema: dict[str, Any]) -> dict[str, Any]:
        transformed = {
            "name": tool_schema.get("name", ""),
            "description": tool_schema.get("description", ""),
            "inputSchema": tool_schema.get("inputSchema", {"type": "object", "properties": {}}),
        }
        if "parameters" in tool_schema:
            transformed["inputSchema"] = tool_schema["parameters"]
        return transformed

    def validate_tool_safety(self, tool: dict[str, Any]) -> tuple[bool, Optional[str]]:
        name = tool.get("name", "")
        description = tool.get("description", "")
        combined = f"{name} {description}"

        for pattern in self._dangerous_patterns:
            if pattern.search(combined):
                return False, f"检测到危险模式: {pattern.pattern}"

        return True, None
