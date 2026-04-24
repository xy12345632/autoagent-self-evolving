"""
CLI Commands - CLI命令处理模块
"""

import click
from typing import Optional, Callable, Any
from functools import wraps


class CLICommands:
    def __init__(self, output, memory_manager=None, skill_manager=None, config_manager=None, agent=None):
        self.output = output
        self.memory_manager = memory_manager
        self.skill_manager = skill_manager
        self.config_manager = config_manager
        self.agent = agent
        self._exit_flag = False

    def is_command(self, text: str) -> bool:
        return text.strip().startswith("/")

    def parse_command(self, text: str) -> tuple[Optional[str], Optional[str]]:
        parts = text.strip()[1:].split(maxsplit=1)
        if not parts:
            return None, None
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None
        return cmd, args

    async def execute_command(self, text: str) -> bool:
        cmd, args = self.parse_command(text)
        if cmd is None:
            return False

        handlers = {
            "help": self._cmd_help,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
            "clear": self._cmd_clear,
            "cls": self._cmd_clear,
            "clearconv": self._cmd_clear_conv,
            "clearconversation": self._cmd_clear_conv,
            "history": self._cmd_history,
            "hist": self._cmd_history,
            "skills": self._cmd_skills,
            "skill": self._cmd_skills,
            "memory": self._cmd_memory,
            "mem": self._cmd_memory,
            "memory_stats": self._cmd_memory_stats,
            "config": self._cmd_config,
            "cfg": self._cmd_config,
            "evolve": self._cmd_evolve,
            "exportskills": self._cmd_export_skills,
            "market": self._cmd_market,
            "publish": self._cmd_publish,
            "remote": self._cmd_remote_market,
            "tools": self._cmd_tools,
            "nudge": self._cmd_nudge,
            "profile": self._cmd_profile,
            "personality": self._cmd_personality,
            "topics": self._cmd_topics,
            "save": self._cmd_save_profile,
            "learn": self._cmd_learn,
        }

        handler = handlers.get(cmd)
        if handler:
            await handler(args)
            return cmd in ("exit", "quit")
        else:
            self.output.print_error(f"未知命令: /{cmd}", "输入 /help 查看可用命令")
            return False

    async def _cmd_help(self, args: Optional[str]) -> None:
        help_text = """
# 可用命令列表

## 基础命令
- `/help` - 显示此帮助信息
- `/exit` - 退出程序
- `/clear` - 清除屏幕
- `/clearconv` - 清除当前对话记录并重置对话

## 对话命令
- `/history` - 显示最近对话历史
- `/history clear` - 清除对话历史

## 技能命令
- `/skills` - 列出所有技能
- `/skills <keyword>` - 搜索技能
- `/evolve` - 显示技能进化统计并触发评估
- `/exportskills` - 导出所有技能为SKILL.md格式
- `/market` - 浏览本地技能市场
- `/market search <关键词>` - 搜索本地市场技能
- `/market install <ID>` - 安装市场技能
- `/publish <技能ID>` - 发布技能到市场
- `/remote search <关键词>` - 搜索远程技能市场
- `/remote featured` - 获取精选技能
- `/remote set_token <令牌>` - 设置远程市场认证令牌

## 内存命令
- `/memory` - 显示内存统计
- `/memory recall <query>` - 搜索记忆
- `/memory recent` - 显示最近记忆
- `/memory_stats` - 显示详细记忆统计

## 工具命令
- `/tools` - 列出所有工具
- `/tools stats` - 显示工具统计
- `/tools search <关键词>` - 搜索工具

## 配置命令
- `/config` - 显示配置信息
- `/config <key>` - 显示特定配置

## 用户档案命令
- `/profile` - 显示用户档案
- `/profile personality` - 显示个性洞察
- `/profile topics` - 显示主题洞察
- `/profile save` - 保存用户档案
- `/profile learn` - 显示学习建议
- `/personality` - 显示个性洞察
- `/topics` - 显示主题洞察
- `/save` - 保存用户档案
- `/learn` - 显示学习建议
        """
        self.output.print_response(help_text, style="markdown")

    async def _cmd_exit(self, args: Optional[str]) -> None:
        self.output.print_info("正在退出...")
        self._exit_flag = True

    async def _cmd_clear(self, args: Optional[str]) -> None:
        self.output.console.clear()
        self.output.print_welcome()

    async def _cmd_clear_conv(self, args: Optional[str]) -> None:
        if self.agent:
            count = len(self.agent.get_history())
            self.agent.clear_history()
            self.output.console.clear()
            self.output.print_welcome()
            self.output.print_info(f"已清除 {count} 条对话记录，当前对话已重置")
        else:
            self.output.print_warning("对话管理器未初始化")

    async def _cmd_history(self, args: Optional[str]) -> None:
        if args == "clear":
            if self.agent:
                self.agent.clear_history()
            self.output.print_info("对话历史已清除")
            return

        if self.agent:
            history = self.agent.get_history()
            if history:
                self.output.print_info(f"共 {len(history)} 条对话记录：")
                for i, msg in enumerate(history[-10:], max(1, len(history)-9)):
                    role = "用户" if msg.get("role") == "user" else "AI"
                    content = msg.get("content", "")[:80]
                    self.output.print_response(f"[{i}] {role}: {content}...")
            else:
                self.output.print_info("暂无对话历史")
        else:
            self.output.print_info("历史记录不可用")

    async def _cmd_skills(self, args: Optional[str]) -> None:
        if self.skill_manager is None:
            self.output.print_warning("技能管理器未初始化")
            return

        if args:
            skills = self.skill_manager.search_skills(args)
            if skills:
                data = [
                    {
                        "名称": s.get("name", ""),
                        "描述": s.get("description", "")[:50],
                        "分类": s.get("category", ""),
                    }
                    for s in skills
                ]
                self.output.print_table(data, title=f"技能搜索: {args}")
            else:
                self.output.print_info(f"未找到包含 '{args}' 的技能")
        else:
            skills = self.skill_manager.list_skills()
            if skills:
                data = [
                    {
                        "名称": s.get("name", ""),
                        "描述": s.get("description", "")[:50],
                        "分类": s.get("category", ""),
                    }
                    for s in skills[:20]
                ]
                self.output.print_table(data, title="可用技能")
            else:
                self.output.print_info("暂无技能")

    async def _cmd_memory(self, args: Optional[str]) -> None:
        if self.memory_manager is None:
            self.output.print_warning("内存管理器未初始化")
            return

        if args:
            if args.startswith("recall"):
                query = args.split("recall", 1)[-1].strip()
                results = self.memory_manager.recall(query)
                if results:
                    data = [
                        {
                            "类型": r.memory_type.value,
                            "内容": r.content[:50],
                            "重要性": r.importance,
                        }
                        for r in results
                    ]
                    self.output.print_table(data, title=f"记忆搜索: {query}")
                else:
                    self.output.print_info(f"未找到相关记忆: {query}")
            elif args == "recent":
                recent = self.memory_manager.get_recent()
                if recent:
                    data = [
                        {
                            "类型": r.memory_type.value,
                            "内容": r.content[:50],
                            "时间": str(r.created_at),
                        }
                        for r in recent[:10]
                    ]
                    self.output.print_table(data, title="最近记忆")
                else:
                    self.output.print_info("暂无记忆")
            else:
                self.output.print_error("未知参数", "使用 /memory recall <query> 或 /memory recent")
        else:
            stats = self.memory_manager.get_stats()
            data = [{"指标": k, "值": str(v)} for k, v in stats.items()]
            self.output.print_table(data, title="内存统计")

    async def _cmd_config(self, args: Optional[str]) -> None:
        if self.config_manager is None:
            self.output.print_warning("配置管理器未初始化")
            return

        if args:
            value = self.config_manager.get(args)
            if value:
                self.output.print_info(f"{args} = {value}")
            else:
                self.output.print_info(f"配置项 '{args}' 不存在")
        else:
            config = self.config_manager.get_all()
            data = [{"配置项": k, "值": str(v)} for k, v in config.items()]
            self.output.print_table(data, title="当前配置")

    async def _cmd_evolve(self, args: Optional[str]) -> None:
        if self.skill_manager is None:
            self.output.print_warning("技能管理器未初始化")
            return

        stats = self.skill_manager.get_evolution_stats()
        data = [
            {"指标": "已记录任务", "值": stats.get("total_tasks_recorded", 0)},
            {"指标": "本会话任务", "值": stats.get("tasks_this_session", 0)},
            {"指标": "本会话创建技能", "值": stats.get("skills_created_this_session", 0)},
            {"指标": "本周期工具调用", "值": stats.get("tool_calls_this_cycle", 0)},
            {"指标": "评估间隔", "值": stats.get("evaluation_interval", 0)},
            {"指标": "距下次评估", "值": stats.get("next_evaluation_at", 0)},
        ]
        self.output.print_table(data, title="技能进化统计")

        if args == "--force" or args == "-f":
            self.output.print_info("正在执行强制评估...")
            report = self.skill_manager.evaluate_and_evolve()
            if report.get("evolved_skills"):
                for evolved in report.get("evolved_skills", []):
                    self.output.print_info(f"  进化: {evolved}")
            else:
                self.output.print_info("无需进化的技能")

    async def _cmd_export_skills(self, args: Optional[str]) -> None:
        if self.skill_manager is None:
            self.output.print_warning("技能管理器未初始化")
            return

        self.output.print_info("正在导出技能为SKILL.md格式...")
        try:
            paths = self.skill_manager.export_all_skills()
            if paths:
                self.output.print_info(f"成功导出 {len(paths)} 个技能")
                for path in paths[:5]:
                    self.output.print_info(f"  - {path}")
                if len(paths) > 5:
                    self.output.print_info(f"  ... 还有 {len(paths) - 5} 个")
            else:
                self.output.print_info("没有技能需要导出")
        except Exception as e:
            self.output.print_error("导出失败", str(e))

    async def _cmd_market(self, args: Optional[str]) -> None:
        if self.skill_manager is None:
            self.output.print_warning("技能管理器未初始化")
            return

        parts = args.split() if args else []
        action = parts[0] if parts else "browse"
        param = parts[1] if len(parts) > 1 else None

        if action == "browse":
            category = param
            stats = self.skill_manager.get_marketplace_stats()
            self.output.print_info(f"本地技能市场 - 共 {stats.get('total_skills', 0)} 个技能")

            listings = self.skill_manager.browse_marketplace(category=category)
            if listings:
                data = [
                    {
                        "名称": l.name,
                        "分类": l.category,
                        "评分": f"{l.rating:.1f}",
                        "下载": l.download_count,
                    }
                    for l in listings[:20]
                ]
                self.output.print_table(data, title="技能市场")
            else:
                self.output.print_info("市场暂无技能")

        elif action == "search":
            if not param:
                self.output.print_info("请提供搜索关键词")
                return
            results = self.skill_manager.search_marketplace(param)
            if results:
                data = [
                    {
                        "名称": l.name,
                        "描述": l.description[:50],
                        "作者": l.author,
                    }
                    for l in results[:10]
                ]
                self.output.print_table(data, title=f"搜索: {param}")
            else:
                self.output.print_info(f"未找到匹配 '{param}' 的技能")

        elif action == "install":
            if not param:
                self.output.print_info("请提供技能ID")
                return
            if self.skill_manager.install_from_marketplace(param):
                self.output.print_success("技能安装成功")
            else:
                self.output.print_error("安装失败", "技能不存在")

        else:
            self.output.print_info("用法:")
            self.output.print_info("  /market browse [分类] - 浏览市场")
            self.output.print_info("  /market search <关键词> - 搜索技能")
            self.output.print_info("  /market install <ID> - 安装技能")

    async def _cmd_publish(self, args: Optional[str]) -> None:
        if self.skill_manager is None:
            self.output.print_warning("技能管理器未初始化")
            return

        parts = args.split() if args else []
        if not parts:
            self.output.print_info("用法: /publish <技能ID> [作者]")
            return

        skill_id = parts[0]
        author = parts[1] if len(parts) > 1 else "local"

        listing_id = self.skill_manager.publish_to_marketplace(skill_id, author)
        if listing_id:
            self.output.print_success(f"技能已发布到市场 (ID: {listing_id})")
        else:
            self.output.print_error("发布失败", "技能不存在")

    async def _cmd_profile(self, args: Optional[str]) -> None:
        """用户档案命令"""
        if self.agent is None or self.agent.user_manager is None:
            self.output.print_warning("用户管理器未初始化")
            return

        profile = self.agent.user_manager.get_user_profile()

        data = [
            {"项目": "用户ID", "值": profile.get('user_id', '')},
            {"项目": "响应风格", "值": profile.get('preferences', {}).get('response_style', '')},
            {"项目": "沟通语气", "值": profile.get('preferences', {}).get('tone', '')},
            {"项目": "语言", "值": profile.get('preferences', {}).get('language', '')},
            {"项目": "学习状态", "值": "已启用" if profile.get('learning_enabled') else "已禁用"},
        ]
        self.output.print_table(data, title="用户档案")

        behaviors = profile.get('behaviors', {})
        if behaviors.get('common_tasks'):
            self.output.print_info("常见任务:")
            for task in behaviors['common_tasks'][:5]:
                self.output.print_info(f"  - {task}")

    async def _cmd_remote_market(self, args: Optional[str]) -> None:
        """远程技能市场命令"""
        if self.skill_manager is None:
            self.output.print_warning("技能管理器未初始化")
            return

        parts = args.split() if args else []
        action = parts[0] if parts else "search"
        param = parts[1] if len(parts) > 1 else None

        hub = self.skill_manager.get_hub_client()

        if action == "search":
            if not param:
                self.output.print_info("请提供搜索关键词")
                return
            self.output.print_info(f"正在搜索远程市场: {param}...")
            results = await hub.search_remote(param)
            if results:
                data = [{"名称": r.get('name', ''), "分类": r.get('category', ''), "作者": r.get('author', '')} for r in results[:10]]
                self.output.print_table(data, title=f"远程市场搜索: {param}")
            else:
                self.output.print_info("未找到匹配的技能")

        elif action == "featured":
            self.output.print_info("正在获取精选技能...")
            results = await hub.get_featured_skills()
            if results:
                data = [{"名称": r.get('name', ''), "描述": r.get('description', '')[:50]} for r in results]
                self.output.print_table(data, title="精选技能")
            else:
                self.output.print_info("暂无精选技能")

        elif action == "set_token":
            if param:
                hub.set_auth_token(param)
                self.output.print_success("远程市场认证令牌已设置")
            else:
                self.output.print_info("请提供认证令牌")

        else:
            self.output.print_info("用法:")
            self.output.print_info("  /remote search <关键词> - 搜索远程技能")
            self.output.print_info("  /remote featured - 获取精选技能")
            self.output.print_info("  /remote set_token <令牌> - 设置认证令牌")

    async def _cmd_memory_stats(self, args: Optional[str]) -> None:
        """记忆统计命令"""
        if self.memory_manager is None:
            self.output.print_warning("记忆管理器未初始化")
            return

        stats = self.memory_manager.get_stats()
        data = [
            {"指标": "总记忆数", "值": stats.get('total_memories', 0)},
            {"指标": "知识", "值": stats.get('knowledge_count', 0)},
            {"指标": "偏好", "值": stats.get('preference_count', 0)},
            {"指标": "上下文", "值": stats.get('context_count', 0)},
            {"指标": "技能", "值": stats.get('skill_count', 0)},
        ]
        self.output.print_table(data, title="记忆统计")

        if hasattr(self.memory_manager, 'summarizer'):
            self.output.print_info("LLM 摘要: 已启用")
        else:
            self.output.print_info("LLM 摘要: 未启用")

    async def _cmd_tools(self, args: Optional[str]) -> None:
        """工具命令"""
        if not hasattr(self, '_tool_registry'):
            from autoagent.tools.tool_registry import ToolRegistry
            self._tool_registry = ToolRegistry()

        parts = args.split() if args else []
        action = parts[0] if parts else "list"
        param = parts[1] if len(parts) > 1 else None

        if action == "list":
            tools = self._tool_registry.list_tools()
            categories = self._tool_registry.get_categories()

            for cat in categories:
                cat_tools = [t for t in tools if t.get('category') == cat]
                if cat_tools:
                    data = [{"工具": t.get('name', ''), "描述": t.get('description', '')[:50]} for t in cat_tools]
                    self.output.print_table(data, title=f"分类: {cat}")

        elif action == "stats":
            tools = self._tool_registry.list_tools()
            self.output.print_info(f"总工具数: {len(tools)}")
            categories = self._tool_registry.get_categories()
            for cat in categories:
                count = len([t for t in tools if t.get('category') == cat])
                self.output.print_info(f"  {cat}: {count}")

        elif action == "search":
            if not param:
                self.output.print_info("请提供搜索关键词")
                return
            results = self._tool_registry.search_tools_by_name(param)
            if results:
                data = [{"工具": t.get('name', ''), "描述": t.get('description', '')[:50]} for t in results]
                self.output.print_table(data, title=f"搜索: {param}")
            else:
                self.output.print_info(f"未找到匹配 '{param}' 的工具")

        else:
            self.output.print_info("用法:")
            self.output.print_info("  /tools - 列出所有工具")
            self.output.print_info("  /tools stats - 显示工具统计")
            self.output.print_info("  /tools search <关键词> - 搜索工具")

    async def _cmd_nudge(self, args: Optional[str]) -> None:
        if self.agent is None or self.agent.nudge_engine is None:
            self.output.print_warning("Nudge 引擎未初始化")
            return

        if args == "list":
            nudges = self.agent.nudge_engine.get_pending_nudges()
            if nudges:
                data = [{"类型": n.type.value, "标题": n.title, "优先级": n.priority.name} for n in nudges]
                self.output.print_table(data, title="待处理 Nudges")
            else:
                self.output.print_info("暂无待处理的 nudges")
        elif args == "stats":
            stats = self.agent.nudge_engine.get_nudge_stats()
            data = [
                {"指标": "总 nudges", "值": stats.get('total_nudges', 0)},
                {"指标": "待显示", "值": stats.get('pending', 0)},
                {"指标": "已关闭", "值": stats.get('dismissed', 0)},
            ]
            self.output.print_table(data, title="Nudge 统计")
        elif args:
            nudge_id = args
            self.agent.nudge_engine.dismiss_nudge(nudge_id)
            self.output.print_success(f"Nudge {nudge_id} 已关闭")
        else:
            self.output.print_info("用法:")
            self.output.print_info("  /nudge list - 显示待处理的 nudges")
            self.output.print_info("  /nudge stats - 显示统计信息")
            self.output.print_info("  /nudge <id> - 关闭指定 nudge")

    async def _cmd_profile(self, args: Optional[str]) -> None:
        """用户档案命令"""
        if self.agent is None or self.agent.user_manager is None:
            self.output.print_warning("用户管理器未初始化")
            return

        if args == "personality":
            await self._cmd_personality(None)
        elif args == "topics":
            await self._cmd_topics(None)
        elif args == "save":
            await self._cmd_save_profile(None)
        elif args == "learn":
            await self._cmd_learn(None)
        else:
            profile = self.agent.user_manager.get_user_profile()

            data = [
                {"项目": "用户ID", "值": profile.get('user_id', '')},
                {"项目": "创建时间", "值": profile.get('created_at', '')},
                {"项目": "更新时间", "值": profile.get('updated_at', '')},
                {"项目": "响应风格", "值": profile.get('preferences', {}).get('response_style', '')},
                {"项目": "沟通语气", "值": profile.get('preferences', {}).get('tone', '')},
                {"项目": "语言", "值": profile.get('preferences', {}).get('language', '')},
                {"项目": "学习状态", "值": "已启用" if profile.get('learning_enabled') else "已禁用"},
            ]
            self.output.print_table(data, title="用户档案")

            behaviors = profile.get('behaviors', {})
            if behaviors.get('common_tasks'):
                self.output.print_info("常见任务:")
                for task in behaviors['common_tasks'][:5]:
                    self.output.print_info(f"  - {task}")

    async def _cmd_personality(self, args: Optional[str]) -> None:
        """个性洞察命令"""
        if self.agent is None or self.agent.user_manager is None:
            self.output.print_warning("用户管理器未初始化")
            return

        insights = self.agent.user_manager.get_personality_insights()

        self.output.print_info(f"已分析 {insights.get('total_analyses', 0)} 次对话")

        if insights.get('top_traits'):
            data = [
                {"特质": t.get('trait', ''), "得分": round(t.get('score', 0), 2)}
                for t in insights.get('top_traits', [])
            ]
            self.output.print_table(data, title="主要个性特质")

        description = insights.get('personality_description', '')
        if description:
            self.output.print_info(f"个性描述: {description}")

    async def _cmd_topics(self, args: Optional[str]) -> None:
        """主题洞察命令"""
        if self.agent is None or self.agent.user_manager is None:
            self.output.print_warning("用户管理器未初始化")
            return

        insights = self.agent.user_manager.get_topic_insights()

        self.output.print_info(f"已检测到 {insights.get('total_topics_detected', 0)} 个主题")

        if insights.get('top_topics'):
            data = [
                {"主题": t.get('topic', ''), "次数": t.get('count', 0)}
                for t in insights.get('top_topics', [])
            ]
            self.output.print_table(data, title="主要兴趣话题")

        current_topics = insights.get('current_session_topics', [])
        if current_topics:
            self.output.print_info(f"当前会话话题: {', '.join(current_topics)}")

    async def _cmd_save_profile(self, args: Optional[str]) -> None:
        """保存用户档案命令"""
        if self.agent is None or self.agent.user_manager is None:
            self.output.print_warning("用户管理器未初始化")
            return

        success = self.agent.user_manager.save()
        if success:
            self.output.print_success("用户档案已保存")
        else:
            self.output.print_error("保存失败", "无法保存用户档案")

    async def _cmd_learn(self, args: Optional[str]) -> None:
        """学习建议命令"""
        if self.agent is None or self.agent.user_manager is None:
            self.output.print_warning("用户管理器未初始化")
            return

        suggestions = self.agent.user_manager.get_learning_suggestions()

        self.output.print_info("学习进度:")
        progress = suggestions.get('progress', {})
        self.output.print_info(f"  个性数据: {progress.get('personality_data', 0)} 条")
        self.output.print_info(f"  主题数据: {progress.get('topic_data', 0)} 条")

        if suggestions.get('suggestions'):
            self.output.print_info("学习建议:")
            for suggestion in suggestions['suggestions']:
                self.output.print_info(f"  - {suggestion}")
        else:
            self.output.print_info("我已经了解你足够多了！")

    def should_exit(self) -> bool:
        return self._exit_flag

    def reset_exit(self) -> None:
        self._exit_flag = False


@click.command()
@click.argument("message", required=False)
def cli_help(message: Optional[str]) -> None:
    if message:
        click.echo(f"帮助: {message}")
    else:
        click.echo("显示帮助信息")


@click.command()
def cli_exit() -> None:
    click.echo("退出程序")


@click.command()
@click.option("--clear", is_flag=True, help="清除历史")
def cli_history(clear: bool) -> None:
    if clear:
        click.echo("历史已清除")
    else:
        click.echo("历史记录...")
