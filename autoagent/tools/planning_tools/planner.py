"""
任务规划工具 - AI辅助的任务分解和规划
"""

import os
import json
import uuid
from typing import List, Optional, Dict, Any

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def plan_task(goal: str, constraints: list = None) -> dict:
    """
    将复杂目标分解为可执行的任务步骤

    参数:
        goal: 要完成的目标或任务描述
        constraints: 约束条件列表 (如时间、资源限制等)

    返回:
        包含任务分解结果的字典
    """
    if not goal or not goal.strip():
        return {"success": False, "error": "目标不能为空"}

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置OPENAI_API_KEY环境变量"
        }

    try:
        if not OPENAI_AVAILABLE:
            return {"success": False, "error": "OpenAI库未安装，请运行: pip install openai"}

        client = OpenAI(api_key=api_key)

        constraints_text = ""
        if constraints:
            constraints_text = "\n约束条件:\n" + "\n".join([f"- {c}" for c in constraints])

        prompt = f"""请将以下目标分解为具体的执行步骤。每个步骤应该:
1. 清晰描述要做什么
2. 包含预期的输入和输出
3. 标注可能的优先级

目标: {goal}
{constraints_text}

请以JSON格式返回任务列表，格式如下:
{{
    "tasks": [
        {{
            "id": "step_1",
            "title": "步骤标题",
            "description": "详细描述",
            "priority": "high/medium/low",
            "estimated_time": "预估时间",
            "dependencies": ["依赖的步骤id"]
        }}
    ],
    "summary": "整体规划摘要"
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的任务规划助手，擅长将复杂目标分解为可执行的步骤。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=2000
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return {
            "success": True,
            "goal": goal,
            "plan_id": str(uuid.uuid4())[:8],
            "tasks": result.get("tasks", []),
            "summary": result.get("summary", ""),
            "constraints": constraints or []
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "任务规划解析失败"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"任务规划失败: {str(e)}"
        }


def refine_plan(plan: dict, feedback: str) -> dict:
    """
    根据反馈优化现有计划

    参数:
        plan: 现有的计划字典
        feedback: 用户反馈或修改要求

    返回:
        包含优化后计划的字典
    """
    if not plan or not plan.get("success"):
        return {"success": False, "error": "无效的计划"}

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置OPENAI_API_KEY环境变量"
        }

    try:
        if not OPENAI_AVAILABLE:
            return {"success": False, "error": "OpenAI库未安装"}

        client = OpenAI(api_key=api_key)

        prompt = f"""现有计划:
{json.dumps(plan, ensure_ascii=False, indent=2)}

用户反馈: {feedback}

请根据用户反馈优化计划，返回优化后的JSON格式:
{{
    "tasks": [...],
    "summary": "..."
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的任务规划助手，根据反馈优化任务计划。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=2000
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return {
            "success": True,
            "original_plan_id": plan.get("plan_id"),
            "plan_id": str(uuid.uuid4())[:8],
            "tasks": result.get("tasks", []),
            "summary": result.get("summary", ""),
            "refined_based_on": feedback
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"计划优化失败: {str(e)}"
        }
