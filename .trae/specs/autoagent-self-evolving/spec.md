# 自进化个人AI Agent (AutoAgent) 规格文档

## Why

我们需要开发一款能够与Hermes Agent齐平的自进化个人AI Agent。Hermes Agent是目前开源领域最先进的自进化智能体，具备持久记忆、技能自主创建、多平台接入等核心能力。当前项目目录为空，需要从零开始构建一个完整的自进化AI Agent系统。

## What Changes

### 核心架构
- **记忆系统**: 跨会话持久记忆，采用FTS5全文检索 + LLM摘要实现知识召回
- **技能系统**: 智能体从经验中自主创建程序性技能（SKILL.md格式），支持跨会话复用
- **消息网关**: 支持CLI、Telegram、Discord、Slack、WhatsApp多平台统一接入
- **工具系统**: 内置40+工具（网页搜索、文件操作、终端命令、代码执行、视觉分析、图像生成、TTS等）
- **MCP集成**: 连接任意MCP服务器扩展工具能力
- **定时自动化**: 内置cron调度器，支持任意计划任务
- **子代理委托**: 生成隔离子智能体并行处理多工作流

### API配置
- OpenCode Zen API: sk-vywf6uSEFrUsrDur4Va0nvbF2lQGmfZZZkGM5JcoaMoYanc6BDeKQI5mctSy8h1j
- OpenRouter API: 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

### 消息平台支持
- CLI（命令行界面）
- Telegram
- Discord
- Slack
- WhatsApp

### 终端后端支持
- 本地执行
- Docker容器
- SSH远程
- 无服务器（ Daytona、Modal）

### 内置工具集（40+）
1. **网页工具**: search、browse、extract、vision
2. **系统工具**: terminal、file_read、file_write、code_execute
3. **AI工具**: image_generation、tts、vision_analysis
4. **规划工具**: planning、cron、memory_management
5. **委托工具**: subagent_spawn、rpc_call

### 记忆文件
- MEMORY.md: 跨会话持久事实和知识
- USER.md: 用户偏好和建模
- SOUL.md: 智能体人格定义
- SKILLS/: 自主创建的技能库

## Impact

- 受影响规格: 记忆系统、技能系统、消息网关、工具系统、MCP集成、定时任务、子代理系统
- 受影响代码: 全部项目文件

## ADDED Requirements

### Requirement: 持久记忆系统
系统 SHALL 提供跨会话持久记忆能力，通过FTS5全文检索和LLM摘要实现知识召回。

#### Scenario: 查询历史记忆
- **WHEN** 用户询问之前解决过的问题
- **THEN** Agent通过FTS5检索相关记忆，加载对应上下文

#### Scenario: 自动保存重要信息
- **WHEN** Agent判断信息重要时
- **THEN** 自动摘要并存入MEMORY.md

### Requirement: 技能自主创建系统
系统 SHALL 提供从经验中自主创建程序性技能的能力。

#### Scenario: 解决复杂问题后创建技能
- **WHEN** Agent解决了一个复杂问题
- **THEN** 自动创建SKILL.md记录解决方案，供后续复用

### Requirement: 多平台消息网关
系统 SHALL 提供CLI、Telegram、Discord、Slack、WhatsApp多平台统一接入。

#### Scenario: 跨平台对话连续性
- **WHEN** 用户在Telegram开始对话，在Discord继续
- **THEN** 对话上下文完整传递

### Requirement: 40+内置工具
系统 SHALL 提供网页搜索、文件操作、终端命令、代码执行、视觉分析、图像生成、TTS等40+内置工具。

### Requirement: MCP集成
系统 SHALL 支持连接任意MCP服务器扩展工具能力。

### Requirement: 定时自动化
系统 SHALL 提供内置cron调度器，支持任意计划任务执行和结果推送。

### Requirement: 子代理委托
系统 SHALL 支持生成隔离子智能体并行处理多工作流。

### Requirement: 多API支持
系统 SHALL 支持OpenCode Zen和OpenRouter API配置。

## MODIFIED Requirements

无

## REMOVED Requirements

无
