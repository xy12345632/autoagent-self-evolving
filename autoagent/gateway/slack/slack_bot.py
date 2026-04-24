import asyncio
from typing import Any, Optional, Dict

from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest

from ..utils.logger import get_logger

logger = get_logger("slack_bot")


class SlackBot:
    def __init__(self, token: str, signing_secret: str, agent_core: Any):
        self.token = token
        self.signing_secret = signing_secret
        self.agent_core = agent_core

        self.client = WebClient(token=token)
        self.socket_client: Optional[SocketModeClient] = None

        from .handlers import SlackMessageHandler, SlackCommandHandler
        from .session_manager import SlackSessionManager

        self.session_manager = SlackSessionManager()
        self.message_handler = SlackMessageHandler(agent_core, self.session_manager)
        self.command_handler = SlackCommandHandler(agent_core, self.session_manager)

    def start(self) -> None:
        logger.info("Starting Slack bot...")

        self.socket_client = SocketModeClient(
            app_token=self.signing_secret,
            web_client=self.client,
            message_handler=self._handle_socket_event,
        )

        self.socket_client.socket_mode_request_listeners.append(self._on_socket_mode_request)
        self.socket_client.connect()

        logger.info("Slack bot started successfully")

        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down Slack bot...")
            self.stop()

    def stop(self) -> None:
        if self.socket_client:
            self.socket_client.close()
            logger.info("Slack bot stopped")

    def _handle_socket_event(self, client: SocketModeClient, req: SocketModeRequest) -> None:
        if req.type == "events_api":
            event = req.payload.get("event", {})
            asyncio.create_task(self.handle_event(event))
        elif req.type == "slash_commands":
            asyncio.create_task(self._handle_command(req))

    async def handle_event(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type")

        if event_type == "message":
            await self.message_handler.handle(event)
        elif event_type == "app_mention":
            await self.message_handler.handle(event)
        elif event_type == "reaction_added":
            await self._handle_reaction(event)

    async def _handle_command(self, req: SocketModeRequest) -> None:
        command = req.payload
        await self.command_handler.handle(command)

    async def _handle_reaction(self, event: Dict[str, Any]) -> None:
        user = event.get("user")
        channel = event.get("item", {}).get("channel")
        reaction = event.get("reaction")

        logger.debug(f"Reaction {reaction} from user {user} in channel {channel}")
