"""
定时任务工具 - 任务调度和Cron表达式管理
"""

import os
import uuid
import time
import threading
import schedule
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from croniter import croniter


_SCHEDULED_TASKS = {}
_TASK_THREADS = {}
_TASK_COUNTER = 0


def schedule_task(cron_expr: str, task_data: dict) -> dict:
    """
    创建一个定时任务

    参数:
        cron_expr: Cron表达式 (如 "0 9 * * *" 表示每天9点)
        task_data: 任务数据，包含:
            - task_name: 任务名称
            - task_func: 任务函数名 (字符串)
            - params: 任务参数 (可选)
            - enabled: 是否启用 (默认True)

    返回:
        包含任务ID的字典
    """
    global _TASK_COUNTER

    if not cron_expr or not cron_expr.strip():
        return {"success": False, "error": "Cron表达式不能为空"}

    if not task_data or not task_data.get("task_name"):
        return {"success": False, "error": "任务名称不能为空"}

    try:
        base_time = datetime.now()
        cron = croniter(cron_expr, base_time)

        next_run = cron.get_next(datetime)

        task_id = f"task_{uuid.uuid4().hex[:8]}"

        _SCHEDULED_TASKS[task_id] = {
            "id": task_id,
            "task_name": task_data.get("task_name"),
            "task_func": task_data.get("task_func"),
            "params": task_data.get("params", {}),
            "cron_expr": cron_expr,
            "enabled": task_data.get("enabled", True),
            "created_at": datetime.now().isoformat(),
            "next_run": next_run.isoformat(),
            "last_run": None,
            "run_count": 0
        }

        _TASK_COUNTER += 1

        return {
            "success": True,
            "task_id": task_id,
            "task_name": task_data.get("task_name"),
            "cron_expr": cron_expr,
            "next_run": next_run.isoformat(),
            "message": "任务创建成功"
        }

    except (ValueError, KeyError) as e:
        return {
            "success": False,
            "error": f"无效的Cron表达式: {str(e)}"
        }


def list_scheduled_tasks() -> dict:
    """
    列出所有定时任务

    返回:
        包含任务列表的字典
    """
    tasks = []

    for task_id, task_info in _SCHEDULED_TASKS.items():
        tasks.append({
            "id": task_id,
            "task_name": task_info.get("task_name"),
            "cron_expr": task_info.get("cron_expr"),
            "enabled": task_info.get("enabled"),
            "next_run": task_info.get("next_run"),
            "last_run": task_info.get("last_run"),
            "run_count": task_info.get("run_count", 0),
            "created_at": task_info.get("created_at")
        })

    tasks.sort(key=lambda x: x.get("next_run") or "")

    return {
        "success": True,
        "tasks": tasks,
        "total": len(tasks),
        "enabled_count": len([t for t in tasks if t.get("enabled")])
    }


def cancel_task(task_id: str) -> dict:
    """
    取消一个定时任务

    参数:
        task_id: 任务ID

    返回:
        操作结果字典
    """
    if not task_id:
        return {"success": False, "error": "任务ID不能为空"}

    if task_id not in _SCHEDULED_TASKS:
        return {
            "success": False,
            "error": f"任务不存在: {task_id}"
        }

    task_name = _SCHEDULED_TASKS[task_id].get("task_name")

    if task_id in _TASK_THREADS:
        try:
            _TASK_THREADS[task_id].cancel()
            del _TASK_THREADS[task_id]
        except Exception:
            pass

    del _SCHEDULED_TASKS[task_id]

    return {
        "success": True,
        "task_id": task_id,
        "task_name": task_name,
        "message": "任务已取消"
    }


def enable_task(task_id: str) -> dict:
    """
    启用一个定时任务

    参数:
        task_id: 任务ID

    返回:
        操作结果字典
    """
    if task_id not in _SCHEDULED_TASKS:
        return {
            "success": False,
            "error": f"任务不存在: {task_id}"
        }

    _SCHEDULED_TASKS[task_id]["enabled"] = True

    try:
        base_time = datetime.now()
        cron = croniter(_SCHEDULED_TASKS[task_id]["cron_expr"], base_time)
        next_run = cron.get_next(datetime)
        _SCHEDULED_TASKS[task_id]["next_run"] = next_run.isoformat()
    except Exception:
        pass

    return {
        "success": True,
        "task_id": task_id,
        "enabled": True,
        "message": "任务已启用"
    }


def disable_task(task_id: str) -> dict:
    """
    禁用一个定时任务

    参数:
        task_id: 任务ID

    返回:
        操作结果字典
    """
    if task_id not in _SCHEDULED_TASKS:
        return {
            "success": False,
            "error": f"任务不存在: {task_id}"
        }

    _SCHEDULED_TASKS[task_id]["enabled"] = False

    if task_id in _TASK_THREADS:
        try:
            _TASK_THREADS[task_id].cancel()
            del _TASK_THREADS[task_id]
        except Exception:
            pass

    return {
        "success": True,
        "task_id": task_id,
        "enabled": False,
        "message": "任务已禁用"
    }


def get_next_run_times(cron_expr: str, count: int = 5) -> list:
    """
    获取Cron表达式接下来的多次执行时间

    参数:
        cron_expr: Cron表达式
        count: 返回的时间点数量

    返回:
        时间点列表
    """
    try:
        base_time = datetime.now()
        cron = croniter(cron_expr, base_time)

        run_times = []
        for _ in range(count):
            next_time = cron.get_next(datetime)
            run_times.append(next_time.isoformat())

        return run_times

    except Exception:
        return []


def validate_cron_expr(cron_expr: str) -> dict:
    """
    验证Cron表达式是否有效

    参数:
        cron_expr: Cron表达式

    返回:
        验证结果字典
    """
    try:
        base_time = datetime.now()
        cron = croniter(cron_expr, base_time)

        next_time = cron.get_next(datetime)

        return {
            "valid": True,
            "next_run": next_time.isoformat(),
            "cron_expr": cron_expr
        }

    except (ValueError, KeyError) as e:
        return {
            "valid": False,
            "error": str(e),
            "cron_expr": cron_expr
        }
