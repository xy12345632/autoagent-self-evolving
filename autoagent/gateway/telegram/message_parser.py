import re
from typing import Optional

from telegram import Update

from ..utils.logger import get_logger

logger = get_logger("message_parser")


class MessageParser:
    def __init__(self):
        self._command_pattern = re.compile(r"^/(\w+)(@[\w_]+)?(?:\s+(.*))?$")
        self._mention_pattern = re.compile(r"@[\w_]+")

    def parse_message(self, text: str) -> dict:
        result = {
            "is_command": False,
            "command": None,
            "args": None,
            "mentions": [],
            "clean_text": text,
            "is_voice_processed": False,
            "processed_text": None,
        }

        if not text:
            return result

        command_match = self._command_pattern.match(text.strip())
        if command_match:
            result["is_command"] = True
            result["command"] = command_match.group(1)
            result["args"] = command_match.group(3)
            result["clean_text"] = ""
            logger.debug(f"解析命令: {result['command']}, 参数: {result['args']}")

        mentions = self._mention_pattern.findall(text)
        result["mentions"] = mentions

        return result

    def extract_command(self, text: str) -> Optional[str]:
        if not text:
            return None

        match = self._command_pattern.match(text.strip())
        if match:
            return match.group(1)
        return None

    def detect_voice_message(self, update: Update) -> bool:
        if update.message is None:
            return False

        has_voice = update.message.voice is not None
        has_audio = update.message.audio is not None
        has_video_note = update.message.video_note is not None

        is_voice = has_voice or has_audio or has_video_note

        if is_voice:
            logger.debug(
                f"检测到语音/音频消息: voice={has_voice}, audio={has_audio}, "
                f"video_note={has_video_note}"
            )

        return is_voice

    async def get_voice_transcription(
        self, update: Update, transcription_service: Optional[callable] = None
    ) -> Optional[str]:
        if not self.detect_voice_message(update):
            return None

        message = update.message
        if message is None:
            return None

        file = None
        if message.voice:
            file = await message.voice.get_file()
        elif message.audio:
            file = await message.audio.get_file()
        elif message.video_note:
            file = await message.video_note.get_file()

        if file is None:
            return None

        if transcription_service:
            try:
                audio_data = await file.download_as_byte_array()
                text = await transcription_service(audio_data)
                logger.info(f"语音转文字成功: {text[:50]}...")
                return text
            except Exception as e:
                logger.error(f"语音转文字失败: {e}")

        return None

    def extract_intent(self, text: str) -> dict:
        text_lower = text.lower()
        intents = {
            "greeting": any(
                word in text_lower
                for word in ["你好", "hello", "hi", "嗨", "您好"]
            ),
            "question": "?" in text or "？" in text,
            "request": any(
                word in text_lower
                for word in ["帮我", "请", "能不能", "可以帮我", "would you"]
            ),
            "goodbye": any(
                word in text_lower for word in ["再见", "拜拜", "bye", "下次见"]
            ),
        }
        return intents

    def parse_args(self, text: str) -> dict:
        args = {"positional": [], "named": {}}

        if not text:
            return args

        parts = text.split()
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                args["named"][key] = value
            else:
                args["positional"].append(part)

        return args
