"""计算器工具"""

import re
import math
from typing import Dict, Any

TOOL_SCHEMA = {
    "name": "calculator",
    "description": "执行数学计算",
    "category": "utility",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '2+2', 'sqrt(16)', 'sin(pi/2)'"
            }
        },
        "required": ["expression"]
    }
}

def calculate(expression: str) -> Dict[str, Any]:
    """
    执行数学计算

    支持: +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e
    """
    try:
        safe_dict = {
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "pi": math.pi,
            "e": math.e,
            "abs": abs,
            "round": round,
        }

        expression = expression.lower().replace('^', '**')

        allowed_chars = set('0123456789+-*/(). sqrtcostanlogpie ')
        if not all(c in allowed_chars or c.isalnum() for c in expression):
            return {"success": False, "error": "Invalid characters in expression"}

        result = eval(expression, {"__builtins__": {}}, safe_dict)

        return {
            "success": True,
            "expression": expression,
            "result": result
        }
    except ZeroDivisionError:
        return {"success": False, "error": "Division by zero"}
    except Exception as e:
        return {"success": False, "error": f"Calculation error: {str(e)}"}

calculate._tool_metadata = TOOL_SCHEMA