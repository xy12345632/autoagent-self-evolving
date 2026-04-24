import httpx
import ssl
import json
from typing import Any, Dict, List, Optional, AsyncIterator

from .streaming import StreamChunk, ChunkType


class OpenCodeZenProvider:
    def __init__(self, api_key: str, base_url: str = "https://api.opencodezen.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=60.0,
            verify=True,
            http2=True
        )

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "minimax-m2.5-free",
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

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "minimax-m2.5-free",
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """
        流式聊天

        Args:
            messages: 消息列表
            model: 模型名称

        Yields:
            StreamChunk: 流式数据块
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs
        }

        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(),
            json=payload
        ) as response:
            response.raise_for_status()

            content_buffer = ""

            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    continue

                if line.startswith("data: "):
                    data = line[6:]

                    if data == "[DONE]":
                        yield StreamChunk(
                            type=ChunkType.DONE,
                            content=content_buffer
                        )
                        break

                    try:
                        chunk_data = json.loads(data)

                        if "choices" in chunk_data:
                            delta = chunk_data["choices"][0].get("delta", {})

                            if "content" in delta and delta["content"]:
                                content = delta["content"]
                                content_buffer += content
                                yield StreamChunk(
                                    type=ChunkType.CONTENT,
                                    content=content,
                                    raw_data=chunk_data
                                )

                            if "tool_calls" in delta:
                                for tool_call in delta["tool_calls"]:
                                    yield StreamChunk(
                                        type=ChunkType.TOOL_CALL,
                                        content=json.dumps(tool_call),
                                        raw_data=chunk_data
                                    )

                    except json.JSONDecodeError:
                        continue

    async def embeddings(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
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

    async def close(self):
        await self.client.aclose()