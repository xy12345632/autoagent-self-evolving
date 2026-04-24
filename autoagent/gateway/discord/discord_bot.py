import asyncio
from typing import Optional, Any
import discord
from discord import Intents

from ..utils.logger import get_logger
from .handlers import DiscordHandlers
from .session_manager import DiscordSessionManager
from .converter import MessageConverter
from .slash_commands import setup_slash_commands

logger = get_logger("discord_bot")


class DiscordBot:
    def __init__(self, token: str, agent_core: Any):
        self.token = token
        self.agent_core = agent_core
        self.bot: Optional[discord.Client] = None
        self.handlers: Optional[DiscordHandlers] = None
        self.session_manager: Optional[DiscordSessionManager] = None
        self.converter: Optional[MessageConverter] = None
        self._running = False

    def _create_client(self) -> discord.Client:
        intents = Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.dm_messages = True
        intents.messages = True
        intents.reactions = True
        return discord.Client(intents=intents)

    async def _setup_bot(self) -> None:
        self.session_manager = DiscordSessionManager()
        self.converter = MessageConverter()
        self.handlers = DiscordHandlers(
            agent_core=self.agent_core,
            session_manager=self.session_manager,
            converter=self.converter,
        )

        await setup_slash_commands(self.bot, self.agent_core, self.session_manager)

        @self.bot.event
        async def on_ready():
            await self.handlers.on_ready()
            logger.info(f"Discord Bot已登录: {self.bot.user}")

        @self.bot.event
        async def on_message(message: discord.Message):
            await self.handlers.on_message(message)

        @self.bot.event
        async def on_message_edit(before: discord.Message, after: discord.Message):
            await self.handlers.on_message_edit(before, after)

        @self.bot.event
        async def on_disconnect():
            logger.warning("Discord Bot已断开连接")

        @self.bot.event
        async def on_resumed():
            logger.info("Discord Bot已恢复连接")

    def start(self) -> None:
        if self._running:
            logger.warning("Discord Bot已在运行")
            return

        self.bot = self._create_client()
        loop = asyncio.get_event_loop()

        async def _start():
            await self._setup_bot()
            await self.bot.start(self.token)

        try:
            loop.run_until_complete(_start())
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭Bot...")
            loop.run_until_complete(self.stop())
        except Exception as e:
            logger.error(f"Discord Bot启动失败: {e}")
            raise

    async def start_async(self) -> None:
        if self._running:
            logger.warning("Discord Bot已在运行")
            return

        self.bot = self._create_client()
        await self._setup_bot()
        self._running = True
        await self.bot.start(self.token)

    async def stop(self) -> None:
        if not self._running and self.bot is None:
            logger.warning("Discord Bot未在运行")
            return

        self._running = False
        if self.bot:
            await self.bot.close()
            logger.info("Discord Bot已停止")
        self.bot = None

    def get_status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "connected": self.bot is not None and not self.bot.is_closed(),
            "user": str(self.bot.user) if self.bot else None,
            "servers": len(self.bot.guilds) if self.bot else 0,
        }
