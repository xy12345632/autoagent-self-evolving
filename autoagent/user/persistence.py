"""
Honcho 用户模型持久化
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..utils.paths import GlobalPaths
from .user_model import UserModel, UserPreference, UserBehavior


class UserPersistence:
    """用户模型持久化管理器"""

    def __init__(self):
        self.data_dir = GlobalPaths.get_data_dir() / "user"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_user_file_path(self, user_id: str = "default") -> Path:
        """获取用户数据文件路径"""
        return self.data_dir / f"{user_id}.json"

    def save_user_model(self, user_model: UserModel) -> bool:
        """保存用户模型到文件"""
        try:
            file_path = self.get_user_file_path(user_model.user_id)

            data = {
                "user_id": user_model.user_id,
                "created_at": user_model.created_at,
                "updated_at": user_model.updated_at,
                "preferences": {
                    "response_style": user_model.preferences.response_style,
                    "communication_tone": user_model.preferences.communication_tone,
                    "preferred_language": user_model.preferences.preferred_language,
                    "notification_preference": user_model.preferences.notification_preference,
                    "interaction_time_preference": user_model.preferences.interaction_time_preference
                },
                "behaviors": {
                    "common_tasks": user_model.behaviors.common_tasks,
                    "tool_usage_history": user_model.behaviors.tool_usage_history,
                    "conversation_topics": user_model.behaviors.conversation_topics,
                    "peak_interaction_hours": user_model.behaviors.peak_interaction_hours,
                    "avg_session_length": user_model.behaviors.avg_session_length,
                    "total_interactions": user_model.behaviors.total_interactions
                },
                "personality_traits": user_model.personality_traits,
                "learning_enabled": user_model.learning_enabled,
                "metadata": user_model.metadata
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"保存用户模型失败: {e}")
            return False

    def load_user_model(self, user_id: str = "default") -> Optional[UserModel]:
        """从文件加载用户模型"""
        try:
            file_path = self.get_user_file_path(user_id)

            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            preferences = UserPreference(
                response_style=data.get('preferences', {}).get('response_style', 'balanced'),
                communication_tone=data.get('preferences', {}).get('communication_tone', 'friendly'),
                preferred_language=data.get('preferences', {}).get('preferred_language', 'zh'),
                notification_preference=data.get('preferences', {}).get('notification_preference', 'smart'),
                interaction_time_preference=data.get('preferences', {}).get('interaction_time_preference', {})
            )

            behaviors = UserBehavior(
                common_tasks=data.get('behaviors', {}).get('common_tasks', []),
                tool_usage_history=data.get('behaviors', {}).get('tool_usage_history', {}),
                conversation_topics=data.get('behaviors', {}).get('conversation_topics', []),
                peak_interaction_hours=data.get('behaviors', {}).get('peak_interaction_hours', []),
                avg_session_length=data.get('behaviors', {}).get('avg_session_length', 0.0),
                total_interactions=data.get('behaviors', {}).get('total_interactions', 0)
            )

            return UserModel(
                user_id=data.get('user_id', user_id),
                created_at=data.get('created_at', datetime.now().isoformat()),
                updated_at=data.get('updated_at', datetime.now().isoformat()),
                preferences=preferences,
                behaviors=behaviors,
                personality_traits=data.get('personality_traits', {}),
                learning_enabled=data.get('learning_enabled', True),
                metadata=data.get('metadata', {})
            )

        except Exception as e:
            print(f"加载用户模型失败: {e}")
            return None

    def user_exists(self, user_id: str = "default") -> bool:
        """检查用户模型是否存在"""
        return self.get_user_file_path(user_id).exists()

    def delete_user_model(self, user_id: str = "default") -> bool:
        """删除用户模型"""
        try:
            file_path = self.get_user_file_path(user_id)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"删除用户模型失败: {e}")
            return False

