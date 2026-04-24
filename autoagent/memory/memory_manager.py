from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..utils.logger import get_logger
from ..api.router import ModelRouter
from .file_memory import MemoryFile
from .memory_store import MemoryStore
from .schemas import MemoryEntry, MemoryType
from .summarizer import MemorySummarizer

logger = get_logger("memory_manager")


class MemoryManager:
    def __init__(
        self,
        db_path: str = "./data/memory.db",
        memory_files_path: Optional[str] = None,
        model_router: Optional[ModelRouter] = None,
    ):
        self.store = MemoryStore(db_path)
        self.file_memory = MemoryFile(memory_files_path)
        self.summarizer = MemorySummarizer(model_router)
        self._importance_keywords = {
            "important", "必须", "记住", "关键", "重要", "不要忘记",
            "preference", "喜欢", "讨厌", "偏好", "always", "never",
        }
        self._skill_keywords = {
            "skill", "技能", "能力", "擅长", "会的", "会做", "能做什么",
        }

    def init_memory_files(self) -> dict[str, bool]:
        results = {}

        results["memory"] = self._init_file_if_empty(
            "memory",
            "# 记忆文件\n\n这是AI的持久记忆存储，记录重要信息、知识和经验。\n\n## 重要记忆\n\n"
        )

        results["user"] = self._init_file_if_empty(
            "user",
            "# 用户信息\n\n记录用户的个人信息、偏好设置和交互历史。\n\n## 基本信息\n\n"
        )

        results["soul"] = self._init_file_if_empty(
            "soul",
            "# 灵魂配置\n\n定义AI的核心性格、价值观、行为准则和沟通风格。\n\n## 性格特征\n\n"
        )

        logger.info(f"Memory files initialized: {results}")
        return results

    def _init_file_if_empty(self, file_type: str, default_content: str) -> bool:
        if not self.file_memory.file_exists(file_type):
            return self.file_memory.write(default_content, file_type)
        return True

    def add_knowledge(
        self, content: str, importance: int = 5, metadata: Optional[dict[str, Any]] = None
    ) -> int:
        memory_id = self.store.store_memory(
            content=content,
            memory_type=MemoryType.KNOWLEDGE,
            metadata=metadata,
            importance=importance,
        )
        logger.debug(f"Added knowledge: {content[:50]}...")
        return memory_id

    def add_preference(
        self, content: str, importance: int = 7, metadata: Optional[dict[str, Any]] = None
    ) -> int:
        memory_id = self.store.store_memory(
            content=content,
            memory_type=MemoryType.PREFERENCE,
            metadata=metadata,
            importance=importance,
        )
        logger.debug(f"Added preference: {content[:50]}...")
        return memory_id

    def add_context(
        self, content: str, importance: int = 5, metadata: Optional[dict[str, Any]] = None
    ) -> int:
        memory_id = self.store.store_memory(
            content=content,
            memory_type=MemoryType.CONTEXT,
            metadata=metadata,
            importance=importance,
        )
        logger.debug(f"Added context: {content[:50]}...")
        return memory_id

    def add_skill(
        self, content: str, importance: int = 6, metadata: Optional[dict[str, Any]] = None
    ) -> int:
        memory_id = self.store.store_memory(
            content=content,
            memory_type=MemoryType.SKILL,
            metadata=metadata,
            importance=importance,
        )
        logger.debug(f"Added skill: {content[:50]}...")
        return memory_id

    def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        results = self.store.search_memories(query, limit)
        logger.debug(f"Recalled {len(results)} memories for query: {query}")
        return results

    async def summarize_entry(self, memory_id: int, max_length: int = 200) -> str:
        entry = self.store.get_memory_by_id(memory_id)
        if not entry:
            return ""
        return await self.summarizer.summarize_entry(entry.content, max_length)

    async def summarize_all(self, theme: Optional[str] = None) -> str:
        memories = self.store.get_recent_memories(100)
        entries = [
            {
                "content": m.content,
                "timestamp": m.created_at.isoformat() if m.created_at else "unknown",
                "memory_type": m.memory_type.value,
                "importance": m.importance,
            }
            for m in memories
        ]
        return await self.summarizer.summarize_multiple(entries, theme)

    def compress_memories(self, max_count: int = 50) -> list[MemoryEntry]:
        all_memories = self.store.get_all_memories()
        memory_dicts = [
            {
                "content": m.content,
                "memory_type": m.memory_type.value,
                "importance": m.importance,
                "access_count": m.access_count or 0,
            }
            for m in all_memories
        ]
        compressed = self.summarizer.compress_memories(memory_dicts, max_count)
        compressed_contents = {c["content"] for c in compressed}
        return [m for m in all_memories if m.content in compressed_contents]

    def get_recent(self, limit: int = 20) -> list[MemoryEntry]:
        return self.store.get_recent_memories(limit)

    def get_by_type(self, memory_type: MemoryType, limit: int = 50) -> list[MemoryEntry]:
        return self.store.get_memories_by_type(memory_type, limit)

    def is_important(self, content: str) -> bool:
        content_lower = content.lower()
        importance_count = sum(
            1 for keyword in self._importance_keywords if keyword in content_lower
        )
        return importance_count >= 2

    def auto_save_context(
        self,
        user_input: Optional[str] = None,
        ai_response: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        if user_input:
            if self.is_important(user_input):
                self.add_context(
                    content=f"用户重要输入: {user_input}",
                    importance=7,
                    metadata={"source": "auto_save", **metadata},
                )

        if ai_response and self.is_important(ai_response):
            self.add_context(
                content=f"AI重要响应: {ai_response}",
                importance=6,
                metadata={"source": "auto_save", **metadata},
            )

    async def summarize_memories(
        self,
        memories: list[MemoryEntry],
        summary_type: str = "general",
    ) -> str:
        if not memories:
            return "没有可摘要的记忆。"

        memory_contents = "\n".join([
            f"- [{m.memory_type.value}] {m.content}" for m in memories
        ])

        prompt_map = {
            "general": f"请总结以下记忆的核心要点，提取共同主题和重要信息：\n{memory_contents}",
            "knowledge": f"请整理以下知识记忆，形成结构化的知识体系：\n{memory_contents}",
            "preference": f"请分析以下偏好记忆，提炼用户偏好和AI风格：\n{memory_contents}",
        }

        prompt = prompt_map.get(summary_type, prompt_map["general"])

        return await self._call_llm_summarize(prompt)

    async def _call_llm_summarize(self, prompt: str) -> str:
        return f"[模拟LLM摘要]\n{prompt[:100]}..."

    def update_memory(self, memory_id: int, content: str) -> bool:
        result = self.store.update_memory(memory_id, content)
        if result:
            logger.info(f"Updated memory {memory_id}")
        return result

    def delete_memory(self, memory_id: int) -> bool:
        result = self.store.delete_memory(memory_id)
        if result:
            logger.info(f"Deleted memory {memory_id}")
        return result

    def archive_memory(self, memory_id: int) -> bool:
        result = self.store.archive_memory(memory_id)
        if result:
            logger.info(f"Archived memory {memory_id}")
        return result

    def save_to_file(
        self,
        memories: list[MemoryEntry],
        file_type: str = "memory",
        title: str = "记忆摘要",
    ) -> bool:
        if not memories:
            return False

        content_lines = [f"## {title} | {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]

        for mem in memories:
            content_lines.append(f"\n### [{mem.memory_type.value}] {mem.created_at}\n")
            content_lines.append(f"{mem.content}\n")
            if mem.metadata:
                content_lines.append(f"**元数据**: {mem.metadata}\n")

        content = "".join(content_lines)
        return self.file_memory.append(content, file_type)

    def load_from_file(self, file_type: str = "memory") -> list[MemoryEntry]:
        parsed = self.file_memory.parse_memories(file_type)
        entries = []

        for item in parsed:
            entry = MemoryEntry(
                content=item.get("content", ""),
                memory_type=MemoryType.CONTEXT,
                metadata={"source": "file", "title": item.get("title", "")},
            )
            entries.append(entry)

        return entries

    def sync_to_file(self, file_type: str = "memory") -> bool:
        memories = self.get_recent(limit=100)
        memories_by_type = {}
        for mem in memories:
            type_name = mem.memory_type.value
            if type_name not in memories_by_type:
                memories_by_type[type_name] = []
            memories_by_type[type_name].append(mem)

        success = True
        for type_name, type_memories in memories_by_type.items():
            title = f"{type_name.title()} 记忆"
            if not self.save_to_file(type_memories, file_type, title):
                success = False

        if success:
            logger.info(f"Synced memories to {file_type} file")

        return success

    def get_stats(self) -> dict[str, Any]:
        db_stats = self.store.get_stats()
        file_stats = {
            "memory_file_exists": self.file_memory.file_exists("memory"),
            "user_file_exists": self.file_memory.file_exists("user"),
            "soul_file_exists": self.file_memory.file_exists("soul"),
        }
        return {**db_stats, **file_stats}
