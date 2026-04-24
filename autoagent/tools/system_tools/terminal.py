"""
终端工具 - 安全的命令执行
"""

import subprocess
import shlex
from typing import Optional, List


DANGEROUS_COMMANDS = [
    "rm -rf /", "rm -rf /*", "format c:", "del /f /s /q c:",
    "shutdown", "restart", "mkfs", "dd if=",
    ":(){ :|:& };:", "curl | sh", "wget | sh",
]


def execute_terminal(command: str, cwd: str = None, timeout: int = 60) -> dict:
    """
    安全地执行终端命令

    Args:
        command: 要执行的命令
        cwd: 工作目录，默认为当前目录
        timeout: 超时时间（秒），默认60

    Returns:
        dict: 包含success状态、stdout、stderr和returncode
    """
    if not command or not command.strip():
        return {"success": False, "error": "命令不能为空"}

    cmd_lower = command.lower().strip()

    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in cmd_lower:
            return {
                "success": False,
                "error": f"禁止执行危险命令: {dangerous}",
                "command": command
            }

    if any(cmd in cmd_lower for cmd in ["sudo", "su ", " chmod 777", "chmod -r 777"]):
        return {
            "success": False,
            "error": "禁止执行提权或权限修改命令",
            "command": command
        }

    try:
        if isinstance(command, str) and not _is_safe_shell_command(command):
            cmd = shlex.split(command)
        else:
            cmd = command

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"命令执行超时（{timeout}秒）",
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"命令执行失败: {str(e)}",
            "command": command
        }


def _is_safe_shell_command(command: str) -> bool:
    """检查是否为安全的shell命令"""
    safe_patterns = [
        "cd ", "ls", "dir", "pwd", "echo", "cat", "head", "tail",
        "grep", "find", "wc", "sort", "uniq", "cut", "awk", "sed",
        "python", "python3", "node", "npm", "git", "curl", "wget",
    ]
    cmd_start = command.strip().split()[0] if command.strip() else ""
    return any(pattern == cmd_start or command.startswith(pattern)
               for pattern in safe_patterns)


def execute_script(script: str, interpreter: str = "bash", cwd: str = None, timeout: int = 60) -> dict:
    """
    执行脚本文件

    Args:
        script: 脚本内容或路径
        interpreter: 解释器类型 (bash, python, node)
        cwd: 工作目录
        timeout: 超时时间

    Returns:
        dict: 执行结果
    """
    import tempfile
    import os

    safe_interpreters = ["bash", "python", "python3", "node", "powershell"]
    if interpreter not in safe_interpreters:
        return {"success": False, "error": f"不支持的解释器: {interpreter}"}

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=f".{interpreter}", delete=False) as f:
            f.write(script)
            script_path = f.name

        try:
            cmd = f"{interpreter} {script_path}"
            return execute_terminal(cmd, cwd=cwd, timeout=timeout)
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    except Exception as e:
        return {"success": False, "error": f"脚本执行失败: {str(e)}"}
