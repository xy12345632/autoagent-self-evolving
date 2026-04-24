import pytest
from datetime import datetime
from autoagent.memory.schemas import MemoryEntry, MemoryType


class TestMemoryEntry:
    def test_create_memory_entry(self):
        entry = MemoryEntry(
            content="测试内容",
            memory_type=MemoryType.CONTEXT
        )
        assert entry.content == "测试内容"
        assert entry.memory_type == MemoryType.CONTEXT
        assert entry.importance == 5
        assert entry.is_archived is False
        assert entry.created_at is not None
        assert entry.updated_at is not None

    def test_memory_entry_with_custom_importance(self):
        entry = MemoryEntry(
            content="重要记忆",
            memory_type=MemoryType.KNOWLEDGE,
            importance=10
        )
        assert entry.importance == 10

    def test_memory_entry_to_dict(self, memory_entry):
        result = memory_entry.to_dict()
        assert result["id"] == 1
        assert result["content"] == "测试记忆内容"
        assert result["memory_type"] == "context"
        assert result["metadata"] == {"source": "test"}
        assert result["importance"] == 5
        assert result["is_archived"] is False

    def test_memory_entry_from_dict(self):
        data = {
            "id": 10,
            "content": "从字典创建",
            "memory_type": "knowledge",
            "metadata": {"domain": "ai"},
            "importance": 9,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "is_archived": False
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.id == 10
        assert entry.content == "从字典创建"
        assert entry.memory_type == MemoryType.KNOWLEDGE
        assert entry.metadata == {"domain": "ai"}
        assert entry.importance == 9

    def test_memory_entry_roundtrip(self):
        original = MemoryEntry(
            content="往返测试",
            memory_type=MemoryType.PREFERENCE,
            metadata={"key": "value"},
            importance=7
        )
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored.content == original.content
        assert restored.memory_type == original.memory_type
        assert restored.metadata == original.metadata
        assert restored.importance == original.importance

    def test_memory_entry_update_timestamp(self):
        entry = MemoryEntry(content="原始内容")
        original_updated = entry.updated_at
        entry.content = "修改内容"
        assert entry.updated_at >= original_updated

    def test_memory_entry_archived_flag(self):
        entry = MemoryEntry(content="待归档内容")
        assert entry.is_archived is False
        entry.is_archived = True
        assert entry.is_archived is True


class TestMemoryType:
    def test_memory_type_values(self):
        assert MemoryType.KNOWLEDGE.value == "knowledge"
        assert MemoryType.PREFERENCE.value == "preference"
        assert MemoryType.CONTEXT.value == "context"
        assert MemoryType.SKILL.value == "skill"

    def test_memory_type_from_string(self):
        entry = MemoryEntry.from_dict({
            "content": "test",
            "memory_type": "knowledge"
        })
        assert entry.memory_type == MemoryType.KNOWLEDGE

    def test_memory_type_default(self):
        entry = MemoryEntry.from_dict({"content": "test"})
        assert entry.memory_type == MemoryType.CONTEXT


class TestMemoryIntegration:
    def test_multiple_memory_entries(self):
        entries = [
            MemoryEntry(id=i, content=f"记忆{i}", memory_type=MemoryType.CONTEXT)
            for i in range(5)
        ]
        assert len(entries) == 5
        assert all(e.id is not None for e in entries)

    def test_memory_importance_filtering(self):
        entries = [
            MemoryEntry(content=f"记忆{i}", importance=i)
            for i in range(1, 11)
        ]
        high_importance = [e for e in entries if e.importance >= 8]
        assert len(high_importance) == 3

    def test_memory_type_filtering(self):
        entries = [
            MemoryEntry(content="知识", memory_type=MemoryType.KNOWLEDGE),
            MemoryEntry(content="偏好", memory_type=MemoryType.PREFERENCE),
            MemoryEntry(content="上下文", memory_type=MemoryType.CONTEXT),
        ]
        knowledge_entries = [
            e for e in entries if e.memory_type == MemoryType.KNOWLEDGE
        ]
        assert len(knowledge_entries) == 1
        assert knowledge_entries[0].content == "知识"
