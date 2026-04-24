from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict, List


@dataclass
class ToolMetadata:
    name: str
    description: str
    category: Optional[str] = None
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    result_schema: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    version: str = "1.0.0"
    deprecated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters_schema": self.parameters_schema,
            "result_schema": self.result_schema,
            "examples": self.examples,
            "version": self.version,
            "deprecated": self.deprecated,
        }


@dataclass
class ToolResult:
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            success=data.get("success", False),
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
            execution_time=data.get("execution_time"),
            timestamp=timestamp or datetime.now(),
        )

    @classmethod
    def success_result(cls, result: Any, metadata: Optional[Dict[str, Any]] = None, execution_time: Optional[float] = None) -> "ToolResult":
        return cls(
            success=True,
            result=result,
            metadata=metadata or {},
            execution_time=execution_time,
        )

    @classmethod
    def error_result(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        return cls(
            success=False,
            error=error,
            metadata=metadata or {},
        )


class BaseTool(ABC):
    def __init__(self):
        self._metadata: Optional[ToolMetadata] = None

    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        pass

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        schema = self.get_metadata().parameters_schema
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for req_param in required:
            if req_param not in params:
                return False, f"Missing required parameter: {req_param}"

        for param_name, param_value in params.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type and not self._check_type(param_value, expected_type):
                    return False, f"Parameter '{param_name}' expected {expected_type}, got {type(param_value).__name__}"

        return True, None

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

    def get_name(self) -> str:
        return self.get_metadata().name

    def get_description(self) -> str:
        return self.get_metadata().description
