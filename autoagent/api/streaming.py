"""
流式响应处理器
"""

import asyncio
import json
from typing import AsyncIterator, Callable, Optional, Any, Dict, List
from dataclasses import dataclass
from enum import Enum


class ChunkType(Enum):
    CONTENT = "content"
    TOOL_CALL = "tool_call"
    ERROR = "error"
    DONE = "done"


@dataclass
class StreamChunk:
    type: ChunkType
    content: str
    raw_data: Optional[Dict[str, Any]] = None


class StreamingHandler:
    """
    流式响应处理器

    功能:
    1. 处理 SSE 格式的流式响应
    2. 支持实时输出显示
    3. 支持中断流式输出
    """

    def __init__(self, on_chunk: Optional[Callable[[StreamChunk], None]] = None):
        self.on_chunk = on_chunk
        self._cancelled = False

    def cancel(self) -> None:
        """取消流式输出"""
        self._cancelled = True

    def reset(self) -> None:
        """重置取消状态"""
        self._cancelled = False

    async def process_sse_stream(
        self,
        response: Any,
        accumulate_content: bool = True
    ) -> AsyncIterator[StreamChunk]:
        """
        处理 SSE 流式响应

        Args:
            response: httpx 响应对象
            accumulate_content: 是否累积内容

        Yields:
            StreamChunk: 流式数据块
        """
        content_buffer = ""

        async for line in response.aiter_lines():
            if self._cancelled:
                yield StreamChunk(
                    type=ChunkType.ERROR,
                    content="Stream cancelled"
                )
                break

            line = line.strip()
            if not line:
                continue

            if line.startswith("data: "):
                data = line[6:]

                if data == "[DONE]":
                    yield StreamChunk(
                        type=ChunkType.DONE,
                        content=content_buffer if accumulate_content else ""
                    )
                    break

                try:
                    chunk_data = json.loads(data)

                    if "choices" in chunk_data:
                        delta = chunk_data["choices"][0].get("delta", {})

                        if "content" in delta:
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

                    elif "error" in chunk_data:
                        yield StreamChunk(
                            type=ChunkType.ERROR,
                            content=str(chunk_data["error"]),
                            raw_data=chunk_data
                        )

                except json.JSONDecodeError:
                    continue

    async def process_non_sse_stream(
        self,
        response: Any
    ) -> AsyncIterator[StreamChunk]:
        """
        处理普通流式响应

        Args:
            response: httpx 响应对象

        Yields:
            StreamChunk: 流式数据块
        """
        async for text in response.aiter_text():
            if self._cancelled:
                break

            yield StreamChunk(
                type=ChunkType.CONTENT,
                content=text
            )


class StreamingResponseGenerator:
    """
    流式响应生成器

    支持:
    1. OpenAI 兼容的 SSE 流式响应
    2. 实时 token 输出
    3. 增量内容渲染
    """

    def __init__(self):
        self.handler = StreamingHandler()

    async def generate_stream(
        self,
        provider: Any,
        messages: list,
        model: str = "minimax-m2.5-free",
        **kwargs
    ) -> AsyncIterator[str]:
        """
        生成流式响应

        Args:
            provider: API 提供者
            messages: 消息列表
            model: 模型名称

        Yields:
            str: 增量内容
        """
        try:
            async for chunk in provider.chat_stream(messages=messages, model=model, stream=True, **kwargs):
                if self.handler._cancelled:
                    break

                if chunk.type == ChunkType.CONTENT:
                    yield chunk.content

                elif chunk.type == ChunkType.ERROR:
                    yield f"\n[Error: {chunk.content}]"

                elif chunk.type == ChunkType.DONE:
                    break

        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    def cancel(self) -> None:
        """取消流式输出"""
        self.handler.cancel()

    def reset(self) -> None:
        """重置状态"""
        self.handler.reset()
