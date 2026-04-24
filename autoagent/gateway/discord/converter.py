from typing import Any, Optional
import discord

from ..utils.logger import get_logger

logger = get_logger("discord_converter")


class MessageConverter:
    def __init__(self):
        self._max_message_length = 2000
        self._max_embed_length = 4096

    def discord_to_internal(self, message: discord.Message) -> dict[str, Any]:
        content = self._clean_content(message.content)

        attachments = self.handle_attachments(message)

        return {
            "role": "user",
            "content": content,
            "message_id": message.id,
            "author": {
                "id": message.author.id,
                "name": message.author.name,
                "display_name": message.author.display_name,
                "is_bot": message.author.bot,
            },
            "channel": {
                "id": message.channel.id,
                "name": getattr(message.channel, "name", "DM"),
                "is_dm": isinstance(message.channel, discord.DMChannel),
            },
            "guild": {
                "id": message.guild.id if message.guild else None,
                "name": message.guild.name if message.guild else None,
            } if message.guild else None,
            "attachments": attachments,
            "timestamp": message.created_at.isoformat(),
            "edited_timestamp": message.edited_at.isoformat() if message.edited_at else None,
            "reference": self._get_reference_info(message.reference) if message.reference else None,
            "metadata": {
                "type": str(message.type),
                "is_mentioning_bot": self._is_mentioning_bot(message),
            },
        }

    def _clean_content(self, content: str) -> str:
        if not content:
            return ""

        content = content.strip()

        content = self._remove_self_mentions(content)

        return content

    def _remove_self_mentions(self, content: str) -> str:
        import re
        mention_pattern = r"<@!?\d+>"
        mentions = re.findall(mention_pattern, content)

        for mention in mentions:
            content = content.replace(mention, "")

        return content.strip()

    def _is_mentioning_bot(self, message: discord.Message) -> bool:
        if not message.guild:
            return False
        return any(
            isinstance(usr, discord.Member) and usr.id == message.guild.me.id
            for usr in message.mentions
        )

    def _get_reference_info(self, reference: discord.MessageReference) -> dict[str, Any]:
        return {
            "message_id": reference.message_id,
            "channel_id": reference.channel_id,
            "guild_id": reference.guild_id,
        }

    def internal_to_discord(self, response: dict[str, Any]) -> str:
        content = response.get("content", "")

        if not content:
            return "**[无内容返回]**"

        return self._format_for_discord(content)

    def _format_for_discord(self, content: str) -> str:
        import re

        code_block_pattern = r"```(\w+)?\n(.*?)```"
        content = re.sub(code_block_pattern, self._escape_code_block, content, flags=re.DOTALL)

        bold_pattern = r"\*\*(.+?)\*\*"
        content = re.sub(bold_pattern, r"**\1**", content)

        italic_pattern = r"\*(.+?)\*"
        content = re.sub(italic_pattern, r"_\1_", content)

        lines = content.split("\n")
        formatted_lines = []
        for line in lines:
            if line.strip() and not line.startswith("```"):
                if len(line) > self._max_embed_length:
                    line = line[: self._max_embed_length - 3] + "..."
            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _escape_code_block(self, match: re.Match) -> str:
        lang = match.group(1) or ""
        code = match.group(2)
        if len(code) > self._max_embed_length - 10:
            code = code[: self._max_embed_length - 10] + "\n    ..."
        return f"```{lang}\n{code}```"

    def handle_attachments(self, message: discord.Message) -> list[dict[str, Any]]:
        if not message.attachments:
            return []

        processed = []
        for attachment in message.attachments:
            info = {
                "id": attachment.id,
                "filename": attachment.filename,
                "content_type": attachment.content_type,
                "size": attachment.size,
                "url": attachment.url,
                "is_image": attachment.width is not None,
            }

            if attachment.width:
                info["width"] = attachment.width
                info["height"] = attachment.height

            if attachment.content_type and attachment.content_type.startswith("image/"):
                info["type"] = "image"
            elif attachment.content_type and attachment.content_type.startswith("video/"):
                info["type"] = "video"
            elif attachment.content_type and attachment.content_type.startswith("audio/"):
                info["type"] = "audio"
            else:
                info["type"] = "file"

            processed.append(info)

        logger.debug(f"处理了 {len(processed)} 个附件")
        return processed

    def create_embed(
        self,
        title: str,
        description: str,
        color: Optional[int] = None,
        fields: Optional[list[dict[str, Any]]] = None,
        footer: Optional[str] = None,
    ) -> discord.Embed:
        if color is None:
            color = 0x7289DA

        embed = discord.Embed(title=title, description=description, color=color)

        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", False),
                )

        if footer:
            embed.set_footer(text=footer)

        return embed

    def split_long_message(self, content: str, max_length: int = None) -> list[str]:
        if max_length is None:
            max_length = self._max_message_length

        if len(content) <= max_length:
            return [content]

        parts = []
        lines = content.split("\n")
        current = []
        current_length = 0

        for line in lines:
            line_length = len(line) + 1
            if current_length + line_length > max_length:
                if current:
                    parts.append("\n".join(current))
                    current = [line]
                    current_length = line_length
                else:
                    parts.append(line[:max_length])
                    current_length = 0
            else:
                current.append(line)
                current_length += line_length

        if current:
            parts.append("\n".join(current))

        return parts

    def format_user_info(self, user: discord.User | discord.Member) -> str:
        return f"**{user.display_name}** ({user.name})"

    def format_channel_info(self, channel: discord.TextChannel) -> str:
        return f"**#{channel.name}**"

    def format_guild_info(self, guild: discord.Guild) -> str:
        return f"**{guild.name}**"
