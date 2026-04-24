import pytest
from unittest.mock import MagicMock, patch
from autoagent.skills.skill_manager import SkillManager


class TestSkillManager:
    def test_skill_manager_init(self, mock_skill_store):
        manager = SkillManager()
        assert manager.store is not None
        assert manager.loader is not None
        assert manager.creator is not None
        assert manager._loaded_skills == {}

    def test_load_skill_from_store(self, mock_skill_store, sample_skill_data):
        mock_skill_store.get_skill.return_value = sample_skill_data
        manager = SkillManager()
        manager.store = mock_skill_store

        result = manager.load_skill("test_skill_001")
        assert result == sample_skill_data
        assert "test_skill_001" in manager._loaded_skills
        mock_skill_store.increment_usage.assert_called_once_with("test_skill_001")

    def test_load_skill_caching(self, mock_skill_store, sample_skill_data):
        mock_skill_store.get_skill.return_value = sample_skill_data
        manager = SkillManager()
        manager.store = mock_skill_store

        manager.load_skill("test_skill_001")
        manager.load_skill("test_skill_001")

        assert mock_skill_store.get_skill.call_count == 1

    def test_load_skill_not_found(self, mock_skill_store):
        mock_skill_store.get_skill.return_value = None
        manager = SkillManager()
        manager.store = mock_skill_store

        result = manager.load_skill("nonexistent")
        assert result is None

    def test_find_relevant_skills(self, mock_skill_store):
        skills = [
            {"id": "skill1", "name": "Python编程", "trigger": "python", "description": "Python相关任务", "usage_count": 5, "success_rate": 0.9},
            {"id": "skill2", "name": "JavaScript编程", "trigger": "javascript", "description": "JS相关任务", "usage_count": 3, "success_rate": 0.8},
            {"id": "skill3", "name": "文档写作", "trigger": "写作", "description": "写作帮助", "usage_count": 10, "success_rate": 1.0},
        ]
        mock_skill_store.list_skills.return_value = skills
        manager = SkillManager()
        manager.store = mock_skill_store

        result = manager.find_relevant_skills("帮我写Python代码")

        assert len(result) <= 5
        assert all(isinstance(s, dict) for s in result)

    def test_find_relevant_skills_empty_query(self, mock_skill_store):
        mock_skill_store.list_skills.return_value = []
        manager = SkillManager()
        manager.store = mock_skill_store

        result = manager.find_relevant_skills("")
        assert result == []

    def test_create_skill(self, mock_skill_store, sample_skill_data):
        mock_skill_store.create_skill.return_value = "new_skill_id"
        manager = SkillManager()
        manager.store = mock_skill_store

        skill_id = manager.create_skill(sample_skill_data)
        assert skill_id == "new_skill_id"
        mock_skill_store.create_skill.assert_called_once_with(sample_skill_data)

    def test_get_skill(self, mock_skill_store, sample_skill_data):
        mock_skill_store.get_skill.return_value = sample_skill_data
        manager = SkillManager()
        manager.store = mock_skill_store

        result = manager.get_skill("test_skill_001")
        assert result == sample_skill_data

    def test_list_skills(self, mock_skill_store, sample_skill_data):
        mock_skill_store.list_skills.return_value = [sample_skill_data]
        manager = SkillManager()
        manager.store = mock_skill_store

        result = manager.list_skills()
        assert len(result) == 1
        assert result[0]["id"] == "test_skill_001"

    def test_list_skills_by_category(self, mock_skill_store, sample_skill_data):
        mock_skill_store.list_skills.return_value = [sample_skill_data]
        manager = SkillManager()
        manager.store = mock_skill_store

        result = manager.list_skills(category="testing")
        assert len(result) == 1

    def test_search_skills(self, mock_skill_store, sample_skill_data):
        mock_skill_store.search_skills.return_value = [sample_skill_data]
        manager = SkillManager()
        manager.store = mock_skill_store

        result = manager.search_skills("测试")
        assert len(result) == 1

    def test_update_skill(self, mock_skill_store, sample_skill_data):
        mock_skill_store.update_skill.return_value = True
        manager = SkillManager()
        manager.store = mock_skill_store

        updated_data = {**sample_skill_data, "description": "更新后的描述"}
        result = manager.update_skill("test_skill_001", updated_data)
        assert result is True

    def test_delete_skill(self, mock_skill_store):
        mock_skill_store.delete_skill.return_value = True
        manager = SkillManager()
        manager.store = mock_skill_store
        manager._loaded_skills["test_skill_001"] = {}

        result = manager.delete_skill("test_skill_001")
        assert result is True
        assert "test_skill_001" not in manager._loaded_skills

    def test_reload_skills(self, mock_skill_store):
        manager = SkillManager()
        manager.store = mock_skill_store
        manager._loaded_skills = {"skill1": {}, "skill2": {}}

        manager.reload_skills()
        assert manager._loaded_skills == {}


class TestSkillCategories:
    def test_get_all_skill_categories(self, mock_skill_store):
        skills = [
            {"id": "s1", "category": "programming"},
            {"id": "s2", "category": "writing"},
            {"id": "s3", "category": "programming"},
        ]
        mock_skill_store.list_skills.return_value = skills
        manager = SkillManager()
        manager.store = mock_skill_store

        categories = manager.get_all_skill_categories()
        assert "programming" in categories
        assert "writing" in categories
        assert len(categories) == 2
