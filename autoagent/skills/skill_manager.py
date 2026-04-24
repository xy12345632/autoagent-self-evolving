from typing import Dict, Any, Optional, List
from .skill_store import SkillStore
from .skill_loader import SkillLoader
from .skill_creator import SkillCreator
from .skill_evolution import SkillEvolutionManager, SkillEvolutionConfig
from .skill_exporter import SkillExporter
from .skill_marketplace import SkillMarketplace, SkillHubClient


class SkillManager:
    def __init__(
        self,
        skills_dir: Optional[str] = None,
        storage_path: Optional[str] = None
    ):
        self.store = SkillStore(storage_path)
        self.loader = SkillLoader(skills_dir)
        self.creator = SkillCreator()
        self.exporter = SkillExporter(skills_dir)
        self.evolution = SkillEvolutionManager(
            skill_store=self.store,
            skill_creator=self.creator,
            config=SkillEvolutionConfig()
        )
        self.marketplace = SkillMarketplace()
        self._hub_client = None
        self._loaded_skills: Dict[str, Dict[str, Any]] = {}

    def load_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        if skill_id in self._loaded_skills:
            self.store.increment_usage(skill_id)
            return self._loaded_skills[skill_id]

        skill_data = self.store.get_skill(skill_id)
        if not skill_data:
            skill_data = self.loader.load_skill_definition(skill_id)

        if skill_data:
            self._loaded_skills[skill_id] = skill_data
            self.store.increment_usage(skill_id)
            return skill_data

        return None

    def find_relevant_skills(self, task: str) -> List[Dict[str, Any]]:
        task_lower = task.lower()
        all_skills = self.store.list_skills()

        scored_skills = []
        for skill in all_skills:
            score = 0
            trigger = skill.get('trigger', '').lower()
            name = skill.get('name', '').lower()
            description = skill.get('description', '').lower()

            if any(word in trigger for word in task_lower.split() if len(word) > 2):
                score += 3
            if any(word in name for word in task_lower.split() if len(word) > 2):
                score += 2
            if any(word in description for word in task_lower.split() if len(word) > 2):
                score += 1

            score += skill.get('usage_count', 0) * 0.1
            score += skill.get('success_rate', 1.0) * 2

            if score > 0:
                scored_skills.append((skill, score))

        scored_skills.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, _ in scored_skills[:5]]

    def auto_create_skill_if_needed(
        self,
        task: str,
        result: Dict[str, Any]
    ) -> Optional[str]:
        if not self.creator.detect_complex_task(task):
            return None

        if result.get('success', False):
            problem = task
            solution_data = result.get('solution', {})
            if isinstance(solution_data, str):
                solution = solution_data
            else:
                solution = solution_data.get('steps', [str(solution_data)])[0]

            context = {
                'category': result.get('category', 'general'),
                'tags': result.get('tags', [])
            }

            skill_data = self.creator.create_skill_from_solution(
                problem, solution, context
            )

            return self.store.create_skill(skill_data)

        return None

    def get_all_skill_categories(self) -> List[str]:
        skills = self.store.list_skills()
        categories = set()
        for skill in skills:
            if 'category' in skill:
                categories.add(skill['category'])
        return sorted(list(categories))

    def create_skill(self, skill_data: Dict[str, Any]) -> str:
        return self.store.create_skill(skill_data)

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        return self.store.get_skill(skill_id)

    def list_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.store.list_skills(category)

    def search_skills(self, query: str) -> List[Dict[str, Any]]:
        return self.store.search_skills(query)

    def update_skill(self, skill_id: str, skill_data: Dict[str, Any]) -> bool:
        return self.store.update_skill(skill_id, skill_data)

    def delete_skill(self, skill_id: str) -> bool:
        if skill_id in self._loaded_skills:
            del self._loaded_skills[skill_id]
        return self.store.delete_skill(skill_id)

    def reload_skills(self) -> None:
        self._loaded_skills.clear()
        self.loader.reload_skills()

    def record_task(
        self,
        problem: str,
        solution: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        success: bool = True
    ) -> str:
        """
        记录一个任务用于技能进化分析

        Args:
            problem: 用户问题
            solution: AI解决方案
            tool_calls: 使用的工具列表
            success: 是否成功

        Returns:
            task_id: 任务记录ID
        """
        return self.evolution.record_task(problem, solution, tool_calls, success)

    def process_task_result(
        self,
        task_id: str,
        result: Dict[str, Any]
    ) -> Optional[str]:
        """
        处理任务结果，可能自动创建技能

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            创建的技能ID或None
        """
        if self.evolution.should_auto_create_skill(task_id):
            skill_id = self.evolution.auto_create_skill(task_id)
            if skill_id:
                skill = self.store.get_skill(skill_id)
                if skill:
                    self.exporter.export_skill(skill)
                return skill_id
        return None

    def evaluate_and_evolve(self) -> Dict[str, Any]:
        """
        执行定期技能评估和进化
        类似于Hermes的每15次工具调用后评估

        Returns:
            评估报告
        """
        return self.evolution.evaluate_and_evolve()

    def record_tool_call(self) -> int:
        """记录工具调用"""
        return self.evolution.record_tool_call()

    def should_evaluate(self) -> bool:
        """检查是否应该进行评估"""
        return self.evolution.should_evaluate()

    def export_all_skills(self) -> List[str]:
        """
        导出所有技能为SKILL.md格式

        Returns:
            导出的文件路径列表
        """
        skills = self.store.list_skills()
        paths = self.exporter.export_all_skills(skills)
        self.exporter.generate_skill_index(skills)
        return paths

    def get_evolution_stats(self) -> Dict[str, Any]:
        """获取技能进化统计"""
        return self.evolution.get_stats()

    def get_skill_suggestions(self, task: str) -> List[Dict[str, Any]]:
        """
        获取技能创建建议

        Args:
            task: 当前任务

        Returns:
            建议创建的新技能列表
        """
        return self.evolution.get_skill_suggestions(task)

    def publish_to_marketplace(
        self,
        skill_id: str,
        author: str = "local",
        version: str = "1.0.0"
    ) -> Optional[str]:
        """
        发布技能到本地市场

        Args:
            skill_id: 技能ID
            author: 作者名
            version: 版本号

        Returns:
            listing_id: 市场列表ID
        """
        skill = self.store.get_skill(skill_id)
        if not skill:
            return None
        return self.marketplace.publish_skill(skill, author, version)

    def browse_marketplace(
        self,
        category: Optional[str] = None,
        sort_by: str = "rating",
        limit: int = 20
    ) -> List:
        """
        浏览本地市场

        Args:
            category: 分类筛选
            sort_by: 排序方式
            limit: 返回数量

        Returns:
            技能列表
        """
        return self.marketplace.browse(category, sort_by, limit)

    def search_marketplace(self, query: str) -> List:
        """搜索本地市场"""
        return self.marketplace.search(query)

    def install_from_marketplace(self, listing_id: str) -> bool:
        """
        从市场安装技能

        Args:
            listing_id: 市场列表ID

        Returns:
            是否成功
        """
        skill_data = self.marketplace.install_skill(listing_id)
        if not skill_data:
            return False

        self.store.create_skill(skill_data)
        return True

    def get_marketplace_stats(self) -> Dict[str, Any]:
        """获取市场统计"""
        return self.marketplace.get_stats()

    def get_hub_client(self) -> SkillHubClient:
        """获取远程市场客户端"""
        if not self._hub_client:
            self._hub_client = SkillHubClient()
        return self._hub_client
