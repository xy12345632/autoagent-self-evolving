# AutoAgent - 自进化个人AI Agent

AutoAgent 是一个具有自进化能力的个人AI助手系统，能够通过与用户的交互持续学习和改进，提供持久记忆、多平台支持、丰富的工具生态和智能技能管理系统。

## 目录

- [特性](特性.md)
- [架构](架构.md)
- [快速开始](快速开始.md)
- [配置指南](配置指南.md)
- [工具系统](工具系统.md)
- [技能系统](技能系统.md)
- [记忆系统](记忆系统.md)
- [API参考](API参考.md)
- [开发指南](开发指南.md)

## 特性

### 核心能力

- **持久记忆** - 跨会话记忆用户偏好、知识和交互历史
- **自进化技能** - 自动从交互中学习并创建新技能，越用越聪明
- **40+工具生态** - 网页搜索、代码执行、文件操作、天气查询等
- **多平台支持** - CLI、Telegram、Discord、Slack、WhatsApp
- **智能上下文** - 构建完整对话上下文，理解用户意图
- **流式输出** - 实时流式响应体验

### 技术特性

- **异步架构** - 全异步设计，支持高并发
- **模型路由** - 支持 OpenCode Zen 和 OpenRouter 多模型切换
- **插件化工具** - 动态注册和加载工具
- **技能市场** - 本地技能存储与共享机制
- **定时任务** - Cron风格的定时任务调度
- **用户建模** - 学习用户行为和偏好

## 架构概览

```
autoagent/
├── api/                    # API提供者与路由
│   ├── opencode_zen.py    # OpenCode Zen提供商
│   ├── openrouter.py      # OpenRouter提供商
│   └── router.py          # 模型路由器
├── config/                # 配置管理
│   ├── config_manager.py  # 配置管理器
│   ├── secrets_manager.py  # 密钥管理
│   └── config.yaml        # 配置文件
├── core/                  # 核心Agent逻辑
│   ├── agent.py          # Agent主类
│   ├── context_builder.py # 上下文构建器
│   ├── message_handler.py # 消息处理器
│   ├── response_generator.py # 响应生成器
│   └── user_manager.py   # 用户管理器
├── gateway/              # 多平台网关
│   ├── cli/             # 命令行界面
│   ├── telegram/        # Telegram Bot
│   ├── discord/         # Discord Bot
│   ├── slack/           # Slack Bot
│   └── whatsapp/       # WhatsApp Bot
├── memory/              # 记忆系统
│   ├── memory_manager.py # 记忆管理器
│   ├── memory_store.py   # 记忆存储
│   ├── file_memory.py    # 文件记忆
│   ├── summarizer.py     # 记忆摘要
│   └── schemas.py        # 数据模式
├── skills/              # 技能系统
│   ├── skill_manager.py  # 技能管理器
│   ├── skill_creator.py  # 技能创建器
│   ├── skill_evolution.py # 技能进化
│   ├── skill_loader.py   # 技能加载器
│   ├── skill_store.py    # 技能存储
│   ├── skill_parser.py   # 技能解析器
│   └── skill_marketplace.py # 技能市场
├── tools/               # 工具系统
│   ├── base_tool.py      # 工具基类
│   ├── tool_registry.py  # 工具注册表
│   ├── tool_executor.py  # 工具执行器
│   ├── tool_learner.py   # 工具学习器
│   ├── tools_loader.py   # 工具加载器
│   ├── web_tools/       # 网页工具
│   ├── system_tools/    # 系统工具
│   ├── ai_tools/        # AI工具
│   ├── planning_tools/  # 规划工具
│   └── delegation_tools/ # 委托工具
├── scheduler/           # 调度系统
│   ├── scheduler.py      # 调度器
│   ├── cron_trigger.py   # Cron触发器
│   ├── task_executor.py  # 任务执行器
│   └── notification_manager.py # 通知管理
├── nudges/             # 提示引擎
│   ├── nudge_engine.py   # 提示引擎
│   ├── nudge_types.py    # 提示类型
│   └── trigger_manager.py # 触发管理器
├── subagent/           # 子代理系统
│   ├── subagent.py       # 子代理
│   └── subagent_manager.py # 子代理管理
├── mcp/                # MCP集成
│   ├── mcp_client.py     # MCP客户端
│   ├── mcp_server_manager.py # 服务器管理
│   ├── resource_manager.py # 资源管理
│   └── tool_filter.py    # 工具过滤
├── user/               # 用户系统
│   ├── user_model.py     # 用户模型
│   ├── preference_learner.py # 偏好学习
│   ├── behavior_tracker.py # 行为追踪
│   ├── personality.py    # 个性化
│   └── persistence.py   # 持久化
├── utils/              # 工具函数
│   ├── logger.py         # 日志
│   ├── paths.py          # 路径管理
│   ├── decorators.py     # 装饰器
│   └── error_handler.py  # 错误处理
└── main.py             # 主入口
```

