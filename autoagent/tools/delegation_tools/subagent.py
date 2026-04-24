"""
子代理管理工具 - 创建、列出和终止子代理
"""

import os
import uuid
import time
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


_SUBAGENTS = {}
_SUBAGENT_COUNTER = 0


def spawn_subagent(task: str, config: dict = None) -> dict:
    """
    创建一个子代理来执行任务

    参数:
        task: 子代理要执行的任务描述
        config: 子代理配置 (可选)
            - name: 子代理名称
            - model: 使用的模型
            - timeout: 超时时间(秒)
            - priority: 优先级

    返回:
        包含子代理信息的字典
    """
    global _SUBAGENT_COUNTER

    if not task or not task.strip():
        return {"success": False, "error": "任务描述不能为空"}

    subagent_id = f"subagent_{uuid.uuid4().hex[:8]}"
    _SUBAGENT_COUNTER += 1

    name = config.get("name", f"Agent-{_SUBAGENT_COUNTER}") if config else f"Agent-{_SUBAGENT_COUNTER}"
    model = config.get("model", "gpt-4o") if config else "gpt-4o"
    timeout = config.get("timeout", 300) if config else 300
    priority = config.get("priority", "normal") if config else "normal"

    subagent_info = {
        "id": subagent_id,
        "name": name,
        "task": task,
        "model": model,
        "timeout": timeout,
        "priority": priority,
        "status": "initializing",
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None,
        "progress": 0
    }

    _SUBAGENTS[subagent_id] = subagent_info

    thread = threading.Thread(
        target=_run_subagent_task,
        args=(subagent_id, task, model, timeout),
        daemon=True
    )
    thread.start()

    subagent_info["status"] = "running"
    subagent_info["started_at"] = datetime.now().isoformat()

    return {
        "success": True,
        "subagent_id": subagent_id,
        "name": name,
        "status": "running",
        "message": f"子代理 {name} 已启动"
    }


def _run_subagent_task(subagent_id: str, task: str, model: str, timeout: int):
    """在新线程中执行子代理任务"""
    if subagent_id not in _SUBAGENTS:
        return

    start_time = time.time()

    try:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            _SUBAGENTS[subagent_id]["status"] = "failed"
            _SUBAGENTS[subagent_id]["error"] = "未配置OPENAI_API_KEY"
            return

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        except ImportError:
            _SUBAGENTS[subagent_id]["status"] = "failed"
            _SUBAGENTS[subagent_id]["error"] = "OpenAI库未安装"
            return

        _SUBAGENTS[subagent_id]["progress"] = 25

        messages = [
            {
                "role": "system",
                "content": "你是一个专门执行任务的AI子代理。请仔细理解任务要求，并给出完整的执行结果。"
            },
            {
                "role": "user",
                "content": task
            }
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=4000
        )

        _SUBAGENTS[subagent_id]["progress"] = 75

        result = response.choices[0].message.content

        elapsed = time.time() - start_time

        _SUBAGENTS[subagent_id]["status"] = "completed"
        _SUBAGENTS[subagent_id]["result"] = result
        _SUBAGENTS[subagent_id]["completed_at"] = datetime.now().isoformat()
        _SUBAGENTS[subagent_id]["progress"] = 100
        _SUBAGENTS[subagent_id]["elapsed_time"] = round(elapsed, 2)

    except Exception as e:
        _SUBAGENTS[subagent_id]["status"] = "failed"
        _SUBAGENTS[subagent_id]["error"] = str(e)
        _SUBAGENTS[subagent_id]["completed_at"] = datetime.now().isoformat()


def list_subagents() -> dict:
    """
    列出所有子代理

    返回:
        包含子代理列表的字典
    """
    subagents = []

    for subagent_id, info in _SUBAGENTS.items():
        subagents.append({
            "id": info.get("id"),
            "name": info.get("name"),
            "task": info.get("task"),
            "status": info.get("status"),
            "progress": info.get("progress", 0),
            "priority": info.get("priority"),
            "created_at": info.get("created_at"),
            "started_at": info.get("started_at"),
            "completed_at": info.get("completed_at"),
            "elapsed_time": info.get("elapsed_time")
        })

    subagents.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    running = len([s for s in subagents if s.get("status") == "running"])
    completed = len([s for s in subagents if s.get("status") == "completed"])
    failed = len([s for s in subagents if s.get("status") == "failed"])

    return {
        "success": True,
        "subagents": subagents,
        "total": len(subagents),
        "running": running,
        "completed": completed,
        "failed": failed
    }


def terminate_subagent(subagent_id: str) -> dict:
    """
    终止一个子代理

    参数:
        subagent_id: 子代理ID

    返回:
        操作结果字典
    """
    if not subagent_id:
        return {"success": False, "error": "子代理ID不能为空"}

    if subagent_id not in _SUBAGENTS:
        return {
            "success": False,
            "error": f"子代理不存在: {subagent_id}"
        }

    info = _SUBAGENTS[subagent_id]

    if info.get("status") == "completed":
        return {
            "success": False,
            "error": "子代理已完成，无法终止"
        }

    if info.get("status") == "failed":
        return {
            "success": False,
            "error": "子代理已失败，无法终止"
        }

    info["status"] = "terminated"
    info["completed_at"] = datetime.now().isoformat()

    return {
        "success": True,
        "subagent_id": subagent_id,
        "name": info.get("name"),
        "message": "子代理已终止"
    }


def get_subagent_status(subagent_id: str) -> dict:
    """
    获取子代理状态

    参数:
        subagent_id: 子代理ID

    返回:
        子代理状态字典
    """
    if subagent_id not in _SUBAGENTS:
        return {
            "success": False,
            "error": f"子代理不存在: {subagent_id}"
        }

    info = _SUBAGENTS[subagent_id]

    return {
        "success": True,
        "id": info.get("id"),
        "name": info.get("name"),
        "status": info.get("status"),
        "progress": info.get("progress", 0),
        "result": info.get("result"),
        "error": info.get("error"),
        "created_at": info.get("created_at"),
        "completed_at": info.get("completed_at")
    }


def cleanup_completed_subagents(keep_recent: int = 10) -> dict:
    """
    清理已完成的子代理记录

    参数:
        keep_recent: 保留最近N条记录

    返回:
        清理结果字典
    """
    completed_ids = [
        sid for sid, info in _SUBAGENTS.items()
        if info.get("status") in ["completed", "failed", "terminated"]
    ]

    completed_ids.sort(
        key=lambda sid: _SUBAGENTS[sid].get("completed_at", ""),
        reverse=True
    )

    to_remove = completed_ids[keep_recent:]
    removed_count = 0

    for sid in to_remove:
        del _SUBAGENTS[sid]
        removed_count += 1

    return {
        "success": True,
        "removed_count": removed_count,
        "remaining_count": len(_SUBAGENTS)
    }
