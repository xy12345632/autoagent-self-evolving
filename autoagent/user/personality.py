"""
个性特质分析器
"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import re


class PersonalityAnalyzer:
    """个性特质分析器"""

    def __init__(self):
        self.trait_keywords = {
            "开放_创新": [
                "试试", "尝试", "新", "创新", "探索", "好奇", "学习", "有趣",
                "实验", "新鲜", "创意", "不同", "变化"
            ],
            "严谨_认真": [
                "仔细", "认真", "精确", "完美", "重要", "必须", "确保",
                "确认", "细节", "准备", "计划", "仔细检查", "保证"
            ],
            "外向_社交": [
                "朋友", "聊天", "聚会", "见面", "一起", "分享", "团队",
                "社交", "活跃", "热闹", "开心"
            ],
            "友善_合作": [
                "谢谢", "请", "麻烦", "辛苦", "没关系", "帮忙", "帮助",
                "合作", "一起", "支持", "理解"
            ],
            "情绪_稳定": [
                "冷静", "淡定", "没关系", "慢慢来", "没问题", "别着急",
                "放松", "不要紧"
            ],
            "实用_效率": [
                "快点", "快速", "效率", "方便", "简单", "直接", "实用",
                "节省时间", "高效", "优化"
            ],
            "技术_编程": [
                "代码", "程序", "开发", "编程", "技术", "Python", "JavaScript",
                "函数", "API", "调试", "部署"
            ],
            "创意_设计": [
                "设计", "艺术", "美观", "漂亮", "颜色", "风格", "创意",
                "灵感", "视觉", "排版"
            ],
            "数据分析": [
                "数据", "分析", "统计", "图表", "趋势", "报告", "研究",
                "可视化", "指标"
            ],
            "规划_组织": [
                "计划", "安排", "组织", "整理", "分类", "时间表", "安排",
                "统筹", "规划"
            ]
        }

        self.user_traits = defaultdict(float)
        self.total_samples = 0

    def analyze_text(self, text: str) -> Dict[str, float]:
        """分析文本，提取个性特质"""
        found_traits = defaultdict(float)

        if not text:
            return {}

        text_lower = text.lower()

        for trait, keywords in self.trait_keywords.items():
            count = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            if count > 0:
                score = min(count / 5, 1.0)  # 最高1.0分
                found_traits[trait] = score

        if found_traits:
            self._update_traits(found_traits)

        return dict(found_traits)

    def _update_traits(self, new_traits: Dict[str, float]):
        """更新用户特质"""
        self.total_samples += 1
        learning_rate = 1.0 / max(self.total_samples, 10)

        for trait, score in new_traits.items():
            old_score = self.user_traits.get(trait, 0)
            new_score = old_score + learning_rate * (score - old_score)
            self.user_traits[trait] = new_score

    def get_personality_traits(self) -> Dict[str, float]:
        """获取个性特质"""
        return dict(self.user_traits)

    def get_top_traits(self, limit: int = 5) -> List[Tuple[str, float]]:
        """获取得分最高的个性特质"""
        sorted_traits = sorted(
            self.user_traits.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_traits[:limit]

    def get_personality_summary(self) -> Dict[str, any]:
        """获取个性分析总结"""
        top_traits = self.get_top_traits(5)

        return {
            "total_analyses": self.total_samples,
            "detected_traits": len(self.user_traits),
            "top_traits": [
                {
                    "trait": trait,
                    "score": round(score, 2)
                }
                for trait, score in top_traits
            ],
            "personality_description": self._generate_description()
        }

    def _generate_description(self) -> str:
        """生成个性描述"""
        top_traits = self.get_top_traits(3)

        if not top_traits:
            return "正在建立个性画像..."

        descriptions = []
        for trait, score in top_traits:
            if score > 0.7:
                descriptions.append(f"你表现出较高的{trait}特质")
            elif score > 0.4:
                descriptions.append(f"你有一定的{trait}倾向")

        return "；".join(descriptions) if descriptions else "正在了解你的个性特质"

    def reset_analysis(self):
        """重置分析"""
        self.user_traits = defaultdict(float)
        self.total_samples = 0

