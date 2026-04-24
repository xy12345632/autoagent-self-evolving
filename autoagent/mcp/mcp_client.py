import asyncio
import json
from typing import Any, Optional

try:
    import httpx
except ImportError:
    httpx = None

try:
    import aiohttp
except ImportError:
    aiohttp = None


class MCPClient:
    def __init__(self, timeout: float = 30.0):
        self.server_url: Optional[str] = None
        self.timeout = timeout
        self._client: Optional[Any] = None
        self._connected = False

    async def connect(self, server_url: str) -> bool:
        if not httpx and not aiohttp:
            raise RuntimeError("需要安装 httpx 或 aiohttp: pip install httpx aiohttp")

        self.server_url = server_url
        try:
            if httpx:
                self._client = httpx.AsyncClient(timeout=self.timeout)
                response = await self._client.get(f"{server_url}/health")
                self._connected = response.status_code == 200
            else:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                self._client = aiohttp.ClientSession(timeout=timeout)
                async with self._client.get(f"{server_url}/health") as response:
                    self._connected = response.status == 200
            return self._connected
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"连接MCP服务器失败: {e}")

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        self.server_url = None

    async def list_tools(self) -> list[dict[str, Any]]:
        if not self._connected or not self.server_url:
            raise RuntimeError("未连接MCP服务器")

        if httpx:
            response = await self._client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            return response.json().get("tools", [])
        else:
            async with self._client.get(f"{self.server_url}/tools") as response:
                data = await response.json()
                return data.get("tools", [])

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> Any:
        if not self._connected or not self.server_url:
            raise RuntimeError("未连接MCP服务器")

        payload = {"name": tool_name, "parameters": params}

        if httpx:
            response = await self._client.post(
                f"{self.server_url}/tools/call", json=payload
            )
            response.raise_for_status()
            return response.json()
        else:
            async with self._client.post(
                f"{self.server_url}/tools/call", json=payload
            ) as response:
                return await response.json()

    async def get_resources(self) -> list[dict[str, Any]]:
        if not self._connected or not self.server_url:
            raise RuntimeError("未连接MCP服务器")

        if httpx:
            response = await self._client.get(f"{self.server_url}/resources")
            response.raise_for_status()
            return response.json().get("resources", [])
        else:
            async with self._client.get(f"{self.server_url}/resources") as response:
                data = await response.json()
                return data.get("resources", [])

    async def read_resource(self, resource_uri: str) -> Any:
        if not self._connected or not self.server_url:
            raise RuntimeError("未连接MCP服务器")

        if httpx:
            response = await self._client.get(
                f"{self.server_url}/resources/read",
                params={"uri": resource_uri}
            )
            response.raise_for_status()
            return response.json()
        else:
            async with self._client.get(
                f"{self.server_url}/resources/read",
                params={"uri": resource_uri}
            ) as response:
                return await response.json()

    @property
    def is_connected(self) -> bool:
        return self._connected
