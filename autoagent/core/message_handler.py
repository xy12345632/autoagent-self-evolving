import re
from typing import Any, Optional
from dataclasses import dataclass
from ..utils.logger import get_logger

logger = get_logger("message_handler")


@dataclass
class IntentResult:
    intent: str
    confidence: float
    entities: dict[str, Any]
    metadata: dict[str, Any]


class MessageHandler:
    def __init__(self):
        self._intent_keywords = {
            "question": ["什么", "怎么", "如何", "为什么", "哪里", "谁", "when", "what", "how", "why", "where", "who"],
            "command": ["执行", "完成", "做", "开始", "停止", "调用", "run", "do", "start", "stop", "execute"],
            "greeting": ["你好", "嗨", "hello", "hi", "早上好", "晚上好"],
            " farewell": ["再见", "拜拜", "bye", "下次见"],
            "planning": ["计划", "安排", "schedule", "plan"],
            "creation": ["创建", "新建", "生成", "写", "create", "new", "generate"],
        }
        self._entity_patterns = {
            "time": r"\d{1,2}[点时]\d{0,2}分?|今天|明天|后天|昨天|\d{4}[-/]\d{1,2}[-/]\d{1,2}",
            "number": r"\d+",
            "mention": r"@[\w]+",
            "hashtag": r"#[\w]+",
        }

    def handle_message(self, message: str) -> dict[str, Any]:
        intent_result = self.classify_intent(message)
        entities = self.extract_entities(message)
        context = self.build_context(message)

        return {
            "original_message": message,
            "intent": intent_result,
            "entities": entities,
            "context": context,
            "processed": True,
        }

    def classify_intent(self, message: str) -> IntentResult:
        message_lower = message.lower()
        scores: dict[str, float] = {}

        for intent, keywords in self._intent_keywords.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                scores[intent] = score / len(keywords)

        if not scores:
            return IntentResult(
                intent="unknown",
                confidence=0.0,
                entities={},
                metadata={}
            )

        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent], 1.0)

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            entities={},
            metadata={"all_scores": scores}
        )

    def extract_entities(self, message: str) -> dict[str, Any]:
        entities = {}

        for entity_type, pattern in self._entity_patterns.items():
            matches = re.findall(pattern, message)
            if matches:
                entities[entity_type] = matches if len(matches) > 1 else matches[0]

        return entities

    def build_context(self, message: str) -> dict[str, Any]:
        context = {
            "message_length": len(message),
            "has_question_mark": "?" in message or "？" in message,
            "has_exclamation": "!" in message or "！" in message,
            "language": self._detect_language(message),
        }
        return context

    def _detect_language(self, text: str) -> str:
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        total_chars = len(text.strip())

        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars
        if chinese_ratio > 0.3:
            return "zh"
        return "en"
