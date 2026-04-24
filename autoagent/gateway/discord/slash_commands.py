from typing import Any, Optional
import discord

from ..utils.logger import get_logger
from .session_manager import DiscordSessionManager
from .converter import MessageConverter

logger = get_logger("discord_slash")


async def setup_slash_commands(
    bot: discord.Client,
    agent_core: Any,
    session_manager: DiscordSessionManager,
) -> None:
    converter = MessageConverter()

    @bot.tree.command(name="ask", description="向AI提问")
    async def ask_command(interaction: discord.Interaction, *, question: str):
        if not interaction.user:
            await interaction.response.send_message("无法识别用户", ephemeral=True)
            return

        session = session_manager.get_or_create_session(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            user_id=interaction.user.id,
        )

        await interaction.response.send_message("🤖 思考中...", ephemeral=True)

        try:
            response = await _process_with_agent(agent_core, session, question)
            if response:
                formatted = converter.internal_to_discord(response)
                parts = converter.split_long_message(formatted)

                await interaction.edit_original_response(content="✅ 回复:")
                for part in parts:
                    await interaction.followup.send(part)
            else:
                await interaction.edit_original_response(content="处理失败，请稍后重试。")
        except Exception as e:
            logger.error(f"/ask 命令执行失败: {e}")
            await interaction.edit_original_response(content=f"执行出错: {str(e)}")

    @bot.tree.command(name="clear", description="清除当前会话历史")
    async def clear_command(interaction: discord.Interaction):
        if not interaction.user:
            await interaction.response.send_message("无法识别用户", ephemeral=True)
            return

        session = session_manager.get_or_create_session(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            user_id=interaction.user.id,
        )

        session.clear()
        await interaction.response.send_message("会话已清除 ✅", ephemeral=True)

    @bot.tree.command(name="history", description="查看最近会话历史")
    async def history_command(interaction: discord.Interaction, limit: int = 10):
        if not interaction.user:
            await interaction.response.send_message("无法识别用户", ephemeral=True)
            return

        session = session_manager.get_or_create_session(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            user_id=interaction.user.id,
        )

        history = session.get_history(limit=limit)

        if not history:
            await interaction.response.send_message("暂无会话历史", ephemeral=True)
            return

        lines = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:80]
            lines.append(f"**{role}**: {content}...")

        content = "\n".join(lines) or "暂无历史"
        parts = converter.split_long_message(content, max_length=1500)

        await interaction.response.send_message("📜 会话历史:", ephemeral=True)
        for part in parts:
            await interaction.followup.send(part, ephemeral=True)

    @bot.tree.command(name="skills", description="查看可用技能列表")
    async def skills_command(interaction: discord.Interaction):
        skills = []
        if hasattr(agent_core, "get_skills"):
            skills = agent_core.get_skills()
        elif hasattr(agent_core, "skills"):
            skills = agent_core.skills

        if not skills:
            await interaction.response.send_message("当前无可用技能", ephemeral=True)
            return

        lines = [f"**可用技能 ({len(skills)}个)**\n"]
        for skill in skills:
            name = skill.get("name", "未知")
            desc = skill.get("description", "无描述")[:60]
            lines.append(f"• **{name}**: {desc}")

        content = "\n".join(lines)
        parts = converter.split_long_message(content, max_length=1500)

        for i, part in enumerate(parts):
            if i == 0:
                await interaction.response.send_message(part, ephemeral=True)
            else:
                await interaction.followup.send(part, ephemeral=True)

    @bot.tree.command(name="ping", description="检查Bot状态")
    async def ping_command(interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        await interaction.response.send_message(
            f"🏓 Pong! 延迟: {latency}ms",
            ephemeral=True,
        )

    @bot.tree.command(name="stats", description="查看会话统计")
    async def stats_command(interaction: discord.Interaction):
        stats = session_manager.get_stats()

        embed = converter.create_embed(
            title="📊 会话统计",
            description="当前会话统计信息",
            fields=[
                {"name": "总会话数", "value": str(stats["total_sessions"]), "inline": True},
                {"name": "活跃用户", "value": str(stats["active_users"]), "inline": True},
                {"name": "活跃频道", "value": str(stats["active_channels"]), "inline": True},
            ],
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="help", description="获取帮助信息")
    async def help_command(interaction: discord.Interaction):
        help_text = """
**🤖 AI Agent Bot 帮助**

**斜杠命令:**
• `/ask <问题>` - 向AI提问
• `/clear` - 清除当前会话
• `/history [数量]` - 查看会话历史
• `/skills` - 查看可用技能
• `/ping` - 检查Bot状态
• `/stats` - 查看会话统计

**使用方式:**
• 在频道中直接 @提问题
• 发送私信进行对话
• 使用 `/ask` 命令获得更快响应

**提示:** 回复较长时会自动分段发送
        """.strip()

        await interaction.response.send_message(help_text, ephemeral=True)

    await bot.tree.sync()
    logger.info("Slash命令注册完成并已同步")


async def _process_with_agent(
    agent_core: Any,
    session: Any,
    message: str,
) -> Optional[dict]:
    try:
        session.add_message({
            "role": "user",
            "content": message,
            "metadata": {"source": "discord_slash"},
        })

        if hasattr(agent_core, "process"):
            result = await agent_core.process(
                message,
                context=session.get_context(),
            )
            return {"content": result}
        elif hasattr(agent_core, "run"):
            result = await agent_core.run(
                message,
                context=session.get_context(),
            )
            return {"content": result}
        else:
            logger.warning("agent_core没有找到process或run方法")
            return {"content": "Agent核心模块接口不兼容"}
    except Exception as e:
        logger.error(f"Agent处理失败: {e}")
        return None


class SlashCommandBuilder:
    def __init__(self):
        self._commands: list[dict[str, Any]] = []

    def add_command(
        self,
        name: str,
        description: str,
        options: Optional[list[dict[str, Any]]] = None,
    ) -> "SlashCommandBuilder":
        self._commands.append({
            "name": name,
            "description": description,
            "options": options or [],
        })
        return self

    def build(self) -> list[dict[str, Any]]:
        return self._commands
