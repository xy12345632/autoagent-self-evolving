"""
SKILL.md 生成器 - 将技能导出为 Hermes 兼容格式
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime


class SkillExporter:
    """
    技能导出器

    将技能导出为 SKILL.md 格式，与 Hermes Agent 技能市场兼容
    """

    def __init__(self, export_dir: Optional[str] = None):
        if export_dir:
            self.export_dir = Path(export_dir)
        else:
            self.export_dir = Path(__file__).parent.parent.parent / "skills"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_skill(self, skill_data: Dict[str, Any]) -> str:
        """
        将单个技能导出为 SKILL.md 格式

        Args:
            skill_data: 技能数据字典

        Returns:
            导出的文件路径
        """
        skill_id = skill_data.get('id', 'unknown')
        filename = self._sanitize_filename(skill_data.get('name', skill_id))
        filepath = self.export_dir / f"{filename}.md"

        content = self._generate_skill_md(skill_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(filepath)

    def export_all_skills(self, skills: List[Dict[str, Any]]) -> List[str]:
        """
        导出所有技能

        Args:
            skills: 技能列表

        Returns:
            导出的文件路径列表
        """
        exported = []
        for skill in skills:
            try:
                path = self.export_skill(skill)
                exported.append(path)
            except Exception:
                continue
        return exported

    def _generate_skill_md(self, skill: Dict[str, Any]) -> str:
        """生成 SKILL.md 内容"""

        lines = [
            f"# {skill.get('name', 'Unnamed Skill')}",
            "",
            skill.get('description', ''),
            "",
            "## 触发条件",
            "```",
            skill.get('trigger', ''),
            "```",
            "",
            "## 动作",
        ]

        actions = skill.get('action', [])
        if isinstance(actions, list):
            for action in actions:
                if isinstance(action, dict):
                    step = action.get('step', '')
                    content = action.get('content', '')
                    lines.append(f"{step}. {content}")
                elif isinstance(action, str):
                    lines.append(f"- {action}")
        elif isinstance(actions, str):
            lines.append(actions)

        lines.extend([
            "",
            "## 示例",
        ])

        examples = skill.get('examples', [])
        if examples:
            for example in examples:
                if isinstance(example, dict):
                    lines.append(f"### {example.get('title', '示例')}")
                    lines.append(example.get('content', ''))
                elif isinstance(example, str):
                    lines.append(example)
        else:
            lines.append("暂无示例")

        lines.extend([
            "",
            "## 元数据",
            f"- **ID**: {skill.get('id', 'N/A')}",
            f"- **分类**: {skill.get('category', 'general')}",
            f"- **标签**: {', '.join(skill.get('tags', []))}",
            f"- **使用次数**: {skill.get('usage_count', 0)}",
            f"- **成功率**: {skill.get('success_rate', 0):.1%}",
            f"- **创建时间**: {skill.get('created_at', 'N/A')}",
            f"- **更新时间**: {skill.get('updated_at', 'N/A')}",
        ])

        return '\n'.join(lines)

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        keepchars = (' ', '.', '_', '-')
        return "".join(c if c.isalnum() or c in keepchars else "_" for c in name).strip()

    def generate_skill_index(self, skills: List[Dict[str, Any]]) -> str:
        """
        生成技能索引文件

        Returns:
            索引文件路径
        """
        index_path = self.export_dir / "SKILLS_INDEX.md"

        lines = [
            "# 可用技能索引",
            "",
            f"总计: {len(skills)} 个技能",
            "",
            "## 按分类",
            "",
        ]

        categories: Dict[str, List[Dict]] = {}
        for skill in skills:
            cat = skill.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(skill)

        for cat, cat_skills in sorted(categories.items()):
            lines.append(f"### {cat} ({len(cat_skills)})")
            for skill in cat_skills:
                lines.append(f"- **{skill.get('name')}**: {skill.get('description', '')[:50]}...")
            lines.append("")

        lines.extend([
            "---",
            "",
            f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])

        content = '\n'.join(lines)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(index_path)


class SkillImporter:
    """
    技能导入器

    从 SKILL.md 文件导入技能
    """

    def __init__(self):
        pass

    def parse_skill_md(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        解析 SKILL.md 文件

        Args:
            filepath: 文件路径

        Returns:
            技能数据字典
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._parse_content(content)
        except Exception:
            return None

    def _parse_content(self, content: str) -> Dict[str, Any]:
        """解析 SKILL.md 内容"""

        lines = content.split('\n')
        skill = {
            'id': '',
            'name': '',
            'description': '',
            'trigger': '',
            'action': [],
            'examples': [],
            'tags': [],
            'category': 'general',
            'usage_count': 0,
            'success_rate': 1.0,
        }

        current_section = None
        section_content = []

        for line in lines:
            line = line.strip()

            if line.startswith('# ') and current_section is None:
                skill['name'] = line[2:].strip()
                skill['id'] = skill['name'].lower().replace(' ', '_')[:16]
                continue

            if line.startswith('## '):
                if section_content and current_section:
                    self._process_section(skill, current_section, section_content)

                current_section = line[3:].strip().lower()
                section_content = []
                continue

            section_content.append(line)

        if current_section and section_content:
            self._process_section(skill, current_section, section_content)

        return skill

    def _process_section(
        self,
        skill: Dict[str, Any],
        section: str,
        content: List[str]
    ) -> None:
        """处理每个 section"""

        section_lower = section.lower()

        if '描述' in section or 'description' in section_lower:
            skill['description'] = ' '.join(content).strip()

        elif '触发' in section or 'trigger' in section_lower:
            clean_content = [l for l in content if l and not l.startswith('```')]
            skill['trigger'] = '\n'.join(clean_content).strip()

        elif '动作' in section or 'action' in section_lower:
            steps = []
            for line in content:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(('-', '*', '•')):
                    steps.append({'step': len(steps) + 1, 'content': line[1:].strip()})
                elif line[0].isdigit() and '.' in line[:3]:
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        steps.append({'step': int(parts[0]), 'content': parts[1].strip()})
                elif line.startswith('```'):
                    continue
                else:
                    steps.append({'step': len(steps) + 1, 'content': line})
            skill['action'] = steps

        elif '示例' in section or 'example' in section_lower:
            skill['examples'] = [{'title': '示例', 'content': '\n'.join(content)}]

        elif '元数据' in section or 'metadata' in section_lower:
            for line in content:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip().strip('*')

                    if '标签' in key or 'tag' in key:
                        skill['tags'] = [t.strip() for t in value.split(',')]
                    elif '分类' in key or 'category' in key:
                        skill['category'] = value
                    elif '使用' in key or 'usage' in key:
                        try:
                            skill['usage_count'] = int(value)
                        except ValueError:
                            pass
                    elif '成功' in key or 'success' in key:
                        try:
                            if '%' in value:
                                skill['success_rate'] = float(value.rstrip('%')) / 100
                            else:
                                skill['success_rate'] = float(value)
                        except ValueError:
                            pass
