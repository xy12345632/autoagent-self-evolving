"""
记忆管理工具 - 短期记忆、长期记忆和记忆摘要
"""

import os
import json
import uuid
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


_MEMORY_STORE = {}


def manage_memory(action: str, data: dict = None) -> dict:
    """
    管理AI记忆，支持保存、回忆、摘要和清除操作

    参数:
        action: 操作类型，支持: save, recall, summarize, clear
        data: 操作所需的数据
            - save: {{"key": str, "value": any, "memory_type": "short_term/long_term"}}
            - recall: {{"key": str}} 或 {{"query": str}}
            - summarize: {{"time_range": "today/week/all"}}
            - clear: {{"memory_type": "short_term/long_term/all"}}

    返回:
        包含操作结果的字典
    """
    global _MEMORY_STORE

    action = action.lower().strip()

    if action == "save":
        return _save_memory(data)
    elif action == "recall":
        return _recall_memory(data)
    elif action == "summarize":
        return _summarize_memory(data)
    elif action == "clear":
        return _clear_memory(data)
    else:
        return {
            "success": False,
            "error": f"不支持的操作: {action}，支持: save, recall, summarize, clear"
        }


def _save_memory(data: dict) -> dict:
    """保存记忆"""
    if not data:
        return {"success": False, "error": "保存数据不能为空"}

    key = data.get("key")
    value = data.get("value")
    memory_type = data.get("memory_type", "short_term")

    if not key:
        return {"success": False, "error": "记忆键(key)不能为空"}

    if value is None:
        return {"success": False, "error": "记忆值(value)不能为空"}

    memory_id = str(uuid.uuid4())
    timestamp = time.time()

    if memory_type not in _MEMORY_STORE:
        _MEMORY_STORE[memory_type] = {}

    _MEMORY_STORE[memory_type][key] = {
        "id": memory_id,
        "value": value,
        "timestamp": timestamp,
        "created_at": datetime.now().isoformat()
    }

    return {
        "success": True,
        "memory_id": memory_id,
        "key": key,
        "memory_type": memory_type,
        "message": f"记忆已保存到{memory_type}"
    }


def _recall_memory(data: dict) -> dict:
    """回忆记忆"""
    if not data:
        return {"success": False, "error": "查询条件不能为空"}

    key = data.get("key")
    query = data.get("query")
    memory_type = data.get("memory_type")

    results = []

    if key:
        if memory_type:
            if memory_type in _MEMORY_STORE and key in _MEMORY_STORE[memory_type]:
                results.append({
                    "key": key,
                    "value": _MEMORY_STORE[memory_type][key]["value"],
                    "memory_type": memory_type
                })
        else:
            for mtype, memories in _MEMORY_STORE.items():
                if key in memories:
                    results.append({
                        "key": key,
                        "value": memories[key]["value"],
                        "memory_type": mtype
                    })

    elif query:
        results = _semantic_recall(query, memory_type)

    return {
        "success": True,
        "results": results,
        "count": len(results)
    }


def _semantic_recall(query: str, memory_type: str = None) -> list:
    """基于语义的记忆检索"""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or not OPENAI_AVAILABLE:
        all_memories = []
        if memory_type:
            memories = _MEMORY_STORE.get(memory_type, {})
        else:
            memories = {}
            for mtype, mems in _MEMORY_STORE.items():
                memories.update(mems)

        for key, mem in memories.items():
            if query.lower() in str(mem["value"]).lower():
                all_memories.append({
                    "key": key,
                    "value": mem["value"],
                    "memory_type": mem.get("memory_type", "unknown")
                })
        return all_memories

    try:
        client = OpenAI(api_key=api_key)

        all_memories = []
        search_sources = []

        if memory_type:
            if memory_type in _MEMORY_STORE:
                for key, mem in _MEMORY_STORE[memory_type].items():
                    all_memories.append({
                        "key": key,
                        "value": mem["value"],
                        "memory_type": memory_type
                    })
                    search_sources.append(f"{key}: {mem['value']}")
        else:
            for mtype, memories in _MEMORY_STORE.items():
                for key, mem in memories.items():
                    all_memories.append({
                        "key": key,
                        "value": mem["value"],
                        "memory_type": mtype
                    })
                    search_sources.append(f"{key}: {mem['value']}")

        if not search_sources:
            return []

        context = "\n".join(search_sources)

        prompt = f"""给定查询: "{query}"

相关记忆:
{context}

请找出与查询最相关的记忆，返回JSON格式:
{{
    "relevant_memories": [
        {{"key": "...", "value": "...", "relevance": "high/medium/low"}}
    ]
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个记忆检索助手，从给定的记忆列表中找出与查询最相关的内容。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return result.get("relevant_memories", [])

    except Exception:
        return all_memories


def _summarize_memory(data: dict) -> dict:
    """记忆摘要"""
    time_range = data.get("time_range", "today") if data else "today"

    all_memories = []
    now = datetime.now()

    for mtype, memories in _MEMORY_STORE.items():
        for key, mem in memories.items():
            all_memories.append({
                "key": key,
                "value": mem["value"],
                "memory_type": mtype,
                "timestamp": mem.get("timestamp", 0)
            })

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or not OPENAI_AVAILABLE:
        return {
            "success": False,
            "error": "需要配置OPENAI_API_KEY来生成摘要"
        }

    try:
        client = OpenAI(api_key=api_key)

        memories_text = "\n".join([f"- {m['key']}: {m['value']}" for m in all_memories])

        prompt = f"""请总结以下记忆内容:

{memories_text}

时间范围: {time_range}

请用简洁的语言总结关键信息，返回JSON格式:
{{
    "summary": "摘要内容",
    "key_points": ["要点1", "要点2"],
    "memory_count": 记忆总数
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个记忆摘要助手，擅长从大量信息中提取关键要点。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return {
            "success": True,
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "memory_count": len(all_memories),
            "time_range": time_range
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"摘要生成失败: {str(e)}"
        }


def _clear_memory(data: dict) -> dict:
    """清除记忆"""
    global _MEMORY_STORE

    memory_type = data.get("memory_type", "all") if data else "all"

    if memory_type == "all":
        cleared_types = list(_MEMORY_STORE.keys())
        _MEMORY_STORE = {}
        return {
            "success": True,
            "message": "已清除所有记忆",
            "cleared_types": cleared_types
        }
    elif memory_type in _MEMORY_STORE:
        del _MEMORY_STORE[memory_type]
        return {
            "success": True,
            "message": f"已清除{memory_type}记忆",
            "cleared_types": [memory_type]
        }
    else:
        return {
            "success": True,
            "message": f"{memory_type}类型的记忆不存在或已清除",
            "cleared_types": []
        }


def get_memory_stats() -> dict:
    """获取记忆统计信息"""
    stats = {}
    total = 0

    for mtype, memories in _MEMORY_STORE.items():
        count = len(memories)
        stats[mtype] = count
        total += count

    return {
        "total_memories": total,
        "by_type": stats
    }
