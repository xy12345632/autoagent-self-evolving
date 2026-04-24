# AutoAgent API 参考

## 核心类

### AutoAgent

主Agent类，统一管理所有组件。

```python
from autoagent.core.agent import AutoAgent

agent = AutoAgent(
    config_manager=config_manager,
    memory_manager=memory_manager,
    skill_manager=skill_manager,
    tool_executor=tool_executor,
    model_router=router
)

agent.start()
```

#### 方法

##### start()

启动Agent。

```python
agent.start() -> bool
```

##### stop()

停止Agent。

```python
agent.stop() -> bool
```

##### process_message(message, context=None)

同步处理消息。

```python
agent.process_message(
    message: str,
    context: dict = None
) -> dict
```

**返回**:

```python
{
    "success": True,
    "message": "原始消息",
    "response": {
        "content": "AI响应内容",
        "tool_calls": [...],
        "success": True
    },
    "intent": "general_query",
    "entities": {},
    "skill_created": None
}
```

##### process_message_async(message, context=None)

异步处理消息。

```python
await agent.process_message_async(
    message: str,
    context: dict = None
) -> dict
```

##### generate_response(prompt, context=None)

生成响应（同步）。

```python
agent.generate_response(
    prompt: str,
    context: dict = None
) -> dict
```

##### generate_response_async(prompt, context=None)

生成响应（异步）。

```python
await agent.generate_response_async(
    prompt: str,
    context: dict = None
) -> dict
```

##### get_history()

获取对话历史。

```python
agent.get_history() -> list[dict]
```

##### clear_history()

清除对话历史。

```python
agent.clear_history() -> None
```

---

## 配置模块

### ConfigManager

配置管理器。

```python
from autoagent.config.config_manager import ConfigManager

config = ConfigManager()

# 获取API密钥
api_key = config.get_api_key("opencode_zen")

# 获取配置项
model_config = config.get_config("model_providers", "opencode_zen")

# 获取整个配置
full_config = config.get_all()
```

#### 方法

##### get_api_key(provider: str) -> str

获取API密钥。

##### get_config(*keys) -> Any

按层级获取配置。

##### get_all() -> dict

获取全部配置。

---

## 记忆模块

### MemoryManager

记忆管理器。

```python
from autoagent.memory.memory_manager import MemoryManager

memory = MemoryManager()
```

#### 方法

##### add_knowledge(content, importance=5, metadata=None) -> int

添加知识记忆。

##### add_preference(content, importance=7, metadata=None) -> int

添加偏好记忆。

##### add_context(content, importance=5, metadata=None) -> int

添加上下文记忆。

##### add_skill(content, importance=6, metadata=None) -> int

添加技能记忆。

##### recall(query, limit=10) -> list[MemoryEntry]

搜索记忆。

##### get_recent(limit=20) -> list[MemoryEntry]

获取最近记忆。

##### get_by_type(memory_type, limit=50) -> list[MemoryEntry]

按类型获取记忆。

##### is_important(content) -> bool

判断内容是否重要。

##### auto_save_context(user_input=None, ai_response=None, metadata=None)

自动保存重要上下文。

##### summarize_entry(memory_id, max_length=200) -> str

摘要单条记忆。

##### summarize_all(theme=None) -> str

摘要所有记忆。

##### compress_memories(max_count=50) -> list[MemoryEntry]

压缩记忆。

##### get_stats() -> dict

获取统计信息。

##### sync_to_file(file_type="memory") -> bool

同步到Markdown文件。

##### load_from_file(file_type="memory") -> list[MemoryEntry]

从Markdown文件加载。

---

## 技能模块

### SkillManager

技能管理器。

```python
from autoagent.skills.skill_manager import SkillManager

skills = SkillManager()
```

#### 方法

##### load_skill(skill_id: str) -> Optional[dict]

加载技能。

##### find_relevant_skills(task: str) -> list[dict]

查找相关技能。

##### create_skill(skill_data: dict) -> str

创建技能。

##### get_skill(skill_id: str) -> Optional[dict]

获取技能详情。

