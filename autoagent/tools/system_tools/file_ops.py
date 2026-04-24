"""
文件操作工具 - 读取、写入、列出文件
"""

import os
import glob
from pathlib import Path
from typing import Optional, List


ALLOWED_DIRS = [
    os.getcwd(),
    os.path.expanduser("~"),
    os.path.join(os.getcwd(), "workspace"),
]


def file_read(path: str) -> dict:
    """
    读取文件内容

    Args:
        path: 文件路径

    Returns:
        dict: 包含success状态和content或error信息
    """
    if not path or not path.strip():
        return {"success": False, "error": "路径不能为空"}

    path = os.path.abspath(path)

    if not _is_path_allowed(path):
        return {"success": False, "error": "路径不在允许范围内"}

    if not os.path.exists(path):
        return {"success": False, "error": f"文件不存在: {path}"}

    if not os.path.isfile(path):
        return {"success": False, "error": f"路径不是文件: {path}"}

    if not os.access(path, os.R_OK):
        return {"success": False, "error": "没有读取权限"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "success": True,
            "path": path,
            "content": content,
            "size": len(content),
            "lines": len(content.splitlines())
        }

    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="gbk") as f:
                content = f.read()
            return {
                "success": True,
                "path": path,
                "content": content,
                "size": len(content),
                "encoding": "gbk"
            }
        except Exception as e:
            return {"success": False, "error": f"文件编码错误: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"读取失败: {str(e)}"}


def file_write(path: str, content: str, append: bool = False) -> dict:
    """
    写入文件内容

    Args:
        path: 文件路径
        content: 要写入的内容
        append: 是否追加模式，默认False（覆盖）

    Returns:
        dict: 包含success状态和写入信息或error信息
    """
    if not path or not path.strip():
        return {"success": False, "error": "路径不能为空"}

    path = os.path.abspath(path)

    if not _is_path_allowed(path):
        return {"success": False, "error": "路径不在允许范围内"}

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "path": path,
            "bytes_written": len(content.encode("utf-8")),
            "append": append
        }

    except PermissionError:
        return {"success": False, "error": "没有写入权限"}
    except Exception as e:
        return {"success": False, "error": f"写入失败: {str(e)}"}


def file_list(path: str, pattern: str = "*") -> dict:
    """
    列出目录下的文件

    Args:
        path: 目录路径
        pattern: 文件匹配模式，如 "*.py", "*.txt"

    Returns:
        dict: 包含success状态和files列表或error信息
    """
    if not path or not path.strip():
        return {"success": False, "error": "路径不能为空"}

    path = os.path.abspath(path)

    if not _is_path_allowed(path):
        return {"success": False, "error": "路径不在允许范围内"}

    if not os.path.exists(path):
        return {"success": False, "error": f"目录不存在: {path}"}

    if not os.path.isdir(path):
        return {"success": False, "error": f"路径不是目录: {path}"}

    try:
        search_path = os.path.join(path, pattern)
        files = glob.glob(search_path)

        result_files = []
        for f in files:
            try:
                stat = os.stat(f)
                result_files.append({
                    "name": os.path.basename(f),
                    "path": f,
                    "is_dir": os.path.isdir(f),
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
            except:
                continue

        result_files.sort(key=lambda x: (not x["is_dir"], x["name"]))

        return {
            "success": True,
            "path": path,
            "pattern": pattern,
            "count": len(result_files),
            "files": result_files
        }

    except Exception as e:
        return {"success": False, "error": f"列出文件失败: {str(e)}"}


def _is_path_allowed(path: str) -> bool:
    """检查路径是否在允许的目录范围内"""
    path = os.path.abspath(path)

    for allowed in ALLOWED_DIRS:
        allowed = os.path.abspath(allowed)
        if path.startswith(allowed):
            return True

    if "..\\" not in path and "/../" not in path.replace("\\", "/"):
        return True

    return False
