from typing import Any, Optional
from ..memory.memory_manager import MemoryManager
from ..skills.skill_manager import SkillManager
from ..utils.logger import get_logger

logger = get_logger("context_builder")


class ContextBuilder:
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        skill_manager: Optional[SkillManager] = None,
    ):
        self.memory_manager = memory_manager
        self.skill_manager = skill_manager

    def build_system_prompt(self) -> str:
        system_parts = []

        system_parts.append("你是一个智能AI助手，能够帮助用户完成各种任务。")

        if self.skill_manager:
            skills = self.skill_manager.list_skills()
            if skills:
                skill_descriptions = [f"- {s.get('name', '未知')}: {s.get('description', '')}" for s in skills[:10]]
                system_parts.append("\n可用技能:\n" + "\n".join(skill_descriptions))

        return "\n\n".join(system_parts)

    def build_conversation_context(self, messages: list[dict[str, Any]]) -> str:
        if not messages:
            return ""

        context_lines = ["## 对话历史\n"]

        for msg in messages[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_lines.append(f"**{role}**: {content}")

        return "\n".join(context_lines)

    def build_memory_context(self, query: str) -> str:
        if not self.memory_manager:
            return ""

        try:
            memories = self.memory_manager.recall(query, limit=5)
            if not memories:
                return ""

            memory_lines = ["## 相关记忆\n"]
            for mem in memories:
                mem_type = mem.memory_type.value if hasattr(mem.memory_type, 'value') else str(mem.memory_type)
                memory_lines.append(f"- [{mem_type}] {mem.content}")

            return "\n".join(memory_lines)
        except Exception as e:
            logger.warning(f"Failed to build memory context: {e}")
            return ""

    def build_skill_context(self, task: str) -> str:
        if not self.skill_manager:
            return ""

        try:
            relevant_skills = self.skill_manager.find_relevant_skills(task)
            if not relevant_skills:
                return ""

            skill_lines = ["## 相关技能\n"]
            for skill in relevant_skills[:3]:
                name = skill.get("name", "未知")
                desc = skill.get("description", "")
                trigger = skill.get("trigger", "")
                skill_lines.append(f"- **{name}**: {desc}")
                if trigger:
                    skill_lines.append(f"  触发词: {trigger}")

            return "\n".join(skill_lines)
        except Exception as e:
            logger.warning(f"Failed to build skill context: {e}")
            return ""

    def build_full_context(
        self,
        messages: Optional[list[dict[str, Any]]] = None,
        query: Optional[str] = None,
        task: Optional[str] = None,
    ) -> dict[str, Any]:
        context = {
            "system_prompt": self.build_system_prompt(),
            "conversation_context": "",
            "memory_context": "",
            "skill_context": "",
        }

        if messages:
            context["conversation_context"] = self.build_conversation_context(messages)

        if query:
            context["memory_context"] = self.build_memory_context(query)

        if task:
            context["skill_context"] = self.build_skill_context(task)

        return context
