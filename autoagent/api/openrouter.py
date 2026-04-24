import httpx
from typing import Any, Dict, List, Optional


class OpenRouterProvider:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        site_url: Optional[str] = None,
        site_name: Optional[str] = None
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.site_url = site_url
        self.site_name = site_name
        self.client = httpx.AsyncClient(timeout=120.0)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name
        return headers

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-4o-mini",
        **kwargs
    ) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(),
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def embeddings(self, text: str, model: str = "openai/text-embedding-3-small") -> List[float]:
        payload = {
            "model": model,
            "input": text
        }
        response = await self.client.post(
            f"{self.base_url}/embeddings",
            headers=self._get_headers(),
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    async def list_models(self) -> List[Dict[str, Any]]:
        response = await self.client.get(
            f"{self.base_url}/models",
            headers=self._get_headers()
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def close(self):
        await self.client.aclose()