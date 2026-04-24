import asyncio
from typing import Any, Optional, Callable, Dict, List
from dataclasses import dataclass
from ..config.config_manager import ConfigManager
from ..utils.logger import get_logger

logger = get_logger("response_generator")


@dataclass
class GenerationResult:
    success: bool
    content: str
    tool_calls: Optional[list[dict[str, Any]]] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = None


class ResponseGenerator:
    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        model_router: Optional[Any] = None
    ):
        self.config_manager = config_manager or ConfigManager()
        self.model_router = model_router
        opencode_zen_config = self.config_manager.get_config("model_providers", "opencode_zen") or {}
        self._default_model = opencode_zen_config.get("default_model", "minimax-m2.5-free")
        self._provider = "opencode_zen"

    async def generate_async(
        self,
        prompt: str,
        tools: Optional[list[dict[str, Any]]] = None,
        context: Optional[dict[str, Any]] = None
    ) -> GenerationResult:
        try:
            if tools:
                return await self._generate_with_tools_async(prompt, tools, context)
            else:
                return await self._generate_simple_async(prompt, context)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return GenerationResult(
                success=False,
                content="",
                error=str(e)
            )

    def generate(
        self,
        prompt: str,
        tools: Optional[list[dict[str, Any]]] = None,
        context: Optional[dict[str, Any]] = None
    ) -> GenerationResult:
        try:
            if tools:
                return self._generate_with_tools_sync(prompt, tools, context)
            else:
                return self._generate_simple_sync(prompt, context)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return GenerationResult(
                success=False,
                content="",
                error=str(e)
            )

    async def _generate_simple_async(self, prompt: str, context: Optional[dict[str, Any]]) -> GenerationResult:
        context = context or {}
        messages = self._build_messages(prompt, context)

        if self.model_router:
            result = await self.model_router.route(
                prompt=prompt,
                messages=messages,
                preferred_provider=self._provider
            )
            content = result.get("content", "")
            if not content and "choices" in result:
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return GenerationResult(
                success=True,
                content=content,
                metadata={"mode": "api", "model": self._default_model}
            )

        return GenerationResult(
            success=False,
            content="",
            error="Model router not configured"
        )

    def _generate_simple_sync(self, prompt: str, context: Optional[dict[str, Any]]) -> GenerationResult:
        context = context or {}
        messages = self._build_messages(prompt, context)

        if self.model_router:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._generate_simple_async(prompt, context))
                    return GenerationResult(
                        success=True,
                        content=f"[处理中] 正在调用AI模型: {prompt[:30]}...",
                        metadata={"mode": "async_triggered"}
                    )
                else:
                    result = loop.run_until_complete(
                        self.model_router.route(
                            prompt=prompt,
                            messages=messages,
                            preferred_provider=self._provider
                        )
                    )
                    content = result.get("content", "")
                    if not content and "choices" in result:
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return GenerationResult(
                        success=True,
                        content=content,
                        metadata={"mode": "api", "model": self._default_model}
                    )
            except Exception as e:
                logger.error(f"API call failed: {e}")
                return GenerationResult(success=False, content="", error=str(e))

        return GenerationResult(
            success=False,
            content="",
            error="Model router not configured"
        )

    async def _generate_with_tools_async(
        self,
        prompt: str,
        tool_calls: list[dict[str, Any]],
        context: Optional[dict[str, Any]]
    ) -> GenerationResult:
        if not tool_calls:
            return await self._generate_simple_async(prompt, context)

        context = context or {}
        messages = self._build_messages(prompt, context, tools=tool_calls)

        if self.model_router:
            result = await self.model_router.route(
                prompt=prompt,
                messages=messages,
                preferred_provider=self._provider
            )
            content = result.get("content", "")
            if not content and "choices" in result:
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return GenerationResult(
                success=True,
                content=content,
                tool_calls=tool_calls,
                metadata={"mode": "tool_calling", "model": self._default_model}
            )

        return GenerationResult(
            success=False,
            content="",
            error="Model router not configured"
        )

    def _generate_with_tools_sync(
        self,
        prompt: str,
        tool_calls: list[dict[str, Any]],
        context: Optional[dict[str, Any]]
    ) -> GenerationResult:
        if not tool_calls:
            return self._generate_simple_sync(prompt, context)

        context = context or {}
        messages = self._build_messages(prompt, context, tools=tool_calls)

        if self.model_router:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._generate_with_tools_async(prompt, tool_calls, context))
                    return GenerationResult(
                        success=True,
                        content=f"[处理中] 正在调用AI模型处理工具调用...",
                        metadata={"mode": "async_triggered"}
                    )
                else:
                    result = loop.run_until_complete(
                        self.model_router.route(
                            prompt=messages,
                            preferred_provider=self._provider
                        )
                    )
                    content = result.get("content", result.get("choices", [{}])[0].get("message", {}).get("content", ""))
                    return GenerationResult(
                        success=True,
                        content=content,
                        tool_calls=tool_calls,
                        metadata={"mode": "tool_calling", "model": self._default_model}
                    )
            except Exception as e:
                logger.error(f"API call failed: {e}")
                return GenerationResult(success=False, content="", error=str(e))

        return GenerationResult(
            success=False,
            content="",
            error="Model router not configured"
        )

    def _build_messages(
        self,
        prompt: str,
        context: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        messages = []

        system_parts = []
        system_parts.append("你是一个智能助手，名为AutoAgent，由自进化个人AI Agent驱动。")

        if context.get("memory_context"):
            system_parts.append(f"\n相关记忆:\n{context['memory_context']}")

        if context.get("skill_context"):
            system_parts.append(f"\n相关技能:\n{context['skill_context']}")

        if tools:
            system_parts.append("\n你可以使用以下工具:")
            for tool in tools:
                name = tool.get("name", "unknown")
                desc = tool.get("description", "")
                system_parts.append(f"- {name}: {desc}")

        messages.append({
            "role": "system",
            "content": "\n".join(system_parts)
        })

        if context.get("history"):
            for h in context["history"][-10:]:
                role = h.get("role", "user")
                content = h.get("content", "")
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": prompt})

        return messages

    def generate_streaming(
        self,
        prompt: str,
        callback: Callable[[str], None],
        context: Optional[dict[str, Any]] = None
    ) -> GenerationResult:
        try:
            result = self._generate_simple_sync(prompt, context)

            for chunk in self._chunk_text(result.content):
                callback(chunk)

            return GenerationResult(
                success=True,
                content=result.content,
                metadata={"mode": "streaming"}
            )
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            return GenerationResult(
                success=False,
                content="",
                error=str(e)
            )

    def _chunk_text(self, text: str, chunk_size: int = 10) -> list[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
