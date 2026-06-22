# Daji Agent Studio

Daji Agent Studio（妲己智能体工作台）是一个基于 FastAPI 和大模型 Tool Calling 的本地智能体项目。

项目采用古风妲己主题界面，支持多轮对话、工具调用、Skills 技能包、长期记忆、Todo 任务规划和网页工作台展示。

## 项目功能

### 1. 多轮对话

支持用户与 Daji Agent 进行连续聊天，并保留当前会话上下文。

### 2. Tool Calling 工具调用

当前支持以下工具：

- `list_files`：查看当前项目目录或子目录
- `read_file`：读取项目中的文本文件
- `run_command`：执行安全命令
- `load_skill`：加载 Skills 技能包
- `remember_memory`：写入长期记忆
- `list_memory`：查看长期记忆
- `update_todos`：更新 Todo 任务计划
- `list_todos`：查看 Todo 任务计划

### 3. Skills 技能包

项目内置 3 个技能包：

- `python_debug`：Python 报错排查技能
- `project_reader`：项目阅读技能
- `agent_learning`：Agent 学习解释技能

技能包位于：

```text
skills/
├── python_debug/
├── project_reader/
└── agent_learning/