## 快速开始

### 环境要求

- Python 3.10+
- pip 或 pipenv

### 安装

```bash
# 克隆项目
cd 自进化个人AI Agent完整项目包

# 安装依赖
pip install -r requirements.txt

# 或使用 setuptools 安装为包
pip install -e .
```

### 配置API密钥

编辑 `autoagent/config/config.yaml`:

```yaml
opencode_zen_api_key: your_opencode_zen_key
openrouter_api_key: your_openrouter_key

model_providers:
  opencode_zen:
    endpoint: https://opencode.ai/zen/v1
    default_model: minimax-m2.5-free
  openrouter:
    endpoint: https://openrouter.ai/api/v1
    default_model: openai/gpt-4o-mini
```

或设置环境变量:

```bash
export OPENCOD EZEN_API_KEY=your_key
export OPENROUTER_API_KEY=your_key
```

### 运行

```bash
# 使用安装的 CLI 命令
autoagent

# 或直接运行
python -m autoagent.main

# 或直接运行主文件
python autoagent/main.py
```

## 配置指南

### 主配置 (config.yaml)

```yaml
# API密钥
opencode_zen_api_key: your_key
openrouter_api_key: your_key

# 模型提供商
model_providers:
  opencode_zen:
    endpoint: https://opencode.ai/zen/v1
    default_model: minimax-m2.5-free
  openrouter:
    endpoint: https://openrouter.ai/api/v1
    default_model: openai/gpt-4o-mini

# 记忆配置
memory:
  type: sqlite_fts
  db_path: ./data/memory.db

# 技能配置
skills:
  path: ./skills
  auto_create: true

# 网关配置
gateway:
  cli:
    enabled: true
  telegram:
    enabled: false
    bot_token: ""
  discord:
    enabled: false
    bot_token: ""
  slack:
    enabled: false
    bot_token: ""
  whatsapp:
    enabled: false

# 工具配置
tools:
  web_search:
    enabled: true
    provider: duckduckgo
  terminal:
    enabled: true
    allowed_commands:
      - ls
      - cd
      - pwd
      - git
      - npm
      - python
      - node
  code_execute:
    enabled: true
    sandbox: docker
```

### 灵魂配置 (data/SOUL.md)

定义AI的核心性格、价值观和行为准则:

```markdown
# 灵魂配置

定义AI的核心性格、价值观、行为准则和沟通风格。

## 性格特征
...
```

### 用户配置 (data/USER.md)

存储用户信息和偏好设置。

### 记忆文件 (data/MEMORY.md)

持久化存储重要记忆和知识。

## 使用指南

### CLI命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/clear` | 清除对话历史 |
| `/memory` | 查看记忆状态 |
| `/skills` | 查看已学技能 |
| `/exit` | 退出程序 |
| `/skill <name>` | 使用指定技能 |
| `/skill create` | 创建新技能 |
| `/skill list` | 列出所有技能 |
| `/skill info <name>` | 查看技能详情 |
| `/marketplace` | 浏览技能市场 |
| `/config` | 查看/修改配置 |
| `/history` | 查看对话历史 |
| `/export skills` | 导出所有技能 |
| `/stats` | 查看使用统计 |

### 基本交互

```python
# 程序启动后，直接输入问题或指令
>>> 你好，今天天气怎么样？
>>> 帮我搜索Python异步编程的最佳实践
>>> 用中文解释什么是装饰器
```

### 工具调用

Agent可以自动调用各种工具完成任务:

```python
>>> 帮我执行 git status
>>> 搜索最新的AI新闻
>>> 计算 2^10 的值
>>> 帮我写一个Hello World程序
```

## 工具系统

### 内置工具类别

#### 网页工具 (web_tools)

| 工具 | 功能 |
|------|------|
| `web_search` | 网页搜索 |
| `browse` | 浏览网页 |
| `extract` | 提取网页内容 |
| `vision` | 视觉分析 |

#### 系统工具 (system_tools)

