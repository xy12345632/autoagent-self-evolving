import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from .skill_parser import SkillParser

logger = logging.getLogger(__name__)


class SkillLoader:
    SKILL_FILE_PATTERN = 'SKILL.md'

    def __init__(self, skills_dir: Optional[str] = None):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = Path(__file__).parent
        self.parser = SkillParser()
        self._discovered_skills: Dict[str, Dict[str, Any]] = {}
        self.discover_skills()

    def discover_skills(self) -> None:
        self._discovered_skills.clear()

        if not self.skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return

        for item in self.skills_dir.iterdir():
            if item.is_dir():
                skill_file = item / self.SKILL_FILE_PATTERN
                if skill_file.exists():
                    try:
                        skill_data = self.parser.parse_skill_file(str(skill_file))
                        skill_id = skill_data.get('id') or item.name
                        skill_data['id'] = skill_id
                        self._discovered_skills[skill_id] = skill_data
                        logger.info(f"Discovered skill: {skill_id}")
                    except Exception as e:
                        logger.error(f"Failed to parse skill file {skill_file}: {e}")

    def load_skill_definition(self, skill_id: str) -> Optional[Dict[str, Any]]:
        if skill_id in self._discovered_skills:
            return self._discovered_skills[skill_id]

        skill_dir = self.skills_dir / skill_id
        skill_file = skill_dir / self.SKILL_FILE_PATTERN

        if skill_file.exists():
            try:
                skill_data = self.parser.parse_skill_file(str(skill_file))
                skill_data['id'] = skill_id
                self._discovered_skills[skill_id] = skill_data
                return skill_data
            except Exception as e:
                logger.error(f"Failed to load skill {skill_id}: {e}")

        return None

    def reload_skills(self) -> None:
        logger.info("Reloading all skills...")
        self.discover_skills()

    def get_discovered_skills(self) -> Dict[str, Dict[str, Any]]:
        return self._discovered_skills.copy()

    def list_skill_ids(self) -> List[str]:
        return list(self._discovered_skills.keys())
