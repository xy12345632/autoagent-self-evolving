from typing import Any, Dict, Optional

from ..utils.logger import get_logger
from .session_manager import WhatsAppSession

logger = get_logger("whatsapp_handlers")


class WhatsAppTextHandler:
    def __init__(self, agent_core: Any, session_manager: Any):
        self.agent_core = agent_core
        self.session_manager = session_manager

    async def handle(self, message: Dict[str, Any], session: WhatsAppSession) -> None:
        text = message.get("text", {}).get("body", "")
        msg_id = message.get("id")

        if not text:
            return

        session.add_message("user", text, {"message_id": msg_id, "type": "text"})
        logger.debug(f"Handling text message: {text[:50]}...")

        try:
            response = await self._process_with_agent(session, text)
            session.add_message("assistant", response)

            from_number = message.get("from")
            await self._send_response(from_number, response)
        except Exception as e:
            logger.error(f"Error handling text message: {e}", exc_info=True)
            from_number = message.get("from")
            await self._send_response(from_number, "抱歉，处理消息时出现错误。")

    async def _process_with_agent(self, session: WhatsAppSession, text: str) -> str:
        if hasattr(self.agent_core, "process_message"):
            return await self.agent_core.process_message(
                text, context={"platform": "whatsapp", "session": session}
            )
        return f"收到消息: {text}"

    async def _send_response(self, to_number: str, text: str) -> None:
        from .whatsapp_client import WhatsAppClient

        if isinstance(self.agent_core, WhatsAppClient):
            await self.agent_core._send_text_message(to_number, text)


class WhatsAppMediaHandler:
    def __init__(self, agent_core: Any, session_manager: Any):
        self.agent_core = agent_core
        self.session_manager = session_manager

    async def handle(self, message: Dict[str, Any], session: WhatsAppSession) -> None:
        msg_type = message.get("type")
        msg_id = message.get("id")
        from_number = message.get("from")

        media_id = message.get(msg_type, {}).get("id")
        mime_type = message.get(msg_type, {}).get("mime_type")
        caption = message.get(msg_type, {}).get("caption", "")

        session.add_message("user", f"[{msg_type}] {caption or 'media'}", {
            "message_id": msg_id,
            "type": msg_type,
            "media_id": media_id,
        })

        logger.debug(f"Handling {msg_type} message from {from_number}")

        try:
            media_url = await self._download_media(media_id) if media_id else None

            if hasattr(self.agent_core, "process_media"):
                response = await self.agent_core.process_media(
                    media_url=media_url,
                    media_type=msg_type,
                    caption=caption,
                    context={"platform": "whatsapp", "session": session}
                )
            else:
                response = await self._default_media_response(msg_type, caption)

            session.add_message("assistant", response)
            await self._send_response(from_number, response)
        except Exception as e:
            logger.error(f"Error handling media: {e}", exc_info=True)
            await self._send_response(from_number, "抱歉，处理媒体消息时出现错误。")

    async def _download_media(self, media_id: str) -> Optional[str]:
        try:
            import aiohttp

            if isinstance(self.agent_core, type):
                return None

            access_token = getattr(self.agent_core, "access_token", None)
            phone_number_id = getattr(self.agent_core, "phone_number_id", None)

            if not access_token or not phone_number_id:
                return None

            url = f"https://graph.facebook.com/v18.0/{media_id}"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("url")
        except Exception as e:
            logger.warning(f"Failed to download media: {e}")

        return None

    async def _default_media_response(self, media_type: str, caption: str) -> str:
        if caption:
            return f"收到您的{media_type}，附言: {caption}"
        return f"收到您的{media_type}，已处理。"

    async def _send_response(self, to_number: str, text: str) -> None:
        from .whatsapp_client import WhatsAppClient

        if isinstance(self.agent_core, WhatsAppClient):
            await self.agent_core._send_text_message(to_number, text)


class WhatsAppVoiceHandler:
    def __init__(self, agent_core: Any, session_manager: Any):
        self.agent_core = agent_core
        self.session_manager = session_manager

    async def handle(self, message: Dict[str, Any], session: WhatsAppSession) -> None:
        msg_id = message.get("id")
        from_number = message.get("from")

        audio_data = message.get("audio", {})
        audio_id = audio_data.get("id")

        session.add_message("user", "[voice message]", {
            "message_id": msg_id,
            "type": "audio",
            "audio_id": audio_id,
        })

        logger.debug(f"Handling voice message from {from_number}")

        try:
            transcription = await self._transcribe_audio(audio_id)

            if hasattr(self.agent_core, "process_voice"):
                response = await self.agent_core.process_voice(
                    transcription=transcription,
                    context={"platform": "whatsapp", "session": session}
                )
            else:
                response = await self._default_voice_response(transcription)

            session.add_message("assistant", response)
            await self._send_response(from_number, response)
        except Exception as e:
            logger.error(f"Error handling voice: {e}", exc_info=True)
            await self._send_response(from_number, "抱歉，处理语音消息时出现错误。")

    async def _transcribe_audio(self, audio_id: Optional[str]) -> Optional[str]:
        if not audio_id:
            return None

        try:
            import aiohttp

            if isinstance(self.agent_core, type):
                return None

            access_token = getattr(self.agent_core, "access_token", None)
            if not access_token:
                return None

            media_url = f"https://graph.facebook.com/v18.0/{audio_id}"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(media_url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        media_content_url = data.get("url")

                        if media_content_url:
                            async with session.get(media_content_url, headers=headers) as file_resp:
                                if file_resp.status == 200:
                                    audio_bytes = await file_resp.read()

                                    if hasattr(self.agent_core, "transcribe"):
                                        return await self.agent_core.transcribe(audio_bytes)

            return None
        except Exception as e:
            logger.warning(f"Failed to transcribe audio: {e}")
            return None

    async def _default_voice_response(self, transcription: Optional[str]) -> str:
        if transcription:
            return f"收到您的语音消息: {transcription}"
        return "收到您的语音消息，已处理。"

    async def _send_response(self, to_number: str, text: str) -> None:
        from .whatsapp_client import WhatsAppClient

        if isinstance(self.agent_core, WhatsAppClient):
            await self.agent_core._send_text_message(to_number, text)
