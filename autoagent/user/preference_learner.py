from typing import Dict, List, Optional, Any
from datetime import datetime
from .user_model import UserModel, UserPreference, UserBehavior


class PreferenceLearner:
    def __init__(self, user_model: UserModel):
        self.user_model = user_model
        self._learning_weights = {
            'explicit': 0.4,
            'implicit': 0.3,
            'behavioral': 0.3
        }

    def learn_from_explicit_feedback(self, feedback_type: str, value: Any):
        if feedback_type == 'response_style':
            self.update_response_style(value, confidence=0.8)
        elif feedback_type == 'communication_tone':
            self.update_communication_tone(value)
        elif feedback_type == 'notification_preference':
            self.user_model.preferences.notification_preference = value

    def learn_from_implicit_feedback(self, action: str, context: Dict[str, Any]):
        if action == 'skip_detailed_response':
            current = self.user_model.preferences.response_style
            if current == 'detailed':
                self.update_response_style('balanced', confidence=0.3)
        elif action == 'expand_summary':
            current = self.user_model.preferences.response_style
            if current == 'concise':
                self.update_response_style('balanced', confidence=0.3)
        elif action == 'change_language':
            if 'language' in context:
                self.user_model.preferences.preferred_language = context['language']

    def learn_from_behavior(self, behavior_data: Dict[str, Any]):
        if 'avg_session_length' in behavior_data:
            self.user_model.behaviors.avg_session_length = behavior_data['avg_session_length']
        if 'peak_hours' in behavior_data:
            self.user_model.behaviors.peak_interaction_hours = behavior_data['peak_hours']
            self.infer_time_preference_from_hours(behavior_data['peak_hours'])

    def update_response_style(self, style: str, confidence: float):
        valid_styles = ['concise', 'balanced', 'detailed']
        if style in valid_styles:
            weight = confidence * self._learning_weights['explicit']
            current = self.user_model.preferences.response_style
            if weight > 0.5:
                self.user_model.preferences.response_style = style

    def update_communication_tone(self, tone: str):
        valid_tones = ['formal', 'friendly', 'casual']
        if tone in valid_tones:
            self.user_model.preferences.communication_tone = tone

    def infer_time_preference(self, interaction_time: datetime):
        hour = interaction_time.hour
        day = interaction_time.strftime('%A').lower()

        if day not in self.user_model.preferences.interaction_time_preference:
            self.user_model.preferences.interaction_time_preference[day] = []

        if hour not in self.user_model.preferences.interaction_time_preference[day]:
            self.user_model.preferences.interaction_time_preference[day].append(hour)

    def infer_time_preference_from_hours(self, peak_hours: List[int]):
        time_categories = {
            'morning': list(range(6, 12)),
            'afternoon': list(range(12, 18)),
            'evening': list(range(18, 22)),
            'night': list(range(22, 24)) + list(range(0, 6))
        }

        for hour in peak_hours:
            for category, hours in time_categories.items():
                if hour in hours:
                    if category not in self.user_model.preferences.interaction_time_preference:
                        self.user_model.preferences.interaction_time_preference[category] = []
                    if hour not in self.user_model.preferences.interaction_time_preference[category]:
                        self.user_model.preferences.interaction_time_preference[category].append(hour)

    def get_preference_summary(self) -> Dict[str, Any]:
        return {
            'response_style': self.user_model.preferences.response_style,
            'communication_tone': self.user_model.preferences.communication_tone,
            'preferred_language': self.user_model.preferences.preferred_language,
            'notification_preference': self.user_model.preferences.notification_preference,
            'interaction_time_preference': self.user_model.preferences.interaction_time_preference,
            'learning_enabled': self.user_model.learning_enabled,
            'personality_traits': self.user_model.personality_traits
        }
