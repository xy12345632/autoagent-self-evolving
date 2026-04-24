"""
技能进化管理器 - 自动从任务中创建和优化技能
类似于 Hermes Agent 的闭环学习系统
"""

import re
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from .skill_creator import SkillCreator
from .skill_store import SkillStore


@dataclass
class TaskRecord:
    task_id: str
    problem: str
    solution: str
    tool_calls: List[Dict[str, Any]]
    success: bool
    created_at: str
    evaluation_score: float = 0.0
    feedback: Optional[Dict[str, Any]] = None


@dataclass
class SkillEvolutionConfig:
    auto_create_threshold: int = 3
    evaluation_interval: int = 15
    min_complexity_score: int = 2
    improvement_weight: float = 0.1
    max_skills_per_session: int = 5


class SkillEvolutionManager:
    """
    自动技能进化管理器

    功能:
    1. 任务完成检测 - 判断任务是否值得创建技能
    2. 技能自动创建 - 从成功任务中提炼可复用技能
    3. 技能自进化 - 根据使用反馈优化已有技能
    4. 定期评估 - 类似Hermes的每N次工具调用后评估
    """

    SUCCESS_PATTERNS = [
        r'完成|成功|搞定|好了|解决了',
        r'✅|✓|✔',
        r'已生成|已创建|已写入',
        r'结果如下|输出为',
    ]

    FAILURE_PATTERNS = [
        r'失败|错误|不行|无法',
        r'❌|✗',
        r'报错|异常',
        r'不存在|找不到',
    ]

    COMPLEXITY_INDICATORS = [
        r'\b(?:首先|然后|接着|最后|其次|接下来)\b',
        r'\b\d+\s*个\s*(?:步骤|阶段|环节)\b',
        r'\b(?:需要|应该|必须)\s*(?:先|再)\b',
        r'```[\s\S]+?```',
        r'\b(?:具体|详细)\s*(?:步骤|流程|方法)\b',
        r'\b(?:循环|递归|并发|异步)\b',
    ]

    def __init__(
        self,
        skill_store: SkillStore,
        skill_creator: SkillCreator,
        config: Optional[SkillEvolutionConfig] = None
    ):
        self.skill_store = skill_store
        self.skill_creator = skill_creator
        self.config = config or SkillEvolutionConfig()

        self._task_records: Dict[str, TaskRecord] = {}
        self._tool_call_count: int = 0
        self._session_task_count: int = 0
        self._created_this_session: int = 0

    def record_tool_call(self) -> int:
        """记录工具调用，返回当前计数"""
        self._tool_call_count += 1
        return self._tool_call_count

    def should_evaluate(self) -> bool:
        """检查是否应该进行定期评估"""
        return self._tool_call_count >= self.config.evaluation_interval

    def reset_evaluation_cycle(self) -> None:
        """重置评估周期"""
        self._tool_call_count = 0

    def record_task(
        self,
        problem: str,
        solution: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        success: bool = True
    ) -> str:
        """
        记录一个任务

        Args:
            problem: 用户问题/任务描述
            solution: AI给出的解决方案
            tool_calls: 使用的工具调用列表
            success: 任务是否成功完成

        Returns:
            task_id: 任务记录ID
        """
        task_id = str(uuid.uuid4())[:8]
        complexity = self._evaluate_complexity(problem, solution, tool_calls)

        record = TaskRecord(
            task_id=task_id,
            problem=problem,
            solution=solution,
            tool_calls=tool_calls or [],
            success=success,
            created_at=datetime.now().isoformat(),
            evaluation_score=complexity
        )

        self._task_records[task_id] = record
        self._session_task_count += 1

        return task_id

    def should_auto_create_skill(self, task_id: str) -> bool:
        """
        判断任务是否应该自动创建技能

        Args:
            task_id: 任务记录ID

        Returns:
            True if skill should be created
        """
        if self._created_this_session >= self.config.max_skills_per_session:
            return False

        if task_id not in self._task_records:
            return False

        record = self._task_records[task_id]

        if not record.success:
            return False

        if record.evaluation_score < self.config.min_complexity_score:
            return False

        existing = self._find_similar_skill(record.problem)
        if existing:
            self._update_skill_with_feedback(existing, record)
            return False

        return True

    def auto_create_skill(self, task_id: str) -> Optional[str]:
        """
        自动从任务创建技能

        Args:
            task_id: 任务记录ID

        Returns:
            skill_id: 创建的技能ID，或None
        """
        if not self.should_auto_create_skill(task_id):
            return None

        record = self._task_records[task_id]

        skill_data = self.skill_creator.create_skill_from_solution(
            problem=record.problem,
            solution=record.solution,
            context={
                'category': self._infer_category(record.problem),
                'tags': self._extract_tags(record),
                'task_id': task_id,
                'tool_count': len(record.tool_calls),
                'success': record.success
            }
        )

        skill_id = self.skill_store.create_skill(skill_data)
        self._created_this_session += 1

        return skill_id

    def evaluate_and_evolve(self) -> Dict[str, Any]:
        """
        定期评估并进化技能
        类似于Hermes Agent的每15次工具调用后评估

        Returns:
            评估报告
        """
        if not self.should_evaluate():
            return {
                'evaluated': False,
                'reason': 'evaluation_interval_not_reached',
                'tool_calls': self._tool_call_count
            }

        report = {
            'evaluated': True,
            'tool_calls': self._tool_call_count,
            'tasks_recorded': self._session_task_count,
            'skills_created': self._created_this_session,
            'evolved_skills': [],
            'archived_skills': []
        }

        for skill_id in self.skill_store.list_skills():
            skill = self.skill_store.get_skill(skill_id)
            if not skill:
                continue

            skill_id_str = skill.get('id', '')
            related_tasks = self._find_related_tasks(skill_id_str)

            if len(related_tasks) >= 3:
                evolution = self._evolve_skill(skill, related_tasks)
                if evolution:
                    report['evolved_skills'].append(evolution)

        self.reset_evaluation_cycle()

        return report

    def get_skill_suggestions(self, task: str) -> List[Dict[str, Any]]:
        """
        获取技能建议（用于上下文增强）

        Args:
            task: 当前任务描述

        Returns:
            建议创建的新技能列表
        """
        suggestions = []
        recent_tasks = list(self._task_records.values())[-10:]

        for record in recent_tasks:
            if not record.success:
                continue

            if self._task_matches_query(record.problem, task):
                continue

            complexity = record.evaluation_score
            if complexity >= self.config.min_complexity_score:
                existing = self._find_similar_skill(record.problem)
                if not existing:
                    suggestions.append({
                        'task': record.problem,
                        'complexity': complexity,
                        'tool_count': len(record.tool_calls),
                        'confidence': min(1.0, complexity / 5.0)
                    })

        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions[:3]

    def _evaluate_complexity(
        self,
        problem: str,
        solution: str,
        tool_calls: Optional[List[Dict[str, Any]]]
    ) -> float:
        """评估任务复杂度"""
        score = 0.0

        for pattern in self.COMPLEXITY_INDICATORS:
            if re.search(pattern, problem) or re.search(pattern, solution):
                score += 1.0

        if tool_calls:
            score += min(len(tool_calls) * 0.5, 3.0)

        lines = solution.strip().split('\n')
        if len(lines) > 5:
            score += 1.0
        if len(lines) > 10:
            score += 1.0

        code_blocks = len(re.findall(r'```[\s\S]+?```', solution))
        score += code_blocks * 0.5

        return score

    def _infer_category(self, problem: str) -> str:
        """推断任务类别"""
        return self.skill_creator._infer_category(problem, None)

    def _extract_tags(self, record: TaskRecord) -> List[str]:
        """从任务记录中提取标签"""
        all_text = f"{record.problem} {record.solution}"

        tags = set()

        tech_patterns = [
            r'\b(?:Python|JavaScript|TypeScript|Java|Go|Rust|C\+\+|React|Vue|Angular)\b',
            r'\b(?:API|HTTP|REST|GraphQL|SQL|NoSQL|MongoDB|PostgreSQL)\b',
            r'\b(?:Git|Docker|Kubernetes|AWS|Azure|GCP)\b',
            r'\b(?:AI|ML|LLM|NLP|GPT|Transformer)\b',
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            tags.update(m.lower() for m in matches)

        if record.tool_calls:
            for call in record.tool_calls:
                if isinstance(call, dict) and 'tool' in call:
                    tags.add(call['tool'])

        return list(tags)[:10]

    def _find_similar_skill(self, problem: str) -> Optional[str]:
        """查找相似技能"""
        existing_skills = self.skill_store.search_skills(problem)
        if existing_skills:
            return existing_skills[0].get('id')
        return None

    def _find_related_tasks(self, skill_id: str) -> List[TaskRecord]:
        """查找与技能相关的任务"""
        related = []
        skill = self.skill_store.get_skill(skill_id)
        if not skill:
            return related

        skill_name = skill.get('name', '').lower()

        for record in self._task_records.values():
            if skill_name in record.problem.lower():
                related.append(record)

        return related

    def _update_skill_with_feedback(
        self,
        skill_id: str,
        record: TaskRecord
    ) -> None:
        """用新任务的反馈更新技能"""
        skill = self.skill_store.get_skill(skill_id)
        if not skill:
            return

        current_usage = skill.get('usage_count', 0)
        current_success = skill.get('success_rate', 1.0)

        new_total = current_usage + 1
        new_successes = current_success * current_usage + (1 if record.success else 0)
        new_success_rate = new_successes / new_total

        updates = {
            'usage_count': new_total,
            'success_rate': new_success_rate
        }

        if record.success and len(record.tool_calls) > 0:
            steps = self.skill_creator._parse_solution_steps(record.solution)
            if steps and len(steps) > 0:
                existing_steps = skill.get('action', [])
                if len(steps) > len(existing_steps):
                    updates['action'] = steps

        self.skill_store.update_skill(skill_id, updates)

    def _evolve_skill(
        self,
        skill: Dict[str, Any],
        related_tasks: List[TaskRecord]
    ) -> Optional[Dict[str, Any]]:
        """根据多个相关任务进化技能"""
        if len(related_tasks) < 3:
            return None

        success_count = sum(1 for t in related_tasks if t.success)
        success_rate = success_count / len(related_tasks)

        if success_rate < 0.5:
            return {
                'skill_id': skill.get('id'),
                'action': 'archived',
                'reason': 'low_success_rate',
                'success_rate': success_rate
            }

        avg_complexity = sum(t.evaluation_score for t in related_tasks) / len(related_tasks)

        if avg_complexity > skill.get('evaluation_score', 0):
            best_task = max(related_tasks, key=lambda t: t.evaluation_score)
            improved = self.skill_creator.improve_skill(
                skill.get('id'),
                {
                    'additional_steps': self.skill_creator._parse_solution_steps(best_task.solution),
                    'success_rate': success_rate
                },
                skill
            )
            self.skill_store.update_skill(skill.get('id'), improved)

            return {
                'skill_id': skill.get('id'),
                'action': 'evolved',
                'new_success_rate': success_rate,
                'task_count': len(related_tasks)
            }

        return None

    def _task_matches_query(self, problem: str, query: str) -> bool:
        """检查问题是否匹配查询"""
        problem_words = set(problem.lower().split())
        query_words = set(query.lower().split())

        overlap = problem_words & query_words
        return len(overlap) >= 2

    def get_stats(self) -> Dict[str, Any]:
        """获取进化统计"""
        return {
            'total_tasks_recorded': len(self._task_records),
            'tasks_this_session': self._session_task_count,
            'skills_created_this_session': self._created_this_session,
            'tool_calls_this_cycle': self._tool_call_count,
            'evaluation_interval': self.config.evaluation_interval,
            'next_evaluation_at': max(0, self.config.evaluation_interval - self._tool_call_count)
        }
