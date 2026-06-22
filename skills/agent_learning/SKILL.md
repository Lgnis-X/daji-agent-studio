# Agent Learning 技能

当用户学习 AI Agent、Tool Calling、Memory、Skills、Subagent、Agent Team 等概念时，使用本技能。

## 核心解释方式

1. 先用一句话解释概念。
2. 再说明它在代码里对应什么。
3. 再给一个小例子。
4. 最后说明它和上一步相比新增了什么。

## 常用解释

### Agent

Agent = 大模型 + 工具 + 循环。

普通聊天机器人只会回答。
Agent 会判断是否需要工具，并根据工具结果继续完成任务。

### Tool Calling

模型不是真的执行工具。
模型只是提出工具调用请求。
真正执行工具的是 Python 代码。

流程是：

用户输入
→ 模型判断是否需要工具
→ Python 执行工具
→ 工具结果返回模型
→ 模型生成最终回答

### Memory

短期记忆通常是 `messages` 或 `history` 列表。
它会保存 user、assistant、tool 的消息。

### Skills

Skills 是外部说明书，不是工具本身。
它告诉 Agent 遇到某类任务时应该怎么做。

## 回答要求

- 不要堆术语。
- 尽量结合当前项目 daji-agent-studio 来解释。
- 用户是新手时，要先讲“这个东西解决什么问题”。