##### list_skills(category=None) -> list[dict]

列出技能。

##### search_skills(query: str) -> list[dict]

搜索技能。

##### update_skill(skill_id: str, skill_data: dict) -> bool

更新技能。

##### delete_skill(skill_id: str) -> bool

删除技能。

##### reload_skills()

重新加载技能。

##### record_task(problem, solution, tool_calls=None, success=True) -> str

记录任务。

##### process_task_result(task_id, result) -> Optional[str]

处理任务结果。

##### evaluate_and_evolve() -> dict

评估和进化技能。

##### should_evaluate() -> bool

检查是否需要评估。

##### export_all_skills() -> list[str]

导出所有技能。

##### publish_to_marketplace(skill_id, author="local", version="1.0.0") -> Optional[str]

发布到市场。

##### browse_marketplace(category=None, sort_by="rating", limit=20) -> list

浏览市场。

##### install_from_marketplace(listing_id: str) -> bool

从市场安装。

---

## 工具模块

### ToolRegistry

工具注册表（单例）。

```python
from autoagent.tools.tool_registry import ToolRegistry

registry = ToolRegistry.get_instance()
```

#### 方法

##### register_tool(tool_name, tool_func, schema=None)

注册工具。

##### unregister_tool(tool_name) -> bool

注销工具。

##### get_tool(tool_name) -> Optional[Callable]

获取工具函数。

##### has_tool(tool_name) -> bool

检查工具是否存在。

##### list_tools(category=None) -> list[str]

列出工具。

##### get_categories() -> list[str]

获取工具类别。

##### get_tools_by_category(category) -> list[str]

按类别获取工具。

##### search_tools(query) -> list[str]

搜索工具。

##### get_tool_schema(tool_name) -> Optional[dict]

获取工具Schema。

##### update_tool_schema(tool_name, schema) -> bool

更新工具Schema。

##### clear()

清空注册表。

##### get_registry_info() -> dict

获取注册表信息。

### ToolExecutor

工具执行器。

```python
from autoagent.tools.tool_executor import ToolExecutor

executor = ToolExecutor(registry)
```

#### 方法

##### execute(tool_name, parameters) -> Any

同步执行工具。

##### execute_async(tool_name, parameters) -> Any

异步执行工具。

##### execute_batch(tools) -> list

批量执行工具。

---

## API模块

### ModelRouter

模型路由器。

```python
from autoagent.api.router import ModelRouter

router = ModelRouter(
    providers={"opencode_zen": provider, "openrouter": provider2},
    default_preference="opencode_zen"
)
```

#### 方法

##### route(prompt, context=None) -> dict

路由到合适模型。

##### add_provider(name, provider)

添加提供商。

##### remove_provider(name)

移除提供商。

##### set_preference(name)

设置默认偏好。

### OpenCodeZenProvider

OpenCode Zen API提供商。

```python
from autoagent.api.opencode_zen import OpenCodeZenProvider

provider = OpenCodeZenProvider(
    api_key="your-api-key",
    base_url="https://opencode.ai/zen/v1"
)
```

### OpenRouterProvider

OpenRouter API提供商。

```python
from autoagent.api.openrouter import OpenRouterProvider

provider = OpenRouterProvider(
    api_key="your-api-key",
    base_url="https://openrouter.ai/api/v1"
)
```

---

## 网关模块

### CLIInterface

命令行界面。

```python
from autoagent.gateway.cli.cli_interface import CLIInterface

cli = CLIInterface(
    memory_manager=memory,
    skill_manager=skills,
    config_manager=config,
    agent=agent,
    message_handler=agent.process_message_async
)

await cli.start()
```

### TelegramBot

Telegram Bot。

```python
from autoagent.gateway.telegram.telegram_bot import TelegramBot

bot = TelegramBot(token="bot-token", agent_core=agent)
await bot.start()
await bot.stop()
```

### DiscordBot

Discord Bot。

```python
from autoagent.gateway.discord.discord_bot import DiscordBot

bot = DiscordBot(token="bot-token", agent_core=agent)
await bot.start()
```

### SlackBot

