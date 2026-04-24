import re
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path


class SkillParser:
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)', re.DOTALL)
    TRIGGER_PATTERN = re.compile(r'^###\s*触发条件\s*$', re.MULTILINE)
    ACTION_PATTERN = re.compile(r'^###\s*操作\s*$', re.MULTILINE)
    EXAMPLE_PATTERN = re.compile(r'^###\s*示例\s*$', re.MULTILINE)

    def parse_skill_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Skill file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.parse_skill_content(content)

    def parse_skill_content(self, content: str) -> Dict[str, Any]:
        frontmatter_match = self.FRONTMATTER_PATTERN.match(content)

        if frontmatter_match:
            frontmatter = self.parse_frontmatter(frontmatter_match.group(1))
            markdown_content = frontmatter_match.group(2)
        else:
            frontmatter = {}
            markdown_content = content

        markdown_data = self.parse_markdown(markdown_content)
        skill_data = {**frontmatter, **markdown_data}

        self.validate_skill(skill_data)
        return skill_data

    def parse_frontmatter(self, content: str) -> Dict[str, Any]:
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}")

    def parse_markdown(self, content: str) -> Dict[str, Any]:
        result = {}

        trigger_match = self._extract_section(content, self.TRIGGER_PATTERN, self.ACTION_PATTERN)
        if trigger_match:
            result['trigger'] = self._clean_markdown(trigger_match)

        action_match = self._extract_section(content, self.ACTION_PATTERN, self.EXAMPLE_PATTERN)
        if action_match:
            result['action'] = self._parse_action_steps(action_match)

        example_match = self._extract_section(content, self.EXAMPLE_PATTERN, None)
        if example_match:
            result['examples'] = self._parse_examples(example_match)

        return result

    def _extract_section(self, content: str, start_pattern: re.Pattern, end_pattern: Optional[re.Pattern]) -> Optional[str]:
        start_match = start_pattern.search(content)
        if not start_match:
            return None

        start_pos = start_match.end()
        if end_pattern:
            end_match = end_pattern.search(content, start_pos)
            if end_match:
                return content[start_pos:end_match.start()]
            return content[start_pos:]
        return content[start_pos:]

    def _clean_markdown(self, text: str) -> str:
        lines = text.strip().split('\n')
        cleaned = []
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                cleaned.append(line[2:])
            elif line:
                cleaned.append(line)
        return '\n'.join(cleaned)

    def _parse_action_steps(self, content: str) -> List[Dict[str, Any]]:
        steps = []
        current_step = None
        current_content = []

        for line in content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            step_match = re.match(r'^(\d+)\.\s+(.*)$', line)
            if step_match:
                if current_step is not None:
                    steps.append({
                        'step': current_step,
                        'content': '\n'.join(current_content).strip()
                    })
                current_step = int(step_match.group(1))
                current_content = [step_match.group(2)]
            elif current_step is not None:
                if line.startswith('- '):
                    current_content.append(line[2:])

        if current_step is not None:
            steps.append({
                'step': current_step,
                'content': '\n'.join(current_content).strip()
            })

        return steps

    def _parse_examples(self, content: str) -> List[Dict[str, Any]]:
        examples = []
        current_example = None
        current_content = []

        for line in content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith('**场景') or line.startswith('**示例'):
                if current_example is not None:
                    examples.append({
                        'title': current_example,
                        'content': '\n'.join(current_content).strip()
                    })
                current_example = line.replace('**', '')
                current_content = []
            else:
                current_content.append(line)

        if current_example is not None:
            examples.append({
                'title': current_example,
                'content': '\n'.join(current_content).strip()
            })

        return examples

    def validate_skill(self, skill_data: Dict[str, Any]) -> None:
        required_fields = ['name', 'description', 'trigger', 'action']
        for field in required_fields:
            if field not in skill_data or not skill_data[field]:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(skill_data.get('action', []), list):
            raise ValueError("Field 'action' must be a list of steps")

        if 'category' in skill_data and not isinstance(skill_data['category'], str):
            raise ValueError("Field 'category' must be a string")

        if 'tags' in skill_data and not isinstance(skill_data['tags'], list):
            raise ValueError("Field 'tags' must be a list")
