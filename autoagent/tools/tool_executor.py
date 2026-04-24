import logging
import time
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .tool_registry import ToolRegistry
from .base_tool import ToolResult, BaseTool

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry.get_instance()
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history = 1000

    def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        start_time = time.time()

        tool_func = self.registry.get_tool(tool_name)
        if tool_func is None:
            error_msg = f"Tool '{tool_name}' not found"
            logger.error(error_msg)
            return ToolResult.error_result(error_msg)

        is_valid, error_msg = self.validate_params(tool_name, params)
        if not is_valid:
            logger.warning(f"Invalid params for tool '{tool_name}': {error_msg}")
            return ToolResult.error_result(f"Invalid parameters: {error_msg}")

        try:
            context = context or {}

            if isinstance(tool_func, BaseTool):
                result = tool_func.execute(params, context)
            else:
                sig_params = self._build_signature_params(tool_func, params, context)
                result = tool_func(**sig_params)

            execution_time = time.time() - start_time

            if isinstance(result, ToolResult):
                result.execution_time = execution_time
                tool_result = result
            else:
                tool_result = ToolResult.success_result(result, execution_time=execution_time)

            self._add_to_history({
                "tool_name": tool_name,
                "params": params,
                "context": context,
                "result": tool_result.to_dict(),
                "execution_time": execution_time,
            })

            logger.info(f"Tool '{tool_name}' executed successfully in {execution_time:.3f}s")
            return tool_result

        except TypeError as e:
            error_msg = f"Parameter error: {str(e)}"
            logger.error(f"Tool '{tool_name}' execution failed: {error_msg}")
            return ToolResult.error_result(error_msg)

        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            logger.error(f"Tool '{tool_name}' execution failed: {error_msg}", exc_info=True)
            return ToolResult.error_result(error_msg)

    def execute_batch(self, tools_calls: List[Dict[str, Any]]) -> List[ToolResult]:
        results = []

        for call in tools_calls:
            tool_name = call.get("tool_name")
            params = call.get("params", {})
            context = call.get("context")

            if not tool_name:
                results.append(ToolResult.error_result("Missing tool_name in batch call"))
                continue

            result = self.execute_tool(tool_name, params, context)
            results.append(result)

        return results

    def execute_parallel(self, tools_calls: List[Dict[str, Any]], max_workers: int = 5) -> List[ToolResult]:
        results_dict: Dict[int, ToolResult] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {}

            for index, call in enumerate(tools_calls):
                tool_name = call.get("tool_name")
                params = call.get("params", {})
                context = call.get("context")

                if not tool_name:
                    results_dict[index] = ToolResult.error_result("Missing tool_name in batch call")
                    continue

                future = executor.submit(self.execute_tool, tool_name, params, context)
                future_to_index[future] = index

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results_dict[index] = result
                except Exception as e:
                    results_dict[index] = ToolResult.error_result(f"Parallel execution error: {str(e)}")

        ordered_results = [results_dict[i] for i in range(len(tools_calls))]
        return ordered_results

    def validate_params(self, tool_name: str, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        tool_func = self.registry.get_tool(tool_name)
        if tool_func is None:
            return False, f"Tool '{tool_name}' not found"

        schema = self.registry.get_tool_schema(tool_name)
        if not schema:
            return True, None

        required = schema.get("parameters_schema", {}).get("required", [])
        properties = schema.get("parameters_schema", {}).get("properties", {})

        for req_param in required:
            if req_param not in params:
                return False, f"Missing required parameter: {req_param}"

        for param_name, param_value in params.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type and not self._check_type(param_value, expected_type):
                    return False, f"Parameter '{param_name}' expected {expected_type}, got {type(param_value).__name__}"

        return True, None

    def get_tool_result_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        schema = self.registry.get_tool_schema(tool_name)
        if schema:
            return schema.get("result_schema")
        return None

    def _build_signature_params(
        self,
        tool_func: Any,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        import inspect
        sig = inspect.signature(tool_func)
        sig_params = {}

        for param_name, param_def in sig.parameters.items():
            if param_name == "context" and param_def.annotation == inspect.Parameter.empty:
                sig_params[param_name] = context
            elif param_name in params:
                sig_params[param_name] = params[param_name]
            elif param_def.default != inspect.Parameter.empty:
                sig_params[param_name] = param_def.default

        return sig_params

    def _check_type(self, value: Any, expected_type: str) -> bool:
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        return isinstance(value, expected)

    def _add_to_history(self, entry: Dict[str, Any]) -> None:
        self._execution_history.append(entry)
        if len(self._execution_history) > self._max_history:
            self._execution_history.pop(0)

    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit:
            return self._execution_history[-limit:]
        return self._execution_history.copy()

    def clear_history(self) -> None:
        self._execution_history.clear()
        logger.info("Tool execution history cleared")