Slack Bot。

```python
from autoagent.gateway.slack.slack_bot import SlackBot

bot = SlackBot(token="bot-token", agent_core=agent)
await bot.start()
```

---

## 调度模块

### Scheduler

任务调度器。

```python
from autoagent.scheduler.scheduler import Scheduler

scheduler = Scheduler()
scheduler.start()
```

#### 方法

##### add_job(func, trigger, args=None, id=None, name=None, **kwargs)

添加任务。

##### remove_job(job_id) -> bool

移除任务。

##### list_jobs() -> list[dict]

列出所有任务。

##### pause_job(job_id) -> bool

暂停任务。

##### resume_job(job_id) -> bool

恢复任务。

##### run_job(job_id) -> bool

手动触发任务。

##### get_task_result(job_id) -> Optional[dict]

获取任务结果。

##### reschedule_job(job_id, trigger)

重新调度任务。

##### shutdown(wait=True)

关闭调度器。

### CronTrigger

Cron触发器。

```python
from autoagent.scheduler.cron_trigger import CronTrigger

trigger = CronTrigger(hour=9, minute=0, day_of_week="mon-fri")
```

---

## MCP模块

### MCPClient

MCP协议客户端。

```python
from autoagent.mcp.mcp_client import MCPClient

client = MCPClient()
```

#### 方法

##### connect(server_url: str) -> bool

连接MCP服务器。

##### disconnect()

断开连接。

##### list_tools() -> list[dict]

列出可用工具。

##### call_tool(tool_name, params) -> Any

调用工具。

##### get_resources() -> list[dict]

获取资源列表。

##### read_resource(resource_uri) -> Any

读取资源。

##### is_connected -> bool

连接状态。

---

## 子代理模块

### SubagentManager

子代理管理器。

```python
from autoagent.subagent.subagent_manager import SubagentManager

manager = SubagentManager()
```

#### 方法

##### create_subagent(task: str, config=None) -> Subagent

创建子代理。

##### list_subagents() -> list[dict]

列出子代理。

##### get_subagent(subagent_id) -> Optional[Subagent]

获取子代理。

##### terminate_subagent(subagent_id) -> bool

终止子代理。

##### terminate_all() -> int

终止所有子代理。

##### get_active_count() -> int

获取活跃数量。

##### cleanup_terminated() -> int

清理已终止的子代理。

### Subagent

子代理类。

```python
subagent = Subagent(
    subagent_id="uuid",
    name="my_subagent",
    config={}
)
```

---

## 用户模块

### UserModel

用户数据模型。

```python
from autoagent.user.user_model import UserModel, UserPreference, UserBehavior

user = UserModel(
    user_id="user_123",
    created_at="2024-01-01T00:00:00Z",
    updated_at="2024-01-15T12:00:00Z",
    preferences=UserPreference(
        response_style="detailed",
        communication_tone="friendly",
        preferred_language="zh"
    ),
    behaviors=UserBehavior(
        common_tasks=["编程", "搜索"],
        tool_usage_history={"web_search": 50}
    )
)
```

---

## 数据类型

### MemoryEntry

```python
@dataclass
class MemoryEntry:
    id: int
    content: str
    memory_type: MemoryType
    importance: int
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    metadata: dict = None
```

### MemoryType

```python
class MemoryType(Enum):
    KNOWLEDGE = "knowledge"
    PREFERENCE = "preference"
    CONTEXT = "context"
    SKILL = "skill"
```

### Nudge

```python
@dataclass
class Nudge:
    id: str
    type: NudgeType
    title: str
    content: str
    priority: NudgePriority
    created_at: str
    trigger_condition: dict = None
    metadata: dict = None
    shown: bool = False
    dismissed: bool = False
```

### NudgeType

```python
class NudgeType(Enum):
    SKILL_SUGGESTION = "skill_suggestion"
    MEMORY_BASED = "memory_based"
    TIME_BASED = "time_based"
    BEHAVIOR_BASED = "behavior_based"
    EVENT_BASED = "event_based"
```

### NudgePriority

```python
class NudgePriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```
