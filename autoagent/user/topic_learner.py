"""
对话主题学习器
"""

import re
from typing import List, Dict, Set, Optional
from collections import Counter


class TopicLearner:
    """对话主题学习器"""

    def __init__(self):
        self.topic_keywords = {
            "编程开发": [
                "Python", "Java", "JavaScript", "代码", "函数", "API",
                "调试", "bug", "程序", "开发", "编译器", "框架",
                "前端", "后端", "数据库", "服务器", "部署"
            ],
            "学习教育": [
                "学习", "课程", "教程", "知识", "教育", "学校",
                "考试", "作业", "论文", "资料", "书籍", "阅读"
            ],
            "生活日常": [
                "吃饭", "睡觉", "逛街", "电影", "游戏", "朋友",
                "家庭", "工作", "上班", "休息", "假期", "旅游"
            ],
            "科技数码": [
                "手机", "电脑", "平板", "笔记本", "软件", "APP",
                "操作系统", "Windows", "Mac", "Linux", "硬件"
            ],
            "创意设计": [
                "设计", "艺术", "图片", "PS", "画图", "排版",
                "颜色", "UI", "UX", "界面", "美观"
            ],
            "数据分析": [
                "数据", "分析", "统计", "图表", "Excel", "表格",
                "报告", "研究", "趋势", "指标"
            ],
            "项目管理": [
                "项目", "计划", "任务", "团队", "协作", "进度",
                "里程碑", "目标", "成果"
            ],
            "健康运动": [
                "运动", "健身", "健康", "饮食", "跑步", "瑜伽",
                "训练", "康复"
            ]
        }

        self.user_topics = Counter()
        self.current_session_topics = set()
        self.topic_history = []

    def detect_topics(self, text: str) -> Set[str]:
        """检测对话主题"""
        found_topics = set()

        if not text:
            return set()

        text_lower = text.lower()

        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_topics.add(topic)
                    break

        if found_topics:
            self._update_topics(found_topics)
            self.current_session_topics.update(found_topics)

        return found_topics

    def _update_topics(self, topics: Set[str]):
        """更新用户主题"""
        for topic in topics:
            self.user_topics[topic] += 1

        self.topic_history.append({
            "timestamp": None,
            "topics": list(topics)
        })

    def get_top_topics(self, limit: int = 5) -> List[Dict[str, any]]:
        """获取得分最高的主题"""
        sorted_topics = self.user_topics.most_common(limit)

        total = sum(self.user_topics.values()) if self.user_topics else 1

        return [
            {
                "topic": topic,
                "count": count,
                "percentage": round(count / total * 100, 1)
            }
            for topic, count in sorted_topics
        ]

    def get_current_session_topics(self) -> List[str]:
        """获取当前会话的主题"""
        return list(self.current_session_topics)

    def reset_session(self):
        """重置会话"""
        self.current_session_topics = set()

    def get_topic_summary(self) -> Dict[str, any]:
        """获取主题分析总结"""
        return {
            "total_topics_detected": len(self.user_topics),
            "top_topics": self.get_top_topics(5),
            "current_session_topics": list(self.current_session_topics),
            "topic_history_count": len(self.topic_history)
        }

