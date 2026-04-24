"""
CLI Interface - CLI主界面模块
"""

import asyncio
import sys
from typing import Optional, Callable, Any, AsyncIterator
from .cli_input import CLIInput
from .cli_output import CLIOutput
from .cli_commands import CLICommands


class CLIInterface:
    def __init__(
        self,
        memory_manager=None,
        skill_manager=None,
        config_manager=None,
        agent=None,
        message_handler: Optional[Callable] = None,
        stream_handler: Optional[Callable] = None,
    ):
        self.input_handler = CLIInput()
        self.output_handler = CLIOutput()
        self.agent = agent
        self.commands = CLICommands(
            output=self.output_handler,
            memory_manager=memory_manager,
            skill_manager=skill_manager,
            config_manager=config_manager,
            agent=agent,
        )
        self.message_handler = message_handler
        self.stream_handler = stream_handler
        self._running = False
        self._streaming_enabled = True

    async def start(self) -> None:
        self._running = True
        self.output_handler.print_welcome()

        while self._running:
            try:
                user_input = self.input_handler.prompt_input(">>> ")
                if not user_input.strip():
                    continue

                if self.commands.is_command(user_input):
                    should_exit = await self.commands.execute_command(user_input)
                    if should_exit:
                        break
                else:
                    await self._process_message(user_input)

            except KeyboardInterrupt:
                self.output_handler.print_info("\n使用 /exit 退出")
                continue
            except EOFError:
                break
            except Exception as e:
                self.output_handler.print_error(str(e))

        self.output_handler.print_info("再见!")

    async def _process_message(self, message: str) -> None:
        if self.stream_handler and self._streaming_enabled:
            try:
                chunks = self.stream_handler(message)
                if asyncio.iscoroutine(chunks):
                    chunks = await chunks

                if asyncio.isasyncgen(chunks):
                    full_content = await self.output_handler.print_stream(chunks)
                elif isinstance(chunks, AsyncIterator):
                    full_content = await self.output_handler.print_stream(chunks)
                else:
                    self.output_handler.print_response(str(chunks))
                    full_content = str(chunks)

            except Exception as e:
                self.output_handler.print_error("流式输出错误", str(e))
                if self.message_handler:
                    response = await self.message_handler(message) if asyncio.iscoroutinefunction(self.message_handler) else self.message_handler(message)
                    self._display_response(response)

        elif self.message_handler:
            self._display_response(await self.message_handler(message) if asyncio.iscoroutinefunction(self.message_handler) else self.message_handler(message))
        else:
            self.output_handler.print_response(f"[模拟回复]: {message}")

    def _display_response(self, response: Any) -> None:
        if isinstance(response, dict):
            inner = response.get("response", {})
            if isinstance(inner, dict):
                content = inner.get("content", "")
                error = inner.get("error")
                if content:
                    self.output_handler.print_response(content)
                elif error:
                    self.output_handler.print_error("错误", error)
                else:
                    self.output_handler.print_response(str(response))
            else:
                self.output_handler.print_response(str(inner))
        else:
            self.output_handler.print_response(str(response))

    async def run_single_command(self, command: str) -> None:
        if self.commands.is_command(command):
            await self.commands.execute_command(command)
        else:
            await self._process_message(command)

    def stop(self) -> None:
        self._running = False

    async def multiline_mode(self) -> str:
        self.output_handler.print_info("多行输入模式 - 输入空行或 Ctrl+D 结束")
        content = self.input_handler.multiline_input()
        return content

    async def process_tool_result(self, tool_name: str, result: Any, success: bool = True) -> None:
        self.output_handler.print_tool_result(tool_name, result, success)

    async def display_table(self, data: list, columns: Optional[list] = None, title: str = "数据") -> None:
        self.output_handler.print_table(data, columns, title)
