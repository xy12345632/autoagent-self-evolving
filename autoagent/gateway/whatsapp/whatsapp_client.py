import asyncio
import time
from typing import Any, Dict, Optional

from ..utils.logger import get_logger

logger = get_logger("whatsapp_client")


class WhatsAppClient:
    def __init__(self, phone_number_id: str, access_token: str, agent_core: Any):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.agent_core = agent_core

        self._webhook_server: Optional[Any] = None
        self._running = False

        from .handlers import WhatsAppTextHandler, WhatsAppMediaHandler, WhatsAppVoiceHandler
        from .session_manager import WhatsAppSessionManager

        self.session_manager = WhatsAppSessionManager()
        self.text_handler = WhatsAppTextHandler(agent_core, self.session_manager)
        self.media_handler = WhatsAppMediaHandler(agent_core, self.session_manager)
        self.voice_handler = WhatsAppVoiceHandler(agent_core, self.session_manager)

    def start(self, webhook_path: str = "/webhook/whatsapp") -> None:
        logger.info("Starting WhatsApp client...")

        try:
            from aiohttp import web

            async def webhook_handler(request: web.Request) -> web.Response:
                body = await request.json()
                await self.process_message(body)
                return web.Response(status=200)

            self._webhook_server = web.Application()
            self._webhook_server.router.add_post(webhook_path, webhook_handler)

            runner = web.AppRunner(self._webhook_server)
            asyncio.get_event_loop().run_until_complete(runner.setup())
            site = web.TCPSite(runner, "0.0.0.0", 5000)
            asyncio.get_event_loop().run_until_complete(site.start())

            self._running = True
            logger.info(f"WhatsApp webhook server started on port 5000 {webhook_path}")

            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down WhatsApp client...")
            self.stop()

    def stop(self) -> None:
        self._running = False
        if self._webhook_server:
            logger.info("WhatsApp client stopped")

    async def process_message(self, message: Dict[str, Any]) -> None:
        entry = message.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        if "messages" not in value:
            return

        messages = value.get("messages", [])
        for msg in messages:
            msg_type = msg.get("type", "text")
            from_number = msg.get("from")
            timestamp = msg.get("timestamp")

            session = self.session_manager.get_or_create_session(from_number)
            session.add_message("user", f"[{msg_type}] message", {"timestamp": timestamp})

            logger.debug(f"Processing {msg_type} message from {from_number}")

            try:
                if msg_type == "text":
                    await self.text_handler.handle(msg, session)
                elif msg_type in ["image", "video", "document"]:
                    await self.media_handler.handle(msg, session)
                elif msg_type == "audio":
                    await self.voice_handler.handle(msg, session)
                else:
                    await self._handle_unsupported(msg_type, from_number)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                await self._send_text_message(from_number, "抱歉，处理消息时出现错误。")

    async def _handle_unsupported(self, msg_type: str, to_number: str) -> None:
        await self._send_text_message(
            to_number, f"暂不支持的消息类型: {msg_type}"
        )

    async def _send_text_message(self, to_number: str, text: str) -> None:
        url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "text": {"body": text},
        }

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        logger.warning(f"Failed to send message: {await resp.text()}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def send_message(self, to_number: str, text: str, metadata: Optional[Dict] = None) -> bool:
        session = self.session_manager.get_or_create_session(to_number)
        session.add_message("assistant", text, metadata)

        await self._send_text_message(to_number, text)
        return True
