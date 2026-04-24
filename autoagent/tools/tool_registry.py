import logging
from typing import Dict, Any, Optional, List, Callable
from threading import RLock

logger = logging.getLogger(__name__)


class ToolRegistry:
    _instance: Optional["ToolRegistry"] = None
    _lock = RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, List[str]] = {}
        self._initialized = True
        logger.info("ToolRegistry initialized")

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_tool(
        self,
        tool_name: str,
        tool_func: Callable,
        schema: Optional[Dict[str, Any]] = None
    ) -> None:
        with self._lock:
            if tool_name in self._tools:
                logger.warning(f"Tool '{tool_name}' already registered, overwriting")

            self._tools[tool_name] = tool_func
            if schema:
                self._schemas[tool_name] = schema

            category = schema.get("category") if schema else None
            if category:
                if category not in self._categories:
                    self._categories[category] = []
                if tool_name not in self._categories[category]:
                    self._categories[category].append(tool_name)

            logger.info(f"Registered tool: {tool_name}")

    def unregister_tool(self, tool_name: str) -> bool:
        with self._lock:
            if tool_name not in self._tools:
                logger.warning(f"Tool '{tool_name}' not found for unregistration")
                return False

            del self._tools[tool_name]
            self._schemas.pop(tool_name, None)

            for category_tools in self._categories.values():
                if tool_name in category_tools:
                    category_tools.remove(tool_name)

            logger.info(f"Unregistered tool: {tool_name}")
            return True

    def get_tool(self, tool_name: str) -> Optional[Callable]:
        return self._tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        if category:
            return self._categories.get(category, []).copy()
        return list(self._tools.keys())

    def get_categories(self) -> List[str]:
        return list(self._categories.keys())

    def get_tools_by_category(self, category: str) -> List[str]:
        return self._categories.get(category, []).copy()

    def search_tools(self, query: str) -> List[str]:
        query_lower = query.lower()
        results = []

        for tool_name in self._tools:
            if query_lower in tool_name.lower():
                results.append(tool_name)
                continue

            schema = self._schemas.get(tool_name, {})
            description = schema.get("description", "").lower()
            if query_lower in description:
                results.append(tool_name)
                continue

            tags = schema.get("tags", [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(tool_name)

        return results

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        return self._schemas.get(tool_name)

    def update_tool_schema(self, tool_name: str, schema: Dict[str, Any]) -> bool:
        with self._lock:
            if tool_name not in self._tools:
                logger.warning(f"Cannot update schema for unregistered tool: {tool_name}")
                return False

            old_category = self._schemas.get(tool_name, {}).get("category")
            new_category = schema.get("category")

            if old_category and old_category in self._categories:
                if tool_name in self._categories[old_category]:
                    self._categories[old_category].remove(tool_name)

            if new_category:
                if new_category not in self._categories:
                    self._categories[new_category] = []
                if tool_name not in self._categories[new_category]:
                    self._categories[new_category].append(tool_name)

            self._schemas[tool_name] = schema
            return True

    def clear(self) -> None:
        with self._lock:
            self._tools.clear()
            self._schemas.clear()
            self._categories.clear()
            logger.info("ToolRegistry cleared")

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        return self._schemas.copy()

    def get_tool_count(self) -> int:
        return len(self._tools)

    def get_registry_info(self) -> Dict[str, Any]:
        return {
            "total_tools": len(self._tools),
            "categories": {cat: len(tools) for cat, tools in self._categories.items()},
            "tools": list(self._tools.keys()),
        }
