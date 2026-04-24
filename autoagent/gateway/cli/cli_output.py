"""
CLI Output Handling - CLI输出处理模块
"""

import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.live import Live


class CLIOutput:
    def __init__(self):
        self.console = Console()

    def print_welcome(self) -> None:
        welcome_text = """
# 欢迎使用 AutoAgent CLI

自进化个人AI Agent - 您的智能助手

**可用命令:**
- `/help` - 显示帮助信息
- `/exit` - 退出程序
- `/clear` - 清除屏幕
- `/history` - 显示历史记录
- `/skills` - 列出可用技能
- `/memory` - 内存管理
- `/config` - 配置管理

**使用技巧:**
- 多行输入: 使用 `\\` 续行
- Ctrl+D: 结束多行输入
- 方向键上下: 切换历史命令
        """
        md = Markdown(welcome_text)
        self.console.print(md)

    def print_response(self, text: str, style: str = "default") -> None:
        if style == "markdown":
            md = Markdown(text)
            self.console.print(md)
        elif style == "code":
            syntax = Syntax(text, "python", theme="monokai", line_numbers=True)
            self.console.print(syntax)
        else:
            self.console.print(text)

    async def print_stream(
        self,
        chunks: AsyncIterator[str],
        show_panel: bool = True
    ) -> str:
        """
        流式打印响应

        Args:
            chunks: 字符串块的异步迭代器
            show_panel: 是否显示面板

        Returns:
            完整的响应内容
        """
        content_parts = []

        if show_panel:
            panel = Panel("", title="AI 响应", border_style="blue")
            live = Live(panel, console=self.console, refresh_per_second=30)
            live.start()

            try:
                async for chunk in chunks:
                    if chunk:
                        content_parts.append(chunk)
                        current_content = ''.join(content_parts)

                        if len(current_content) > 500:
                            display_content = current_content[-500:]
                        else:
                            display_content = current_content

                        live.update(Panel(
                            display_content,
                            title="AI 响应",
                            border_style="blue"
                        ))

                live.update(Panel(
                    ''.join(content_parts),
                    title="AI 响应",
                    border_style="green"
                ))

            finally:
                live.stop()
        else:
            async for chunk in chunks:
                if chunk:
                    content_parts.append(chunk)
                    self.console.print(chunk, end="", soft_wrap=True)

        return ''.join(content_parts)

    def print_streaming_status(self, status: str) -> None:
        """打印流式状态"""
        self.console.print(f"[dim]{status}[/dim]")

    def print_error(self, error: str, details: Optional[str] = None) -> None:
        error_panel = Panel(
            f"[bold red]错误:[/bold red] {error}\n{details if details else ''}",
            title="Error",
            border_style="red",
        )
        self.console.print(error_panel)

    def print_tool_result(
        self, tool_name: str, result: Any, success: bool = True
    ) -> None:
        status = "[green]成功[/green]" if success else "[red]失败[/red]"
        result_str = str(result)

        if len(result_str) > 500:
            result_str = result_str[:500] + "..."

        panel = Panel(
            f"**工具:** {tool_name}\n**状态:** {status}\n**结果:**\n{result_str}",
            title="工具执行结果",
            border_style="green" if success else "red",
        )
        self.console.print(panel)

    def print_table(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: str = "数据表格",
    ) -> None:
        if not data:
            self.console.print("[yellow]无数据[/yellow]")
            return

        table = Table(title=title, show_header=True, header_style="bold magenta")

        if columns is None:
            columns = list(data[0].keys()) if data else []

        for col in columns:
            table.add_column(str(col), style="cyan")

        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])

        self.console.print(table)

    def print_info(self, message: str) -> None:
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def print_success(self, message: str) -> None:
        self.console.print(f"[green]✓[/green] {message}")

    def print_warning(self, message: str) -> None:
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def print_divider(self) -> None:
        self.console.print("[dim]" + "─" * 50 + "[/dim]")