| 工具 | 功能 |
|------|------|
| `terminal` | 执行终端命令 |
| `code_execute` | 执行代码 |
| `file_ops` | 文件操作 |

#### AI工具 (ai_tools)

| 工具 | 功能 |
|------|------|
| `image_gen` | 图像生成 |
| `tts` | 文本转语音 |
| `transcription` | 语音转文字 |
| `vision_analysis` | 图像分析 |

#### 规划工具 (planning_tools)

| 工具 | 功能 |
|------|------|
| `planner` | 任务规划 |
| `cron_job` | 定时任务 |
| `memory_mgmt` | 记忆管理 |

#### 委托工具 (delegation_tools)

| 工具 | 功能 |
|------|------|
| `subagent` | 创建子代理 |
| `rpc_call` | RPC调用 |

### 工具注册

```python
from autoagent.tools.tool_registry import ToolRegistry

registry = ToolRegistry.get_instance()
registry.register_tool(
    tool_name="my_tool",
    tool_func=my_function,
    schema={
        "name": "my_tool",
        "description": "工具描述",
        "category": "custom",
        "parameters": {...}
    }
)
```

## 技能系统

### 技能结构

```python
{
    "id": "skill_xxx",
    "name": "技能名称",
    "description": "技能描述",
    "trigger": ["触发词1", "触发词2"],
    "action": {
        "type": "function",
        "function": "函数名"
    },
    "category": "category",
    "usage_count": 0,
    "success_rate": 1.0
}
```

### 技能自动进化

Agent会自动:

1. 记录任务解决过程
2. 识别可复用的模式
3. 创建新技能
4. 评估和优化现有技能

### 技能市场

```python
# 发布技能到本地市场
skill_manager.publish_to_marketplace(skill_id, author="user", version="1.0.0")

# 浏览市场
skills = skill_manager.browse_marketplace(category="coding", sort_by="rating")

# 安装技能
skill_manager.install_from_marketplace(listing_id)
```

### 技能导入/导出

```bash
# 导出所有技能
/exporter skills

# 导出指定技能
/exporter skill <skill_name>
```

## 记忆系统

### 记忆类型

| 类型 | 说明 | 重要性范围 |
|------|------|-----------|
| `KNOWLEDGE` | 知识记忆 | 1-10 |
| `PREFERENCE` | 偏好记忆 | 1-10 |
| `CONTEXT` | 上下文记忆 | 1-10 |
| `SKILL` | 技能记忆 | 1-10 |

### 记忆管理

```python
# 添加知识
memory_manager.add_knowledge("Python是一门解释型语言", importance=7)

# 添加偏好
memory_manager.add_preference("用户喜欢简洁的回答", importance=8)

# 搜索记忆
results = memory_manager.recall("Python", limit=10)

# 获取统计
stats = memory_manager.get_stats()
```

### 记忆摘要

```python
# 摘要单条记忆
summary = await memory_manager.summarize_entry(memory_id)

# 摘要所有记忆
all_summary = await memory_manager.summarize_all(theme="技术")
```

## 多平台网关

### Telegram Bot

```python
from autoagent.gateway.telegram.telegram_bot import TelegramBot

bot = TelegramBot(token="your_bot_token", agent_core=agent)
await bot.start()
```

启动后使用 `/start` 开始交互。

### Discord Bot

```python
from autoagent.gateway.discord.discord_bot import DiscordBot

bot = DiscordBot(token="your_bot_token", agent_core=agent)
await bot.start()
```

### Slack Bot

```python
from autoagent.gateway.slack.slack_bot import SlackBot

bot = SlackBot(token="your_bot_token", agent_core=agent)
await bot.start()
```

### WhatsApp Bot

```python
from autoagent.gateway.whatsapp.whatsapp_client import WhatsAppBot

bot = WhatsAppBot(session_name="my_session", agent_core=agent)
await bot.start()
```

## MCP集成

Model Context Protocol (MCP) 客户端允许连接外部MCP服务器:

```python
from autoagent.mcp.mcp_client import MCPClient

client = MCPClient()

# 连接服务器
await client.connect("http://localhost:8080")

# 列出可用工具
tools = await client.list_tools()

# 调用工具
result = await client.call_tool("tool_name", {"param": "value"})

# 获取资源
resources = await client.get_resources()
```

## 调度系统

### 添加定时任务

