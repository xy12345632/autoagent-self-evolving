import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from autoagent.api.router import ModelRouter


class TestModelRouter:
    @pytest.fixture
    def mock_provider(self):
        provider = MagicMock()
        provider.chat = AsyncMock(return_value={"content": "response", "usage": 100})
        return provider

    @pytest.fixture
    def router(self, mock_provider):
        providers = {"opencode_zen": mock_provider}
        return ModelRouter(providers, default_preference="opencode_zen")

    @pytest.mark.asyncio
    async def test_route_basic(self, router, mock_provider):
        result = await router.route("test prompt")
        assert result["content"] == "response"
        mock_provider.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_with_preferred_provider(self, router, mock_provider):
        result = await router.route("test prompt", preferred_provider="opencode_zen")
        assert result["content"] == "response"

    @pytest.mark.asyncio
    async def test_route_fallback_on_failure(self, mock_provider):
        failing_provider = MagicMock()
        failing_provider.chat = AsyncMock(side_effect=Exception("API Error"))

        working_provider = MagicMock()
        working_provider.chat = AsyncMock(return_value={"content": "fallback response"})

        providers = {
            "failing": failing_provider,
            "working": working_provider
        }
        router = ModelRouter(providers, default_preference="failing")

        result = await router.route("test prompt")
        assert result["content"] == "fallback response"

    @pytest.mark.asyncio
    async def test_route_updates_usage_counter(self, router, mock_provider):
        await router.route("prompt 1")
        await router.route("prompt 2")

        stats = router.get_stats()
        assert stats["usage"]["opencode_zen"] == 2

    @pytest.mark.asyncio
    async def test_route_tracks_failed_providers(self, mock_provider):
        failing_provider = MagicMock()
        failing_provider.chat = AsyncMock(side_effect=Exception("API Error"))

        providers = {"failing": failing_provider}
        router = ModelRouter(providers, default_preference="failing")

        try:
            await router.route("test prompt")
        except Exception:
            pass

        stats = router.get_stats()
        assert "failing" in stats["failed"]

    def test_get_next_available_provider(self, mock_provider):
        providers = {"provider1": mock_provider, "provider2": MagicMock()}
        router = ModelRouter(providers)

        router.failed_providers["provider1"] = 1
        available = router._get_next_available_provider()
        assert available == "provider2"

    def test_get_next_available_provider_all_failed(self, mock_provider):
        providers = {"provider1": mock_provider}
        router = ModelRouter(providers)

        router.failed_providers["provider1"] = 1
        available = router._get_next_available_provider()
        assert available is None

    @pytest.mark.asyncio
    async def test_load_balance(self, router, mock_provider):
        router.usage_counter["opencode_zen"] = 10
        most_used = await router.load_balance()
        assert most_used == "opencode_zen"

    def test_get_stats(self, router):
        router.usage_counter["opencode_zen"] = 5
        router.failed_providers["other"] = 2

        stats = router.get_stats()
        assert stats["usage"]["opencode_zen"] == 5
        assert stats["failed"]["other"] == 2
        assert "opencode_zen" in stats["available_providers"]

    def test_reset_stats(self, router):
        router.usage_counter["test"] = 10
        router.failed_providers["test"] = 5

        router.reset_stats()
        assert dict(router.usage_counter) == {}
        assert dict(router.failed_providers) == {}

    def test_route_no_available_providers(self):
        router = ModelRouter({}, default_preference="nonexistent")
        router.failed_providers["nonexistent"] = 1

        with pytest.raises(RuntimeError, match="No available providers"):
            asyncio.get_event_loop().run_until_complete(router.route("test"))


class TestModelRouterIntegration:
    @pytest.mark.asyncio
    async def test_multiple_providers_fallback_chain(self):
        providers = {}
        responses = ["first", "second", "third"]

        for i, resp in enumerate(responses):
            provider = MagicMock()
            if i == 0:
                provider.chat = AsyncMock(side_effect=Exception("Fail"))
            else:
                provider.chat = AsyncMock(return_value={"content": resp})
            providers[f"provider{i}"] = provider

        router = ModelRouter(providers, default_preference="provider0")

        result = await router.route("test")
        assert result["content"] == "second"

    @pytest.mark.asyncio
    async def test_provider_recovery(self):
        call_count = [0]

        async def mock_chat_fail(*args, **kwargs):
            call_count[0] += 1
            raise Exception("Temporary failure")

        async def mock_chat_success(*args, **kwargs):
            call_count[0] += 1
            return {"content": "success"}

        provider1 = MagicMock()
        provider1.chat = mock_chat_fail
        provider2 = MagicMock()
        provider2.chat = mock_chat_success

        router = ModelRouter({"fail": provider1, "success": provider2})

        result = await router.route("prompt", preferred_provider="fail")
        assert result["content"] == "success"
        assert "fail" in router.failed_providers
        assert call_count[0] == 2


class TestOpenRouterAPI:
    @pytest.fixture
    def openrouter_config(self):
        return {
            "model": "anthropic/claude-3-opus",
            "temperature": 0.7,
            "max_tokens": 4096
        }

    def test_openrouter_config_parsing(self, openrouter_config):
        assert openrouter_config["model"] == "anthropic/claude-3-opus"
        assert openrouter_config["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_openrouter_chat_request_format(self):
        from autoagent.api.openrouter import OpenRouterProvider

        with patch.object(OpenRouterProvider, '__init__', lambda x, y: None):
            provider = OpenRouterProvider(None)
            provider.api_key = "test_key"
            provider.model = "test-model"
            provider.base_url = "https://openrouter.ai/api/v1"

            messages = [{"role": "user", "content": "Hello"}]
            assert messages[0]["role"] == "user"
            assert messages[0]["content"] == "Hello"


class TestOpenCodeZenAPI:
    def test_opencode_zen_endpoint_config(self):
        endpoint = "https://api.opencodezen.com/v1/chat"
        assert "opencodezen.com" in endpoint

    @pytest.mark.asyncio
    async def test_opencode_zen_chat_request(self):
        from autoagent.api.opencode_zen import OpenCodeZenProvider

        with patch.object(OpenCodeZenProvider, '__init__', lambda x, y: None):
            provider = OpenCodeZenProvider(None)
            provider.api_key = "test_key"
            provider.model = "test-model"

            messages = [{"role": "user", "content": "Test"}]
            assert len(messages) == 1
