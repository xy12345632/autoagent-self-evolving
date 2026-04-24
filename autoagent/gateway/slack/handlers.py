from typing import Any, Dict, Optional

from ..utils.logger import get_logger
from .session_manager import SlackSession

logger = get_logger("slack_handlers")


class SlackMessageHandler:
    def __init__(self, agent_core: Any, session_manager: Any):
        self.agent_core = agent_core
        self.session_manager = session_manager

    async def handle(self, event: Dict[str, Any]) -> None:
        if event.get("subtype") == "bot_message":
            return

        user = event.get("user")
        channel = event.get("channel")
        text = event.get("text", "")
        thread_ts = event.get("thread_ts")

        workspace = self._get_workspace(event)

        session = self.session_manager.get_or_create_session(workspace, user, channel)

        if thread_ts:
            session.add_message("user", text, {"thread_ts": thread_ts, "is_thread": True})
        else:
            session.add_message("user", text)

        logger.debug(f"Handling message from {user} in {channel}: {text[:50]}...")

        try:
            response = await self._process_with_agent(session, text)
            session.add_message("assistant", response)

            await self._send_response(channel, response, thread_ts)
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await self._send_response(channel, "抱歉，处理消息时出现错误。", thread_ts)

    async def _process_with_agent(self, session: SlackSession, text: str) -> str:
        if hasattr(self.agent_core, "process_message"):
            return await self.agent_core.process_message(
                text, context={"platform": "slack", "session": session}
            )

        return f"收到消息: {text}"

    async def _send_response(
        self, channel: str, text: str, thread_ts: Optional[str] = None
    ) -> None:
        from .slack_bot import SlackBot

        if isinstance(self.agent_core, SlackBot):
            client = self.agent_core.client
            payload = {
                "channel": channel,
                "text": text,
            }
            if thread_ts:
                payload["thread_ts"] = thread_ts

            client.chat_postMessage(**payload)


class SlackCommandHandler:
    def __init__(self, agent_core: Any, session_manager: Any):
        self.agent_core = agent_core
        self.session_manager = session_manager

    async def handle(self, command: Dict[str, Any]) -> None:
        command_type = command.get("command", "")
        user = command.get("user_id")
        channel = command.get("channel_id")
        text = command.get("text", "")

        workspace = command.get("team_id", "default")

        logger.info(f"Handling command {command_type} from {user}")

        session = self.session_manager.get_or_create_session(workspace, user, channel)
        session.add_message("user", f"/{command_type} {text}", {"command": command_type})

        response = await self._process_command(command_type, text, session)

        await self._send_response(command, response)

    async def _process_command(
        self, command_type: str, text: str, session: SlackSession
    ) -> str:
        if command_type == "/help":
            return self._get_help_text()
        elif command_type == "/clear":
            session.clear_history()
            return "对话历史已清除。"
        elif command_type == "/stats":
            return self._get_stats_text(session)
        else:
            if hasattr(self.agent_core, "process_command"):
                return await self.agent_core.process_command(command_type, text)
            return f"未知命令: {command_type}"

    def _get_help_text(self) -> str:
        return """可用命令:
/help - 显示此帮助信息
/clear - 清除对话历史
/stats - 显示对话统计"""

    def _get_stats_text(self, session: SlackSession) -> str:
        message_count = len(session.messages)
        return f"""对话统计:
- 消息数: {message_count}
- 会话时长: {session.last_activity - session.created_at:.0f}秒"""

    async def _send_response(self, command: Dict[str, Any], text: str) -> None:
        from .slack_bot import SlackBot

        if isinstance(self.agent_core, SlackBot):
            client = self.agent_core.client
            client.api_call(
                "api/chat.postMessage",
                {
                    "channel": command.get("channel_id"),
                    "text": text,
                    "response_type": "ephemeral",
                },
            )

    def _get_workspace(self, event: Dict[str, Any]) -> str:
        return event.get("team", "default")
