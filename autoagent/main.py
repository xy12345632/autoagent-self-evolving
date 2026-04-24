"""
AutoAgent 主入口
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path

# 设置编码以支持中文
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import rich.console
from rich.logging import RichHandler

sys.path.insert(0, str(Path(__file__).parent.parent))

from autoagent.config.config_manager import ConfigManager
from autoagent.memory.memory_manager import MemoryManager
from autoagent.skills.skill_manager import SkillManager
from autoagent.tools.tool_registry import ToolRegistry
from autoagent.tools.tool_executor import ToolExecutor
from autoagent.api.router import ModelRouter
from autoagent.api.opencode_zen import OpenCodeZenProvider
from autoagent.api.openrouter import OpenRouterProvider
from autoagent.core.agent import AutoAgent
from autoagent.gateway.cli.cli_interface import CLIInterface
from autoagent.utils.paths import GlobalPaths


console = rich.console.Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("autoagent")


def print_welcome():
    console.print("[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
    console.print("[bold green]  🤖 AutoAgent - 自进化个人AI Agent[/bold green]")
    console.print("[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
    console.print("")
    console.print("[cyan]欢迎使用AutoAgent！这是您的个人AI助手。[/cyan]")
    console.print("")
    console.print("[yellow]功能特性：[/yellow]")
    console.print("  🧠 [white]持久记忆[/white] - 跨会话记忆您的偏好和知识")
    console.print("  📚 [white]技能系统[/white] - 自动学习和创建新技能")
    console.print("  🛠️ [white]40+工具[/white] - 网页搜索、代码执行、文件操作等")
    console.print("  💬 [white]多平台[/white] - CLI交互")
    console.print("  🔄 [white]自进化[/white] - 越用越聪明")
    console.print("")
    console.print("[yellow]常用命令：[/yellow]")
    console.print("  [green]/help[/green]   - 显示帮助")
    console.print("  [green]/clear[/green] - 清除对话历史")
    console.print("  [green]/memory[/green]- 查看记忆状态")
    console.print("  [green]/skills[/green]- 查看已学技能")
    console.print("  [green]/exit[/green]  - 退出程序")
    console.print("")
    console.print("[dim]━[/dim]" * 50)


async def init_agent() -> AutoAgent:
    GlobalPaths.ensure_directories()
    GlobalPaths.migrate_data_if_needed()

    logger.info("正在初始化组件...")

    config_manager = ConfigManager()
    logger.info("✓ 配置管理器已初始化")

    memory_manager = MemoryManager()
    memory_manager.init_memory_files()
    logger.info("✓ 记忆系统已初始化")

    skill_manager = SkillManager()
    skill_manager.loader.discover_skills()
    logger.info("✓ 技能系统已初始化")

    tool_registry = ToolRegistry()
    tool_executor = ToolExecutor(tool_registry)
    logger.info("✓ 工具系统已初始化")

    api_key = config_manager.get_api_key("opencode_zen")
    opencode_zen_config = config_manager.get_config("model_providers", "opencode_zen")

    opencode_zen_provider = OpenCodeZenProvider(
        api_key=api_key,
        base_url="https://opencode.ai/zen/v1"
    )
    logger.info("✓ OpenCode Zen API已连接")

    openrouter_api_key = config_manager.get_api_key("openrouter")
    openrouter_config = config_manager.get_config("model_providers", "openrouter")
    openrouter_provider = OpenRouterProvider(
        api_key=openrouter_api_key,
        base_url=openrouter_config.get("endpoint", "https://openrouter.ai/api/v1")
    )
    logger.info("✓ OpenRouter API已连接")

    providers = {
        "opencode_zen": opencode_zen_provider,
        "openrouter": openrouter_provider
    }

    router = ModelRouter(providers, default_preference="opencode_zen")
    logger.info("✓ 模型路由器已初始化")

    agent = AutoAgent(
        config_manager=config_manager,
        memory_manager=memory_manager,
        skill_manager=skill_manager,
        tool_executor=tool_executor,
        model_router=router
    )
    agent.start()
    logger.info("✓ Agent已启动")

    return agent


async def main() -> None:
    console.print("[bold green]AutoAgent[/bold green] 自进化个人AI Agent启动中...")
    logger.info("AutoAgent 启动中...")

    try:
        agent = await init_agent()
        print_welcome()

        cli = CLIInterface(
            memory_manager=agent.memory_manager,
            skill_manager=agent.skill_manager,
            config_manager=agent.config_manager,
            agent=agent,
            message_handler=agent.process_message_async
        )

        await cli.start()

    except KeyboardInterrupt:
        console.print("\n[yellow]收到中断信号，正在关闭...[/yellow]")
    except Exception as e:
        console.print(f"[bold red]错误:[/bold red] {e}")
        console.print(f"[red]{traceback.format_exc()}[/red]")
        logger.error(f"启动失败: {e}")
        logger.error(traceback.format_exc())
    finally:
        console.print("[green]感谢使用AutoAgent，再见！[/green]")


if __name__ == "__main__":
    asyncio.run(main())


def main_sync() -> None:
    """同步入口点，用于命令行工具"""
    asyncio.run(main())
