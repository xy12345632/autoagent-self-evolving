import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

from .tool_registry import ToolRegistry
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

TOOL_FILE_PATTERN = "*.py"
TOOL_CLASS_SUFFIX = "Tool"
EXCLUDED_FILES = {"__init__.py", "base_tool.py", "tool_registry.py", "tool_executor.py", "tools_loader.py"}


class ToolsLoader:
    def __init__(self, tools_dir: Optional[str] = None, registry: Optional[ToolRegistry] = None):
        if tools_dir:
            self.tools_dir = Path(tools_dir)
        else:
            self.tools_dir = Path(__file__).parent
        self.registry = registry or ToolRegistry.get_instance()
        self._discovered_tools: Dict[str, Dict[str, Any]] = {}

    def discover_tools(self) -> Dict[str, Dict[str, Any]]:
        self._discovered_tools.clear()

        if not self.tools_dir.exists():
            logger.warning(f"Tools directory does not exist: {self.tools_dir}")
            return {}

        for py_file in self.tools_dir.glob(TOOL_FILE_PATTERN):
            if py_file.name in EXCLUDED_FILES:
                continue

            try:
                module_name = py_file.stem
                module = self._import_module(module_name)

                if module:
                    tools = self._extract_tools_from_module(module)
                    for tool_name, tool_info in tools.items():
                        self._discovered_tools[tool_name] = tool_info
                        logger.info(f"Discovered tool: {tool_name}")

            except Exception as e:
                logger.error(f"Failed to discover tools from {py_file}: {e}", exc_info=True)

        return self._discovered_tools

    def load_all_tools(self) -> int:
        logger.info(f"Loading all tools from {self.tools_dir}")

        discovered = self.discover_tools()
        loaded_count = 0

        for tool_name, tool_info in discovered.items():
            try:
                self._register_tool(tool_name, tool_info)
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load tool '{tool_name}': {e}", exc_info=True)

        logger.info(f"Loaded {loaded_count} tools")
        return loaded_count

    def reload_tools(self) -> int:
        logger.info("Reloading all tools...")
        self.registry.clear()
        return self.load_all_tools()

    def load_tool(self, tool_name: str) -> bool:
        if tool_name in self._discovered_tools:
            tool_info = self._discovered_tools[tool_name]
            self._register_tool(tool_name, tool_info)
            return True

        for py_file in self.tools_dir.glob(TOOL_FILE_PATTERN):
            if py_file.name in EXCLUDED_FILES:
                continue

            try:
                module_name = py_file.stem
                module = self._import_module(module_name)

                if module:
                    tools = self._extract_tools_from_module(module)
                    if tool_name in tools:
                        self._register_tool(tool_name, tools[tool_name])
                        self._discovered_tools[tool_name] = tools[tool_name]
                        return True

            except Exception as e:
                logger.error(f"Failed to load tool '{tool_name}' from {py_file}: {e}")

        return False

    def unload_tool(self, tool_name: str) -> bool:
        return self.registry.unregister_tool(tool_name)

    def _import_module(self, module_name: str):
        try:
            full_module_name = f"autoagent.tools.{module_name}"
            return importlib.import_module(full_module_name)
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            return None

    def _extract_tools_from_module(self, module) -> Dict[str, Dict[str, Any]]:
        tools = {}

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith(TOOL_CLASS_SUFFIX) and issubclass(obj, BaseTool) and obj is not BaseTool:
                try:
                    instance = obj()
                    metadata = instance.get_metadata()
                    tools[metadata.name] = {
                        "instance": instance,
                        "metadata": metadata.to_dict(),
                        "class": obj,
                    }
                except Exception as e:
                    logger.error(f"Failed to instantiate tool class {name}: {e}")

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and hasattr(obj, "_tool_metadata"):
                metadata = getattr(obj, "_tool_metadata")
                tools[metadata.get("name", name)] = {
                    "function": obj,
                    "metadata": metadata,
                }

        return tools

    def _register_tool(self, tool_name: str, tool_info: Dict[str, Any]) -> None:
        metadata = tool_info.get("metadata", {})
        instance = tool_info.get("instance")
        function = tool_info.get("function")

        if instance:
            self.registry.register_tool(tool_name, instance, metadata)
        elif function:
            self.registry.register_tool(tool_name, function, metadata)

    def get_discovered_tools(self) -> Dict[str, Dict[str, Any]]:
        return self._discovered_tools.copy()

    def list_discovered_tool_ids(self) -> List[str]:
        return list(self._discovered_tools.keys())

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        return self._discovered_tools.get(tool_name)


def register_tool_func(tool_name: str, description: str, parameters_schema: Optional[Dict[str, Any]] = None):
    def decorator(func: Callable) -> Callable:
        metadata = {
            "name": tool_name,
            "description": description,
            "parameters_schema": parameters_schema or {"type": "object", "properties": {}},
        }
        func._tool_metadata = metadata
        return func
    return decorator


def load_all_tools(tools_dir: Optional[str] = None) -> int:
    loader = ToolsLoader(tools_dir=tools_dir)
    return loader.load_all_tools()


def discover_tools(tools_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    loader = ToolsLoader(tools_dir=tools_dir)
    return loader.discover_tools()


def _load_builtin_tools():
    try:
        from . import translation
        from . import calculator
        from . import weather
        from . import news
    except ImportError:
        pass

_load_builtin_tools()
