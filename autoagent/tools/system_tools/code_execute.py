"""
代码执行工具 - 沙箱代码执行
"""

import subprocess
import tempfile
import os
import resource
from typing import Dict, Optional


ALLOWED_LANGUAGES = ["python", "javascript", "node", "bash", "sh", "ruby", "php"]
DANGEROUS_PATTERNS = [
    "import os", "import sys", "import subprocess", "import multiprocessing",
    "from os", "from sys", "from subprocess", "import socket",
    "import requests", "import urllib", "subprocess.", "os.system",
    "__import__", "eval(", "exec(", "open(", "file(",
    "child_process", "require('child_process')", "import subprocess",
    "Runtime.getRuntime", "ProcessBuilder", "System.exit",
]


def execute_code(code: str, language: str = "python", timeout: int = 30) -> dict:
    """
    在沙箱环境中执行代码

    Args:
        code: 要执行的代码
        language: 语言类型 (python, javascript, bash等)
        timeout: 超时时间（秒），默认30

    Returns:
        dict: 包含success状态、output、error和execution_time
    """
    language = language.lower().strip()

    if language not in ALLOWED_LANGUAGES:
        return {
            "success": False,
            "error": f"不支持的语言: {language}",
            "allowed_languages": ALLOWED_LANGUAGES
        }

    if language in ["python", "python3"]:
        return _execute_python(code, timeout)
    elif language in ["javascript", "node"]:
        return _execute_javascript(code, timeout)
    elif language in ["bash", "sh"]:
        return _execute_bash(code, timeout)
    else:
        return {"success": False, "error": f"未实现的语言: {language}"}


def _check_dangerous(code: str) -> Optional[str]:
    """检查危险代码模式"""
    for pattern in DANGEROUS_PATTERNS:
        if pattern in code:
            return pattern
    return None


def _execute_python(code: str, timeout: int) -> dict:
    """执行Python代码"""
    dangerous = _check_dangerous(code)
    if dangerous:
        return {
            "success": False,
            "error": f"禁止使用危险代码: {dangerous}",
            "language": "python"
        }

    import time
    start_time = time.time()

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            script_path = f.name

        try:
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )

            execution_time = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "language": "python",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "execution_time": round(execution_time, 3)
            }

        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "language": "python",
            "error": f"执行超时（{timeout}秒）",
            "execution_time": timeout
        }
    except FileNotFoundError:
        return {
            "success": False,
            "language": "python",
            "error": "Python解释器未找到"
        }
    except Exception as e:
        return {
            "success": False,
            "language": "python",
            "error": f"执行失败: {str(e)}"
        }


def _execute_javascript(code: str, timeout: int) -> dict:
    """执行JavaScript代码"""
    dangerous = _check_dangerous(code)
    if dangerous:
        return {
            "success": False,
            "error": f"禁止使用危险代码: {dangerous}",
            "language": "javascript"
        }

    import time
    start_time = time.time()

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            script_path = f.name

        try:
            result = subprocess.run(
                ["node", script_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            execution_time = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "language": "javascript",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "execution_time": round(execution_time, 3)
            }

        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "language": "javascript",
            "error": f"执行超时（{timeout}秒）",
            "execution_time": timeout
        }
    except FileNotFoundError:
        return {
            "success": False,
            "language": "javascript",
            "error": "Node.js解释器未找到"
        }
    except Exception as e:
        return {
            "success": False,
            "language": "javascript",
            "error": f"执行失败: {str(e)}"
        }


def _execute_bash(code: str, timeout: int) -> dict:
    """执行Bash脚本"""
    dangerous = _check_dangerous(code)
    if dangerous:
        return {
            "success": False,
            "error": f"禁止使用危险代码: {dangerous}",
            "language": "bash"
        }

    import time
    start_time = time.time()

    try:
        result = subprocess.run(
            ["bash", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        execution_time = time.time() - start_time

        return {
            "success": result.returncode == 0,
            "language": "bash",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "execution_time": round(execution_time, 3)
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "language": "bash",
            "error": f"执行超时（{timeout}秒）",
            "execution_time": timeout
        }
    except FileNotFoundError:
        return {
            "success": False,
            "language": "bash",
            "error": "Bash解释器未找到"
        }
    except Exception as e:
        return {
            "success": False,
            "language": "bash",
            "error": f"执行失败: {str(e)}"
        }
