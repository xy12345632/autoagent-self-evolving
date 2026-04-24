import asyncio
from typing import Optional, Any

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from ..utils.logger import get_logger
from .handlers import MessageHandler as AgentMessageHandler, CommandHandler as AgentCommandHandler, CallbackQueryHandler as AgentCallbackQueryHandler
from .session_manager import SessionManager
from .reply_manager import ReplyManager
from .message_parser import MessageParser

logger = get_logger("telegram_bot")


class TelegramBot:
    def __init__(self, token: str, agent_core: Any):
        self.token = token
        self.agent_core = agent_core
        self.application: Optional[Application] = None
        self.session_manager = SessionManager()
        self.reply_manager: Optional[ReplyManager] = None
        self.message_parser = MessageParser()
        self._handlers: dict[str, Any] = {}
        self._running = False

    async def _post_init(self, application: Application) -> None:
        self.reply_manager = ReplyManager(application.bot)
        self._setup_handlers(application)
        logger.info("Telegram Bot 初始化完成")

    def _setup_handlers(self, application: Application) -> None:
        self._handlers["command"] = AgentCommandHandler(
            agent_core=self.agent_core,
            session_manager=self.session_manager,
            reply_manager=self.reply_manager
        )
        self._handlers["message"] = AgentMessageHandler(
            agent_core=self.agent_core,
            session_manager=self.session_manager,
            reply_manager=self.reply_manager,
            message_parser=self.message_parser
        )
        self._handlers["callback"] = AgentCallbackQueryHandler(
            agent_core=self.agent_core,
            session_manager=self.session_manager,
            reply_manager=self.reply_manager
        )

        application.add_handler(CommandHandler("start", self._handlers["command"].start))
        application.add_handler(CommandHandler("help", self._handlers["command"].help))
        application.add_handler(CommandHandler("reset", self._handlers["command"].reset))
        application.add_handler(CommandHandler("status", self._handlers["command"].status))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handlers["message"].handle))
        application.add_handler(CallbackQueryHandler(self._handlers["callback"].handle))

    async def start(self) -> None:
        if self._running:
            logger.warning("Telegram Bot 已在运行中")
            return

        logger.info("正在启动 Telegram Bot...")
        self.application = Application.builder().token(self.token).post_init(self._post_init).build()
        self._running = True
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Telegram Bot 已启动")

    async def stop(self) -> None:
        if not self._running or self.application is None:
            logger.warning("Telegram Bot 未在运行")
            return

        logger.info("正在停止 Telegram Bot...")
        await self.application.updater.stop_pipeline()
        await self.application.stop()
        await self.application.shutdown()
        self._running = False
        logger.info("Telegram Bot 已停止")

    async def process_update(self, update: Update) -> None:
        if self.application is None:
            raise RuntimeError("Telegram Bot 未初始化")
        await self.application.process_update(update)

    @property
    def is_running(self) -> bool:
        return self._running
