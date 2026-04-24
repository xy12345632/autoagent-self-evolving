import asyncio
from typing import Any, Callable, Optional

from .mcp_server_manager import ServerManager


class ResourceManager:
    def __init__(self, server_manager: ServerManager):
        self._server_manager = server_manager
        self._subscriptions: dict[str, dict[str, asyncio.Task]] = {}

    async def list_resources(self, server_name: str) -> list[dict[str, Any]]:
        client = await self._server_manager.get_client(server_name)
        if not client:
            raise ValueError(f"服务器 {server_name} 未找到或未连接")
        return await client.get_resources()

    async def read_resource(self, server_name: str, uri: str) -> Any:
        client = await self._server_manager.get_client(server_name)
        if not client:
            raise ValueError(f"服务器 {server_name} 未找到或未连接")
        return await client.read_resource(uri)

    async def subscribe_resource(
        self,
        server_name: str,
        uri: str,
        callback: Callable[[Any], None]
    ) -> None:
        if server_name not in self._subscriptions:
            self._subscriptions[server_name] = {}
        if uri in self._subscriptions[server_name]:
            return

        async def poll():
            last_value = None
            while True:
                try:
                    value = await self.read_resource(server_name, uri)
                    if value != last_value:
                        last_value = value
                        await callback(value)
                except Exception:
                    pass
                await asyncio.sleep(5)

        task = asyncio.create_task(poll())
        self._subscriptions[server_name][uri] = task

    def unsubscribe_resource(self, server_name: str, uri: str) -> bool:
        if server_name not in self._subscriptions:
            return False
        if uri not in self._subscriptions[server_name]:
            return False
        self._subscriptions[server_name][uri].cancel()
        del self._subscriptions[server_name][uri]
        return True

    def unsubscribe_all(self) -> None:
        for server_subs in self._subscriptions.values():
            for task in server_subs.values():
                task.cancel()
        self._subscriptions.clear()
