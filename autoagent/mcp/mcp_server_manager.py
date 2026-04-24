import asyncio
from typing import Any, Optional

from .mcp_client import MCPClient


class ServerConfig:
    def __init__(self, name: str, url: str, config: Optional[dict[str, Any]] = None):
        self.name = name
        self.url = url
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.timeout = self.config.get("timeout", 30.0)


class ServerManager:
    def __init__(self):
        self._servers: dict[str, ServerConfig] = {}
        self._clients: dict[str, MCPClient] = {}
        self._startup_tasks: list[asyncio.Task] = []

    def add_server(self, name: str, url: str, config: Optional[dict[str, Any]] = None) -> None:
        if name in self._servers:
            raise ValueError(f"服务器 {name} 已存在")
        self._servers[name] = ServerConfig(name, url, config)

    def remove_server(self, name: str) -> bool:
        if name not in self._servers:
            return False
        del self._servers[name]
        if name in self._clients:
            asyncio.create_task(self._clients[name].disconnect())
            del self._clients[name]
        return True

    def get_server(self, name: str) -> Optional[ServerConfig]:
        return self._servers.get(name)

    def list_servers(self) -> list[dict[str, Any]]:
        return [
            {"name": s.name, "url": s.url, "enabled": s.enabled, "config": s.config}
            for s in self._servers.values()
        ]

    async def start_all(self) -> dict[str, bool]:
        results = {}
        for name, config in self._servers.items():
            if config.enabled:
                try:
                    client = MCPClient(timeout=config.timeout)
                    await client.connect(config.url)
                    self._clients[name] = client
                    results[name] = True
                except Exception:
                    results[name] = False
            else:
                results[name] = False
        return results

    async def stop_all(self) -> None:
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()

    async def get_client(self, name: str) -> Optional[MCPClient]:
        if name not in self._clients:
            config = self._servers.get(name)
            if not config or not config.enabled:
                return None
            client = MCPClient(timeout=config.timeout)
            await client.connect(config.url)
            self._clients[name] = client
        return self._clients[name]
