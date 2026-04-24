import pytest
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from autoagent.memory.schemas import MemoryEntry, MemoryType


@pytest.fixture
def memory_entry():
    return MemoryEntry(
        id=1,
        content="测试记忆内容",
        memory_type=MemoryType.CONTEXT,
        metadata={"source": "test"},
        importance=5
    )


@pytest.fixture
def knowledge_entry():
    return MemoryEntry(
        id=2,
        content="知识库条目",
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"domain": "programming"},
        importance=8
    )


@pytest.fixture
def preference_entry():
    return MemoryEntry(
        id=3,
        content="用户偏好",
        memory_type=MemoryType.PREFERENCE,
        metadata={"category": "ui"},
        importance=6
    )


@pytest.fixture
def mock_memory_store():
    mock = MagicMock()
    mock.get_all.return_value = []
    mock.add.return_value = True
    mock.update.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_skill_store():
    mock = MagicMock()
    mock.list_skills.return_value = []
    mock.get_skill.return_value = None
    mock.create_skill.return_value = "skill_001"
    mock.search_skills.return_value = []
    return mock


@pytest.fixture
def mock_tool_registry():
    from autoagent.tools.tool_registry import ToolRegistry
    registry = ToolRegistry()
    registry.clear()
    return registry


@pytest.fixture
def sample_skill_data():
    return {
        "id": "test_skill_001",
        "name": "测试技能",
        "description": "用于测试的技能",
        "trigger": ["测试", "test"],
        "action": {"type": "function", "function": "test_func"},
        "category": "testing",
        "usage_count": 0,
        "success_rate": 1.0
    }


@pytest.fixture
def sample_tool_schema():
    return {
        "name": "test_tool",
        "description": "测试工具",
        "category": "testing",
        "parameters": {
            "input": {"type": "string", "required": True}
        }
    }


@pytest.fixture
def mock_config():
    return {
        "model_providers": {
            "opencode_zen": {
                "model": "test-model",
                "temperature": 0.7
            }
        },
        "memory": {
            "storage_path": "data/memory.json",
            "max_entries": 1000
        },
        "skills": {
            "skills_dir": "skills/",
            "storage_path": "data/skills.json"
        },
        "gateway": {
            "telegram": {"enabled": False},
            "discord": {"enabled": False}
        },
        "tools": {
            "web_tools": {"enabled": True},
            "system_tools": {"enabled": True}
        }
    }


@pytest.fixture
def temp_config_file(mock_config):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        import yaml
        yaml.dump(mock_config, f)
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def reset_singletons(mock_config):
    from autoagent.tools.tool_registry import ToolRegistry
    from autoagent.config.config_manager import ConfigManager

    ToolRegistry._instance = None
    ConfigManager._instance = None
    ConfigManager._config = {}

    with patch('autoagent.utils.paths.GlobalPaths.ensure_directories'):
        yield

    ToolRegistry._instance = None
    ConfigManager._instance = None
    ConfigManager._config = {}