```python
from autoagent.scheduler.scheduler import Scheduler
from autoagent.scheduler.cron_trigger import CronTrigger

scheduler = Scheduler()
scheduler.start()

# Cron风格触发
trigger = CronTrigger(hour=9, minute=0)  # 每天9点
scheduler.add_job(
    func=my_task,
    trigger=trigger,
    id="morning_task",
    name="早间任务"
)
```

### 任务管理

```python
# 列出所有任务
jobs = scheduler.list_jobs()

# 暂停任务
scheduler.pause_job("job_id")

# 恢复任务
scheduler.resume_job("job_id")

# 删除任务
scheduler.remove_job("job_id")

# 手动触发
scheduler.run_job("job_id")
```

## 子代理系统

创建和管理子代理处理复杂任务:

```python
from autoagent.subagent.subagent_manager import SubagentManager

manager = SubagentManager()

# 创建子代理
subagent = await manager.create_subagent(
    task="分析这个代码库",
    config={"name": "code_analyzer"}
)

# 列出子代理
agents = await manager.list_subagents()

# 终止子代理
await manager.terminate_subagent(subagent_id)
```

## 提示引擎

提示引擎(Nudge Engine)主动提供智能建议:

### 提示类型

| 类型 | 说明 |
|------|------|
| `SKILL_SUGGESTION` | 技能建议 |
| `MEMORY_BASED` | 基于记忆的建议 |
| `TIME_BASED` | 时间触发建议 |
| `BEHAVIOR_BASED` | 行为模式建议 |
| `EVENT_BASED` | 事件触发建议 |

### 提示优先级

- `HIGH` - 高优先级
- `MEDIUM` - 中优先级
- `LOW` - 低优先级

## 开发指南

### 添加新工具

1. 创建工具类继承 `BaseTool`:

```python
from autoagent.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "我的工具"
    category = "custom"

    async def execute(self, **kwargs):
        # 工具逻辑
        return result
```

2. 在 `tools_loader.py` 中注册

### 添加新网关

1. 在 `gateway/` 下创建新平台目录
2. 实现消息处理器和会话管理
3. 在 `main.py` 中初始化

### 添加新API提供商

1. 在 `api/` 创建提供商类
2. 实现标准接口方法
3. 在路由器中注册

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试
pytest tests/test_memory.py

# 运行带覆盖率
pytest --cov=autoagent tests/
```

### 测试结构

```
tests/
├── conftest.py         # pytest配置和fixture
├── test_api.py         # API测试
├── test_config.py      # 配置测试
├── test_memory.py      # 记忆系统测试
├── test_skills.py      # 技能系统测试
└── test_tools.py       # 工具系统测试
```

### 编写测试

```python
import pytest
from autoagent.memory.memory_manager import MemoryManager

def test_memory_add(memory_entry):
    manager = MemoryManager()
    memory_id = manager.add_knowledge("测试知识", importance=5)
    assert memory_id > 0
```

## 项目结构

```
.
├── autoagent/              # 主包
│   ├── api/               # API层
│   ├── config/             # 配置
│   ├── core/               # 核心
│   ├── gateway/            # 网关
│   ├── memory/             # 记忆
│   ├── skills/             # 技能
│   ├── tools/              # 工具
│   ├── scheduler/          # 调度
│   ├── nudges/             # 提示
│   ├── subagent/           # 子代理
│   ├── mcp/                # MCP
│   ├── user/               # 用户
│   └── utils/              # 工具
├── data/                   # 数据目录
│   ├── MEMORY.md           # 记忆文件
│   ├── SOUL.md             # 灵魂配置
│   ├── USER.md             # 用户配置
│   └── memory.db           # SQLite数据库
├── tests/                  # 测试
├── pyproject.toml          # 项目配置
└── requirements.txt        # 依赖
```

## 依赖

核心依赖:

- `pyyaml>=6.0` - YAML配置解析
- `aiohttp>=3.9.0` - 异步HTTP
- `requests>=2.31.0` - HTTP请求
- `openai>=1.12.0` - OpenAI API
- `rich>=13.7.0` - 富文本输出
- `click>=8.1.0` - CLI框架

平台集成:

- `telethon>=1.35.0` - Telegram
- `discord.py>=2.3.0` - Discord
- `slack-sdk>=3.21.0` - Slack

其他:

- `apscheduler>=3.10.0` - 任务调度
- `Pillow>=10.0.0` - 图像处理
- `pytest>=7.4.0` - 测试

## 许可证

MIT License

## 联系方式

项目地址: https://github.com/your-repo/autoagent
