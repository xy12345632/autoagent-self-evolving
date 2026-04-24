import re
from typing import Dict, Any, Optional, List


class SkillCreator:
    COMPLEXITY_INDICATORS = [
        r'\b(?:首先|然后|接着|最后|其次)\b.*?(?:然后|接着)',
        r'\b\d+\s*个\s*(?:步骤|阶段|环节)\b',
        r'\b(?:需要|应该|必须)\s*(?:先|再)\b',
        r'\b(?:完成|实现|达到)\b.*?\b(?:需要|必须)\b',
        r'```',
        r'\b(?:具体|详细)\s*(?:步骤|流程|方法)\b'
    ]

    def detect_complex_task(self, conversation: str) -> bool:
        for pattern in self.COMPLEXITY_INDICATORS:
            if re.search(pattern, conversation):
                return True
        return False

    def create_skill_from_solution(
        self,
        problem: str,
        solution: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        skill_name = self._extract_skill_name(problem, context)
        skill_trigger = self._generate_trigger(problem)
        skill_action = self._parse_solution_steps(solution)
        skill_category = self._infer_category(problem, context)
        skill_tags = self._extract_tags(problem, solution, context)

        return {
            'name': skill_name,
            'description': self._generate_description(problem, solution),
            'category': skill_category,
            'tags': skill_tags,
            'trigger': skill_trigger,
            'action': skill_action,
            'examples': self._generate_examples(problem, solution)
        }

    def _extract_skill_name(self, problem: str, context: Optional[Dict[str, Any]]) -> str:
        if context and 'skill_name' in context:
            return context['skill_name']

        problem_clean = re.sub(r'[^\w\s\u4e00-\u9fff]', '', problem)
        words = problem_clean.split()
        if len(words) <= 5:
            return problem_clean
        return ' '.join(words[:5])

    def _generate_trigger(self, problem: str) -> str:
        lines = problem.strip().split('\n')
        trigger_lines = []
        for line in lines[:3]:
            line = line.strip()
            if line and len(line) > 5:
                trigger_lines.append(line)
                if len(trigger_lines) >= 2:
                    break
        return '\n'.join(trigger_lines)

    def _parse_solution_steps(self, solution: str) -> List[Dict[str, Any]]:
        steps = []
        step_pattern = re.compile(r'^(\d+)[.、)\]]\s*(.+)$', re.MULTILINE)
        current_step = None
        current_content = []

        for line in solution.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            match = step_pattern.match(line)
            if match:
                if current_step is not None:
                    steps.append({
                        'step': current_step,
                        'content': '\n'.join(current_content).strip()
                    })
                current_step = int(match.group(1))
                current_content = [match.group(2)]
            elif current_step is not None:
                if line.startswith('- ') or line.startswith('* '):
                    current_content.append(line[2:])
                else:
                    current_content.append(line)

        if current_step is not None:
            steps.append({
                'step': current_step,
                'content': '\n'.join(current_content).strip()
            })

        if not steps:
            steps = [{
                'step': 1,
                'content': solution.strip()
            }]

        return steps

    def _infer_category(self, problem: str, context: Optional[Dict[str, Any]]) -> str:
        if context and 'category' in context:
            return context['category']

        problem_lower = problem.lower()
        category_keywords = {
            'coding': ['代码', '编程', '函数', '实现', 'bug', 'code', 'programming'],
            'writing': ['写作', '文章', '文档', '撰写', 'write', 'document'],
            'analysis': ['分析', '研究', '调查', '分析', 'analyze', 'research'],
            'design': ['设计', '规划', '方案', 'design', 'plan'],
            'data': ['数据', '处理', '分析', 'data', 'process']
        }

        for category, keywords in category_keywords.items():
            if any(kw in problem_lower for kw in keywords):
                return category

        return 'general'

    def _extract_tags(
        self,
        problem: str,
        solution: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        tags = set()

        if context and 'tags' in context:
            tags.update(context['tags'])

        all_text = f"{problem} {solution}"
        tech_patterns = [
            r'\b(?:Python|JavaScript|TypeScript|Java|Go|Rust|C\+\+|React|Vue|Angular)\b',
            r'\b(?:API|HTTP|REST|GraphQL|SQL|NoSQL|MongoDB|PostgreSQL)\b',
            r'\b(?:Git|Docker|Kubernetes|AWS|Azure|GCP)\b',
            r'\b(?:AI|ML|LLM|NLP|GPT|Transformer)\b'
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            tags.update(m.lower() for m in matches)

        return list(tags)[:10]

    def _generate_description(self, problem: str, solution: str) -> str:
        problem_summary = problem[:100]
        if len(problem) > 100:
            problem_summary += '...'
        return f"解决 {problem_summary}"

    def _generate_examples(self, problem: str, solution: str) -> List[Dict[str, Any]]:
        return [{
            'title': '典型场景',
            'content': f"问题：{problem[:200]}\n\n解决方案：{solution[:200]}"
        }]

    def improve_skill(
        self,
        skill_id: str,
        feedback: Dict[str, Any],
        current_skill: Dict[str, Any]
    ) -> Dict[str, Any]:
        improved = current_skill.copy()

        if 'additional_steps' in feedback:
            existing_steps = current_skill.get('action', [])
            next_step = len(existing_steps) + 1
            for step in feedback['additional_steps']:
                step['step'] = next_step
                existing_steps.append(step)
                next_step += 1
            improved['action'] = existing_steps

        if 'better_trigger' in feedback:
            improved['trigger'] = feedback['better_trigger']

        if 'new_tags' in feedback:
            existing_tags = set(current_skill.get('tags', []))
            existing_tags.update(feedback['new_tags'])
            improved['tags'] = list(existing_tags)

        if 'success_rate' in feedback:
            improved['success_rate'] = feedback['success_rate']

        return improved

    def generate_skill_content(
        self,
        problem: str,
        steps: List[str],
        result: Optional[str] = None
    ) -> str:
        content_lines = [
            f"# {self._extract_skill_name(problem, None)}",
            "",
            "## 触发条件",
            problem,
            "",
            "## 操作",
        ]

        for i, step in enumerate(steps, 1):
            content_lines.append(f"{i}. {step}")

        if result:
            content_lines.extend([
                "",
                "## 结果",
                result
            ])

        return '\n'.join(content_lines)
