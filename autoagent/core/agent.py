import asyncio
from typing import Any, Optional
from ..config.config_manager import ConfigManager
from ..memory.memory_manager import MemoryManager
from ..skills.skill_manager import SkillManager
from ..tools.tool_executor import ToolExecutor
from ..utils.logger import get_logger
from ..nudges.nudge_engine import NudgeEngine
from .message_handler import MessageHandler
from .response_generator import ResponseGenerator
from .context_builder import ContextBuilder
from .user_manager import UserManager

logger = get_logger("agent")


class AutoAgent:
    def __init__(
        self,
        config_manager: ConfigManager,
        memory_manager: MemoryManager,
        skill_manager: SkillManager,
        tool_executor: ToolExecutor,
        model_router: Optional[Any] = None,
    ):
        self.config_manager = config_manager
        self.memory_manager = memory_manager
        self.skill_manager = skill_manager
        self.tool_executor = tool_executor
        self.model_router = model_router

        self.message_handler = MessageHandler()
        self.response_generator = ResponseGenerator(config_manager, model_router)
        self.context_builder = ContextBuilder(memory_manager, skill_manager)
        self.user_manager = UserManager()
        self.nudge_engine = NudgeEngine(memory_manager=memory_manager, skill_manager=skill_manager)

        self._running = False
        self._conversation_history: list[dict[str, Any]] = []

    def start(self) -> bool:
        if self._running:
            logger.warning("Agent is already running")
            return False

        try:
            self._running = True
            logger.info("AutoAgent started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            self._running = False
            return False

    def stop(self) -> bool:
        if not self._running:
            logger.warning("Agent is not running")
            return False

        try:
            self._running = False
            logger.info("AutoAgent stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop agent: {e}")
            return False

    def process_message(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        if not self._running:
            return {
                "success": False,
                "error": "Agent is not running",
                "message": message
            }

        try:
            processed = self.message_handler.handle_message(message)

            context = context or {}
            context.update(processed.get("context", {}))

            relevant_skills = self.skill_manager.find_relevant_skills(message)
            if relevant_skills:
                context["relevant_skills"] = relevant_skills

            response = self.generate_response(message, context)

            self._add_to_history("user", message)
            self._add_to_history("assistant", response.get("content", ""))

            if self.memory_manager and response.get("success"):
                self.memory_manager.auto_save_context(
                    user_input=message,
                    ai_response=response.get("content", "")
                )

            task_id = self.skill_manager.record_task(
                problem=message,
                solution=response.get("content", ""),
                tool_calls=response.get("tool_calls"),
                success=response.get("success", True)
            )

            created_skill = self.skill_manager.process_task_result(task_id, response)
            if created_skill:
                logger.info(f"Auto-created skill: {created_skill}")

            if self.skill_manager.should_evaluate():
                eval_report = self.skill_manager.evaluate_and_evolve()
                logger.info(f"Evolution evaluation: {eval_report.get('evolved_skills', [])}")

            return {
                "success": True,
                "message": message,
                "response": response,
                "intent": processed.get("intent").intent if processed.get("intent") else None,
                "entities": processed.get("entities", {}),
                "skill_created": created_skill,
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": message
            }

    async def process_message_async(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        if not self._running:
            return {
                "success": False,
                "error": "Agent is not running",
                "message": message
            }

        try:
            processed = self.message_handler.handle_message(message)

            context = context or {}
            context.update(processed.get("context", {}))

            relevant_skills = self.skill_manager.find_relevant_skills(message)
            if relevant_skills:
                context["relevant_skills"] = relevant_skills

            response = await self.generate_response_async(message, context)

            self.user_manager.record_interaction({
                'type': 'message',
                'content': message,
                'response_length': len(response.get('content', ''))
            }, user_message=message)

            if response.get("tool_calls"):
                for tool_call in response.get("tool_calls", []):
                    tool_name = tool_call.get('name', '')
                    if tool_name:
                        self.user_manager.record_tool_usage(tool_name, tool_call)

            self.user_manager.record_task_completion(
                task=message,
                tools_used=[tc.get('name', '') for tc in response.get("tool_calls", [])],
                success=response.get("success", True)
            )

            nudges = await self.nudge_engine.check_and_generate_nudges()
            for nudge in nudges:
                self.nudge_engine.add_nudge(nudge)

            self._add_to_history("user", message)
            self._add_to_history("assistant", response.get("content", ""))

            if self.memory_manager and response.get("success"):
                self.memory_manager.auto_save_context(
                    user_input=message,
                    ai_response=response.get("content", "")
                )

            task_id = self.skill_manager.record_task(
                problem=message,
                solution=response.get("content", ""),
                tool_calls=response.get("tool_calls"),
                success=response.get("success", True)
            )

            created_skill = self.skill_manager.process_task_result(task_id, response)
            if created_skill:
                logger.info(f"Auto-created skill: {created_skill}")

            if self.skill_manager.should_evaluate():
                eval_report = self.skill_manager.evaluate_and_evolve()
                logger.info(f"Evolution evaluation: {eval_report.get('evolved_skills', [])}")

            return {
                "success": True,
                "message": message,
                "response": response,
                "intent": processed.get("intent").intent if processed.get("intent") else None,
                "entities": processed.get("entities", {}),
                "skill_created": created_skill,
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": message
            }

    def generate_response(
        self,
        prompt: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        context = context or {}

        full_context = self.context_builder.build_full_context(
            messages=self._conversation_history,
            query=prompt,
            task=prompt
        )
        context.update(full_context)

        relevant_tools = []
        if context.get("relevant_skills"):
            for skill in context["relevant_skills"]:
                tool_name = skill.get("name", "")
                if tool_name:
                    relevant_tools.append({
                        "name": tool_name,
                        "description": skill.get("description", "")
                    })

        result = self.response_generator.generate(
            prompt=prompt,
            tools=relevant_tools if relevant_tools else None,
            context=context
        )

        return {
            "success": result.success,
            "content": result.content,
            "tool_calls": result.tool_calls,
            "error": result.error
        }

    async def generate_response_async(
        self,
        prompt: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        context = context or {}

        full_context = self.context_builder.build_full_context(
            messages=self._conversation_history,
            query=prompt,
            task=prompt
        )
        context.update(full_context)

        relevant_tools = []
        if context.get("relevant_skills"):
            for skill in context["relevant_skills"]:
                tool_name = skill.get("name", "")
                if tool_name:
                    relevant_tools.append({
                        "name": tool_name,
                        "description": skill.get("description", "")
                    })

        result = await self.response_generator.generate_async(
            prompt=prompt,
            tools=relevant_tools if relevant_tools else None,
            context=context
        )

        return {
            "success": result.success,
            "content": result.content,
            "tool_calls": result.tool_calls,
            "error": result.error
        }

    def _add_to_history(self, role: str, content: str) -> None:
        self._conversation_history.append({
            "role": role,
            "content": content
        })
        if len(self._conversation_history) > 100:
            self._conversation_history = self._conversation_history[-100:]

    def get_history(self) -> list[dict[str, Any]]:
        return self._conversation_history.copy()

    def clear_history(self) -> None:
        self._conversation_history.clear()
        logger.info("Conversation history cleared")
