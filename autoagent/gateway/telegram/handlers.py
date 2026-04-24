from telegram import Update
from telegram.ext import ContextTypes

from ..utils.logger import get_logger
from .session_manager import SessionManager
from .reply_manager import ReplyManager
from .message_parser import MessageParser

logger = get_logger("telegram_handlers")


class CommandHandler:
    def __init__(
        self,
        agent_core: any,
        session_manager: SessionManager,
        reply_manager: ReplyManager,
    ):
        self.agent_core = agent_core
        self.session_manager = session_manager
        self.reply_manager = reply_manager

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        self.session_manager.create_session(user.id)
        welcome_message = (
            f"👋 你好 {user.first_name}！\n\n"
            "我是你的个人AI助手。\n"
            "你可以直接发送消息与我对话，或者使用以下命令：\n\n"
            "/help - 查看帮助\n"
            "/reset - 重置会话\n"
            "/status - 查看状态"
        )
        await self.reply_manager.send_message(user.id, welcome_message)
        logger.info(f"用户 {user.id} 启动了Bot")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        help_message = (
            "📖 **使用指南**\n\n"
            "**基本操作**\n"
            "• 直接发送消息与我对话\n"
            "• 发送语音消息，我会自动识别\n\n"
            "**可用命令**\n"
            "/start - 重新开始\n"
            "/help - 显示此帮助\n"
            "/reset - 清空当前会话历史\n"
            "/status - 查看当前状态\n\n"
            "**会话管理**\n"
            "• 我会记住对话上下文\n"
            "• 使用 /reset 可重新开始对话"
        )
        await self.reply_manager.send_message(user.id, help_message)

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        self.session_manager.clear_session(user.id)
        self.session_manager.create_session(user.id)
        await self.reply_manager.send_message(user.id, "🔄 会话已重置，让我们重新开始吧！")
        logger.info(f"用户 {user.id} 重置了会话")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        session = self.session_manager.get_session(user.id)
        message_count = len(session.messages) if session else 0
        status_message = (
            "📊 **状态信息**\n\n"
            f"用户ID: `{user.id}`\n"
            f"会话消息数: {message_count}\n"
            f"平台: Telegram"
        )
        await self.reply_manager.send_message(user.id, status_message)


class MessageHandler:
    def __init__(
        self,
        agent_core: any,
        session_manager: SessionManager,
        reply_manager: ReplyManager,
        message_parser: MessageParser,
    ):
        self.agent_core = agent_core
        self.session_manager = session_manager
        self.reply_manager = reply_manager
        self.message_parser = message_parser

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        text = update.message.text

        if not self.session_manager.get_session(user.id):
            self.session_manager.create_session(user.id)

        session = self.session_manager.get_session(user.id)
        session.add_message("user", text)

        await self.reply_manager.send_typing_action(user.id)

        parsed = self.message_parser.parse_message(text)
        command = self.message_parser.extract_command(text)

        if parsed.get("is_voice_processed"):
            text = parsed.get("processed_text", text)

        response = await self._get_agent_response(user.id, text, command)

        session.add_message("assistant", response)
        await self.reply_manager.send_message(user.id, response)
        logger.info(f"处理用户 {user.id} 消息: {text[:30]}... -> {response[:30]}...")

    async def _get_agent_response(
        self, user_id: int, text: str, command: str | None
    ) -> str:
        if hasattr(self.agent_core, "process_message"):
            result = await self.agent_core.process_message(
                text,
                context={"user_id": user_id, "platform": "telegram", "command": command}
            )
            return result.get("response", "抱歉，响应出现问题。")
        return "这是模拟响应，实际使用时将连接到Agent Core。"


class CallbackQueryHandler:
    def __init__(
        self,
        agent_core: any,
        session_manager: SessionManager,
        reply_manager: ReplyManager,
    ):
        self.agent_core = agent_core
        self.session_manager = session_manager
        self.reply_manager = reply_manager

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None:
            return

        user = update.effective_user
        data = query.data

        await query.answer()

        if data.startswith("action_"):
            action = data[7:]
            await self._handle_action(user.id, action, query)

    async def _handle_action(
        self, user_id: int, action: str, query: any
    ) -> None:
        action_handlers = {
            "cancel": "操作已取消",
            "confirm": "已确认操作",
            "retry": "正在重试...",
        }
        response = action_handlers.get(action, f"未知操作: {action}")
        await self.reply_manager.edit_message(
            query.message.chat_id,
            query.message.message_id,
            f"{response}\n\n_此为按钮回调示例_"
        )
