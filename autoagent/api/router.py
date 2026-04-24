import asyncio
from typing import Any, Callable, Dict, List, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class ModelRouter:
    def __init__(
        self,
        providers: Dict[str, Any],
        default_preference: Optional[str] = None
    ):
        self.providers = providers
        self.default_preference = default_preference or list(providers.keys())[0]
        self.usage_counter: Counter = Counter()
        self.failed_providers: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def route(
        self,
        prompt: str,
        preferred_provider: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        provider_name = preferred_provider or self.default_preference

        if provider_name not in self.providers:
            provider_name = self._get_next_available_provider()

        if not provider_name:
            raise RuntimeError("No available providers")

        provider = self.providers[provider_name]
        try:
            if not hasattr(provider, "chat"):
                raise AttributeError(f"Provider {provider_name} has no chat method")

            if messages:
                result = await provider.chat(messages=messages, **kwargs)
            else:
                result = await provider.chat(messages=[{"role": "user", "content": prompt}], **kwargs)

            async with self._lock:
                self.usage_counter[provider_name] += 1
                if provider_name in self.failed_providers:
                    del self.failed_providers[provider_name]

            return result

        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {e}")
            return await self.fallback(provider_name, e, prompt, **kwargs)

    async def fallback(
        self,
        failed_provider: str,
        error: Exception,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        async with self._lock:
            self.failed_providers[failed_provider] = self.failed_providers.get(failed_provider, 0) + 1

        available = self._get_next_available_provider()
        if not available:
            raise RuntimeError("No available providers after fallback attempts")

        logger.info(f"Falling back from {failed_provider} to {available}")
        return await self.route(prompt, preferred_provider=available, **kwargs)

    def _get_next_available_provider(self) -> Optional[str]:
        for provider_name in self.providers:
            if provider_name not in self.failed_providers:
                return provider_name
        return None

    async def load_balance(self) -> str:
        async with self._lock:
            if not self.usage_counter:
                return self.default_preference
            return self.usage_counter.most_common(1)[0][0]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "usage": dict(self.usage_counter),
            "failed": dict(self.failed_providers),
            "available_providers": list(self.providers.keys())
        }

    def reset_stats(self):
        self.usage_counter.clear()
        self.failed_providers.clear()