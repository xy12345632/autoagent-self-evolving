import uuid
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime


class SkillStore:
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(__file__).parent / 'store'
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        index_file = self.storage_path / 'index.json'
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
                for skill_id in index.get('skills', []):
                    skill_file = self.storage_path / f'{skill_id}.json'
                    if skill_file.exists():
                        with open(skill_file, 'r', encoding='utf-8') as sf:
                            self._skills[skill_id] = json.load(sf)

    def _save_to_disk(self, skill_id: str) -> None:
        skill_file = self.storage_path / f'{skill_id}.json'
        with open(skill_file, 'w', encoding='utf-8') as f:
            json.dump(self._skills[skill_id], f, ensure_ascii=False, indent=2)
        self._update_index()

    def _update_index(self) -> None:
        index = {'skills': list(self._skills.keys())}
        index_file = self.storage_path / 'index.json'
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def create_skill(self, skill_data: Dict[str, Any]) -> str:
        skill_id = skill_data.get('id') or str(uuid.uuid4())[:8]
        if skill_id in self._skills:
            raise ValueError(f"Skill with id {skill_id} already exists")

        skill_record = {
            'id': skill_id,
            'name': skill_data['name'],
            'description': skill_data.get('description', ''),
            'category': skill_data.get('category', 'general'),
            'tags': skill_data.get('tags', []),
            'trigger': skill_data.get('trigger', ''),
            'action': skill_data.get('action', []),
            'examples': skill_data.get('examples', []),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'usage_count': 0,
            'success_rate': 1.0
        }

        self._skills[skill_id] = skill_record
        self._save_to_disk(skill_id)
        return skill_id

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        return self._skills.get(skill_id)

    def list_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.get('category') == category]
        return sorted(skills, key=lambda x: x.get('usage_count', 0), reverse=True)

    def search_skills(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        for skill in self._skills.values():
            if (query_lower in skill.get('name', '').lower() or
                query_lower in skill.get('description', '').lower() or
                query_lower in skill.get('trigger', '').lower() or
                any(query_lower in tag.lower() for tag in skill.get('tags', []))):
                results.append(skill)
        return sorted(results, key=lambda x: x.get('usage_count', 0), reverse=True)

    def update_skill(self, skill_id: str, skill_data: Dict[str, Any]) -> bool:
        if skill_id not in self._skills:
            return False

        existing = self._skills[skill_id]
        updated = {
            'id': skill_id,
            'name': skill_data.get('name', existing['name']),
            'description': skill_data.get('description', existing['description']),
            'category': skill_data.get('category', existing['category']),
            'tags': skill_data.get('tags', existing['tags']),
            'trigger': skill_data.get('trigger', existing['trigger']),
            'action': skill_data.get('action', existing['action']),
            'examples': skill_data.get('examples', existing['examples']),
            'created_at': existing['created_at'],
            'updated_at': datetime.now().isoformat(),
            'usage_count': skill_data.get('usage_count', existing['usage_count']),
            'success_rate': skill_data.get('success_rate', existing['success_rate'])
        }

        self._skills[skill_id] = updated
        self._save_to_disk(skill_id)
        return True

    def delete_skill(self, skill_id: str) -> bool:
        if skill_id not in self._skills:
            return False

        del self._skills[skill_id]
        skill_file = self.storage_path / f'{skill_id}.json'
        if skill_file.exists():
            skill_file.unlink()
        self._update_index()
        return True

    def increment_usage(self, skill_id: str) -> None:
        if skill_id in self._skills:
            self._skills[skill_id]['usage_count'] += 1
            self._save_to_disk(skill_id)

    def update_success_rate(self, skill_id: str, success: bool) -> None:
        if skill_id not in self._skills:
            return

        skill = self._skills[skill_id]
        total = skill['usage_count'] + 1
        current_successes = skill['success_rate'] * skill['usage_count']
        new_successes = current_successes + (1 if success else 0)
        skill['success_rate'] = new_successes / total
        self._save_to_disk(skill_id)
