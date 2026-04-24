from typing import List, Dict, Any, Optional
from datetime import datetime
from ..api.router import ModelRouter

class MemorySummarizer:
    def __init__(self, model_router: ModelRouter = None):
        self.model_router = model_router

    async def summarize_entry(self, content: str, max_length: int = 200) -> str:
        if not self.model_router:
            return content[:max_length] + "..." if len(content) > max_length else content

        prompt = f"""请为以下内容生成一个简洁的摘要，不超过{max_length}个字：

{content}

摘要："""

        result = await self.model_router.route(
            prompt=prompt,
            messages=[{"role": "user", "content": prompt}]
        )

        if isinstance(result, dict):
            return result.get('choices', [{}])[0].get('message', {}).get('content', content[:max_length])
        return content[:max_length]

    async def summarize_multiple(self, entries: List[Dict[str, Any]], theme: Optional[str] = None) -> str:
        if not entries:
            return ""

        content_combined = "\n---\n".join([
            f"[{e.get('timestamp', 'unknown')}] {e.get('content', '')}"
            for e in entries
        ])

        theme_prompt = f"（主题：{theme}）" if theme else ""

        prompt = f"""请将以下关于{theme_prompt}的记忆片段聚合为一个简洁的摘要：

{content_combined}

聚合摘要："""

        if self.model_router:
            result = await self.model_router.route(
                prompt=prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            if isinstance(result, dict):
                return result.get('choices', [{}])[0].get('message', {}).get('content', "")

        return content_combined[:300]

    async def compress_memories(self, memories: List[Dict[str, Any]], max_count: int = 50) -> List[Dict[str, Any]]:
        if len(memories) <= max_count:
            return memories

        sorted_memories = sorted(
            memories,
            key=lambda x: x.get('importance', 5) * (1 + x.get('access_count', 0) * 0.1),
            reverse=True
        )

        return sorted_memories[:max_count]

    def calculate_importance(self, memory_data: Dict[str, Any]) -> float:
        score = 5.0

        if memory_data.get('access_count', 0) > 10:
            score += 2.0
        elif memory_data.get('access_count', 0) > 5:
            score += 1.0

        content_length = len(memory_data.get('content', ''))
        if content_length > 500:
            score += 1.0
        elif content_length > 1000:
            score += 2.0

        memory_type = memory_data.get('memory_type', '')
        if memory_type == 'KNOWLEDGE':
            score += 1.5
        elif memory_type == 'PREFERENCE':
            score += 1.0

        return min(10.0, max(0.0, score))