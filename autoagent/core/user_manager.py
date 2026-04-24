"""
用户管理器 - 管理用户模型和偏好
"""

from typing import Dict, Any, Optional
from datetime import datetime

from ..user.user_model import UserModel, UserPreference, UserBehavior
from ..user.preference_learner import PreferenceLearner
from ..user.behavior_tracker import BehaviorTracker
from ..user.persistence import UserPersistence
from ..user.personality import PersonalityAnalyzer
from ..user.topic_learner import TopicLearner


class UserManager:
    """
    用户管理器

    负责管理用户模型、偏好学习、行为追踪、个性分析和主题学习
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.persistence = UserPersistence()

        saved_model = self.persistence.load_user_model(user_id)

        if saved_model:
            self.user_model = saved_model
        else:
            self.user_model = UserModel(
                user_id=user_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                preferences=UserPreference(),
                behaviors=UserBehavior(),
                personality_traits={},
                learning_enabled=True
            )

        self.preference_learner = PreferenceLearner(self.user_model)
        self.behavior_tracker = BehaviorTracker(self.user_model)
        self.personality_analyzer = PersonalityAnalyzer()
        self.topic_learner = TopicLearner()

        for trait, score in self.user_model.personality_traits.items():
            self.personality_analyzer.user_traits[trait] = score

        for topic, count in self._topic_to_counter(self.user_model.behaviors.conversation_topics):
            self.topic_learner.user_topics[topic] = count

    def _topic_to_counter(self, topics: list) -> Dict[str, int]:
        """转换话题列表为计数器"""
        from collections import Counter
        return Counter(topics)

    def record_interaction(self, interaction_data: Dict[str, Any], user_message: Optional[str] = None):
        """记录一次交互"""
        self.behavior_tracker.record_interaction(
            interaction_data.get('type', 'unknown'),
            interaction_data
        )

        if user_message:
            self.personality_analyzer.analyze_text(user_message)
            self.topic_learner.detect_topics(user_message)

            detected_topics = self.topic_learner.get_current_session_topics()
            if detected_topics:
                new_topics = [
                    topic for topic in detected_topics if topic not in self.user_model.behaviors.conversation_topics]
                self.user_model.behaviors.conversation_topics.extend(new_topics)

        self._sync_traits_to_model()
        self.user_model.updated_at = datetime.now().isoformat()

    def record_tool_usage(self, tool_name: str, context: Dict[str, Any]):
        """记录工具使用"""
        self.behavior_tracker.record_tool_usage(tool_name, context)
        self.preference_learner.learn_from_behavior({
            'type': 'tool_usage',
            'tool': tool_name
        })
        self.user_model.updated_at = datetime.now().isoformat()

    def record_task_completion(self, task: str, tools_used: list, success: bool):
        """记录任务完成"""
        self.behavior_tracker.record_task_completion(task, tools_used, success)
        self.user_model.updated_at = datetime.now().isoformat()

    def learn_preference(self, preference_type: str, value: Any):
        """学习用户偏好"""
        if preference_type == 'response_style':
            self.preference_learner.update_response_style(value, confidence=0.8)
        elif preference_type == 'tone':
            self.preference_learner.update_communication_tone(value)
        self.user_model.updated_at = datetime.now().isoformat()

    def _sync_traits_to_model(self):
        """将分析的特质同步到用户模型"""
        traits = self.personality_analyzer.get_personality_traits()
        self.user_model.personality_traits = traits

    def save(self) -> bool:
        """保存用户模型"""
        self._sync_traits_to_model()
        return self.persistence.save_user_model(self.user_model)

    def get_response_context(self) -> Dict[str, Any]:
        """获取用于生成响应的上下文"""
        return {
            'user_id': self.user_model.user_id,
            'response_style': self.user_model.preferences.response_style,
            'tone': self.user_model.preferences.communication_tone,
            'language': self.user_model.preferences.preferred_language,
            'common_tasks': self.behavior_tracker.get_common_tasks(5),
            'tool_usage_stats': self.behavior_tracker.get_tool_usage_stats(),
            'personality_traits': self.personality_analyzer.get_top_traits(3),
            'conversation_topics': self.topic_learner.get_current_session_topics()
        }

    def get_user_profile(self) -> Dict[str, Any]:
        """获取用户档案"""
        return {
            'user_id': self.user_model.user_id,
            'created_at': self.user_model.created_at,
            'updated_at': self.user_model.updated_at,
            'preferences': {
                'response_style': self.user_model.preferences.response_style,
                'tone': self.user_model.preferences.communication_tone,
                'language': self.user_model.preferences.preferred_language,
            },
            'behaviors': self.behavior_tracker.get_behavior_summary(),
            'personality': self.personality_analyzer.get_personality_summary(),
            'topics': self.topic_learner.get_topic_summary(),
            'learning_enabled': self.user_model.learning_enabled
        }

    def get_personality_insights(self) -> Dict[str, Any]:
        """获取个性洞察"""
        return self.personality_analyzer.get_personality_summary()

    def get_topic_insights(self) -> Dict[str, Any]:
        """获取主题洞察"""
        return self.topic_learner.get_topic_summary()

    def predict_next_tool(self, current_task: str) -> Optional[str]:
        """预测下一个可能使用的工具"""
        return self.behavior_tracker.predict_next_tool(current_task)

    def get_learning_suggestions(self) -> Dict[str, Any]:
        """获取学习建议"""
        suggestions = []

        personality_summary = self.personality_analyzer.get_personality_summary()
        if personality_summary['total_analyses'] < 10:
            suggestions.append("与我多对话，帮助我更好地了解你的个性特质。")

        topics = self.topic_learner.get_topic_summary()
        if topics['total_topics_detected'] < 3:
            suggestions.append("讨论更多话题，让我了解你的兴趣方向。")

        return {
            'suggestions': suggestions,
            'progress': {
                'personality_data': personality_summary['total_analyses'],
                'topic_data': topics['total_topics_detected']
            }
        }