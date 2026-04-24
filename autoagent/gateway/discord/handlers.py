from typing import Any, Optional
import discord

from ..utils.logger import get_logger
from .session_manager import DiscordSessionManager
from .converter import MessageConverter

logger = get_logger("discord_handlers")


class DiscordHandlers:
    def __init__(
        self,
        agent_core: Any,
        session_manager: DiscordSessionManager,
        converter: MessageConverter,
    ):
        self.agent_core = agent_core
        self.session_manager = session_manager
        self.converter = converter
        self._prefix = "!"
        self._blocked_users: set[int] = set()

    async def on_ready(self) -> None:
        logger.info("Discord事件处理器已就绪")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.author.system:
            return

        if message.author.id in self._blocked_users:
            return

        if not self._should_respond(message):
            return

        try:
            internal_msg = self.converter.discord_to_internal(message)
            session = self.session_manager.get_or_create_session(
                guild_id=getattr(message.guild, "id", None),
                channel_id=message.channel.id,
                user_id=message.author.id,
            )
            session.add_message(internal_msg)

            thinking_msg = await message.channel.send("🤖 思考中...")
            response = await self._process_with_agent(session, internal_msg)
            await thinking_msg.delete()

            if response:
                formatted = self.converter.internal_to_discord(response)
                await message.channel.send(formatted)
                session.add_message({
                    "role": "assistant",
                    "content": response.get("content", ""),
                    "metadata": {"source": "discord"},
                })
            else:
                await message.channel.send("抱歉，处理消息时出现错误。")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            await message.channel.send(f"处理消息时出错: {str(e)}")

    async def on_command(self, ctx: discord.ApplicationContext, *args: str) -> None:
        command = args[0] if args else ""
        content = " ".join(args[1:]) if len(args) > 1 else ""

        logger.info(f"收到命令: {command} - 参数: {content}")

        if command == "ask":
            await self._handle_ask_command(ctx, content)
        elif command == "clear":
            await self._handle_clear_command(ctx)
        elif command == "history":
            await self._handle_history_command(ctx)
        elif command == "skills":
            await self._handle_skills_command(ctx)
        else:
            await ctx.respond(f"未知命令: {command}", ephemeral=True)

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.content == after.content:
            return

        logger.info(f"消息被编辑: {before.id} - {before.content[:50]} -> {after.content[:50]}")

        session = self.session_manager.find_session_by_message_id(before.id)
        if session:
            session.add_message({
                "role": "system",
                "content": f"[消息被编辑] 原始: {before.content} | 新: {after.content}",
                "metadata": {"edit_time": str(after.edited_at)},
            })

    async def _should_respond(self, message: discord.Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True

        if message.content.startswith(self._prefix):
            return False

        if self.bot_mentioned(message):
            return True

        return False

    def bot_mentioned(self, message: discord.Message) -> bool:
        if not message.guild:
            return True
        return any(
            isinstance(usr, discord.Member) and usr.id == message.guild.me.id
            for usr in message.mentions
        )

    async def _process_with_agent(self, session: Any, message: dict) -> Optional[dict]:
        try:
            if hasattr(self.agent_core, "process"):
                result = await self.agent_core.process(
                    message["content"],
                    context=session.get_context(),
                )
                return {"content": result}
            elif hasattr(self.agent_core, "run"):
                result = await self.agent_core.run(
                    message["content"],
                    context=session.get_context(),
                )
                return {"content": result}
            else:
                logger.warning("agent_core没有找到process或run方法")
                return {"content": "Agent核心模块接口不兼容"}
        except Exception as e:
            logger.error(f"Agent处理失败: {e}")
            return None

    async def _handle_ask_command(self, ctx: discord.ApplicationContext, content: str) -> None:
        if not content:
            await ctx.respond("请提供问题内容，例如: /ask 你好", ephemeral=True)
            return

        session = self.session_manager.get_or_create_session(
            guild_id=getattr(ctx.guild, "id", None) if ctx.guild else None,
            channel_id=ctx.channel_id,
            user_id=ctx.user.id,
        )

        await ctx.respond("🤖 处理中...", ephemeral=True)
        response = await self._process_with_agent(session, {"content": content})

        if response:
            await ctx.followup.send(self.converter.internal_to_discord(response))
        else:
            await ctx.followup.send("处理失败，请稍后重试。")

    async def _handle_clear_command(self, ctx: discord.ApplicationContext) -> None:
        session = self.session_manager.get_or_create_session(
            guild_id=getattr(ctx.guild, "id", None) if ctx.guild else None,
            channel_id=ctx.channel_id,
            user_id=ctx.user.id,
        )
        session.clear()
        await ctx.respond("会话已清除 ✅", ephemeral=True)

    async def _handle_history_command(self, ctx: discord.ApplicationContext) -> None:
        session = self.session_manager.get_or_create_session(
            guild_id=getattr(ctx.guild, "id", None) if ctx.guild else None,
            channel_id=ctx.channel_id,
            user_id=ctx.user.id,
        )
        history = session.get_history()

        if not history:
            await ctx.respond("暂无会话历史", ephemeral=True)
            return

        lines = []
        for msg in history[-10:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]
            lines.append(f"**{role}**: {content}...")

        await ctx.respond("\n".join(lines) or "暂无历史", ephemeral=True)

    async def _handle_skills_command(self, ctx: discord.ApplicationContext) -> None:
        skills = []
        if hasattr(self.agent_core, "get_skills"):
            skills = self.agent_core.get_skills()

        if not skills:
            await ctx.respond("当前无可用技能", ephemeral=True)
            return

        lines = [f"**可用技能 ({len(skills)}个)**\n"]
        for skill in skills:
            name = skill.get("name", "未知")
            desc = skill.get("description", "无描述")[:50]
            lines.append(f"• **{name}**: {desc}")

        await ctx.respond("\n".join(lines), ephemeral=True)

    def block_user(self, user_id: int) -> None:
        self._blocked_users.add(user_id)
        logger.info(f"已屏蔽用户: {user_id}")

    def unblock_user(self, user_id: int) -> None:
        self._blocked_users.discard(user_id)
        logger.info(f"已解除屏蔽用户: {user_id}")

    def is_blocked(self, user_id: int) -> bool:
        return user_id in self._blocked_users
