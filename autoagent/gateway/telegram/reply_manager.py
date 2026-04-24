from typing import Optional

from telegram import InlineKeyboardMarkup, Message
from telegram.constants import ParseMode
from telegram.ext import Bot

from ..utils.logger import get_logger

logger = get_logger("reply_manager")


class ReplyManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self._max_message_length = 4096

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_web_page_preview: bool = True,
    ) -> Optional[Message]:
        try:
            if len(text) > self._max_message_length:
                text = text[: self._max_message_length - 3] + "..."

            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
            )
            logger.debug(f"发送消息到 {chat_id}: {text[:50]}...")
            return message

        except Exception as e:
            logger.error(f"发送消息失败: chat_id={chat_id}, error={e}")
            return None

    async def send_typing_action(self, chat_id: int) -> None:
        try:
            await self.bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception as e:
            logger.error(f"发送typing状态失败: chat_id={chat_id}, error={e}")

    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Optional[Message]:
        try:
            if len(text) > self._max_message_length:
                text = text[: self._max_message_length - 3] + "..."

            message = await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
            logger.debug(f"编辑消息 {message_id}: {text[:50]}...")
            return message

        except Exception as e:
            logger.error(f"编辑消息失败: chat_id={chat_id}, message_id={message_id}, error={e}")
            return None

    async def send_photo(
        self,
        chat_id: int,
        photo: str,
        caption: Optional[str] = None,
        parse_mode: str = ParseMode.MARKDOWN,
    ) -> Optional[Message]:
        try:
            message = await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
            )
            logger.debug(f"发送图片到 {chat_id}")
            return message

        except Exception as e:
            logger.error(f"发送图片失败: chat_id={chat_id}, error={e}")
            return None

    async def send_document(
        self,
        chat_id: int,
        document: str,
        caption: Optional[str] = None,
    ) -> Optional[Message]:
        try:
            message = await self.bot.send_document(
                chat_id=chat_id,
                document=document,
                caption=caption,
            )
            logger.debug(f"发送文档到 {chat_id}")
            return message

        except Exception as e:
            logger.error(f"发送文档失败: chat_id={chat_id}, error={e}")
            return None

    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.debug(f"删除消息 {message_id}")
            return True

        except Exception as e:
            logger.error(f"删除消息失败: chat_id={chat_id}, message_id={message_id}, error={e}")
            return False

    async def reply_with_keyboard(
        self,
        chat_id: int,
        text: str,
        keyboard: list[list[dict]],
        parse_mode: str = ParseMode.MARKDOWN,
    ) -> Optional[Message]:
        from telegram import InlineKeyboardButton

        buttons = [
            [InlineKeyboardButton(**btn) for btn in row] for row in keyboard
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        return await self.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
