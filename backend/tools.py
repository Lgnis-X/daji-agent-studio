import subprocess
from pathlib import Path
from backend.skills import load_skill
from backend.memory import add_memory, list_memories_as_text
from backend.todo import update_todos, list_todos_as_text

WORKSPACE_ROOT = Path.cwd().resolve()


def is_safe_path(path: str):
    """
    检查路径是否安全。
    只允许访问当前项目目录内部的文件。
    """

    try:
        target_path = (WORKSPACE_ROOT / path).resolve()

        try:
            target_path.relative_to(WORKSPACE_ROOT)
        except ValueError:
            return False, None, "安全限制：不能访问项目目录之外的路径。"

        return True, target_path, ""

    except Exception as e:
        return False, None, f"路径解析失败：{e}"


def list_files(path: str = ".") -> str:
    """
    查看当前项目目录下的文件和文件夹。
    """

    safe, target_path, error = is_safe_path(path)
    if not safe:
        return error

    try:
        if not target_path.exists():
            return f"路径不存在：{path}"

        if not target_path.is_dir():
            return f"这不是一个文件夹：{path}"

        items = []

        for item in sorted(target_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if item.name in [".venv", "__pycache__"]:
                continue

            if item.is_dir():
                items.append(f"[DIR]  {item.name}")
            else:
                items.append(f"[FILE] {item.name}")

        if not items:
            return f"目录 {path} 是空的。"

        return "\n".join(items)

    except Exception as e:
        return f"list_files 工具执行失败：{e}"


def read_file(path: str) -> str:
    """
    读取当前项目目录下的文本文件内容。
    """

    if not path:
        return "缺少 path 参数，请提供要读取的文件路径。"

    sensitive_names = [".env", "secret", "key", "password", "token"]

    lower_path = path.lower()
    for word in sensitive_names:
        if word in lower_path:
            return "安全限制：不能读取 .env、密钥、密码、token 等敏感文件内容。"

    safe, target_path, error = is_safe_path(path)
    if not safe:
        return error

    try:
        if not target_path.exists():
            return f"文件不存在：{path}"

        if not target_path.is_file():
            return f"这不是一个文件：{path}"

        max_size = 50 * 1024
        file_size = target_path.stat().st_size

        if file_size > max_size:
            return f"文件过大：{path}，大小为 {file_size} 字节。当前工具限制读取 50KB 以内的文本文件。"

        try:
            content = target_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = target_path.read_text(encoding="gbk", errors="ignore")

        if not content.strip():
            return f"文件 {path} 是空的。"

        max_chars = 8000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n……文件内容较长，后面部分已省略。"

        return content

    except Exception as e:
        return f"read_file 工具执行失败：{e}"


def run_command(command: str) -> str:
    """
    执行安全的命令行命令。
    这里只允许少量白名单命令。
    """

    if not command:
        return "缺少 command 参数，请提供要执行的命令。"

    command = command.strip()
    lower_command = command.lower()

    dangerous_symbols = ["&&", "||", ";", "|", ">", ">>", "<", "`"]
    for symbol in dangerous_symbols:
        if symbol in command:
            return f"安全限制：命令中包含危险符号 {symbol}，已拒绝执行。"

    dangerous_words = [
        "del", "erase", "rd", "rmdir", "remove-item",
        "rm", "move", "copy", "xcopy", "robocopy",
        "format", "shutdown", "restart-computer",
        "taskkill", "kill",
        "set-executionpolicy",
        "powershell", "cmd",
        "curl", "wget",
    ]

    for word in dangerous_words:
        if lower_command.startswith(word + " ") or lower_command == word:
            return f"安全限制：命令 {word} 可能有风险，已拒绝执行。"

    allowed_exact_commands = {
        "dir",
        "ls",
        "pwd",
        "python --version",
        "python -v",
        "pip --version",
        "pip list",
        "where python",
        "where pip",
    }

    allowed_prefixes = [
        "pip show ",
    ]

    is_allowed = False

    if lower_command in allowed_exact_commands:
        is_allowed = True

    for prefix in allowed_prefixes:
        if lower_command.startswith(prefix):
            is_allowed = True

    if not is_allowed:
        return (
            "安全限制：当前只允许执行这些安全命令：\n"
            "- dir\n"
            "- ls\n"
            "- pwd\n"
            "- python --version\n"
            "- pip list\n"
            "- pip show 包名\n"
            "- where python\n"
            "- where pip\n"
        )

    if lower_command == "pwd":
        return str(WORKSPACE_ROOT)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10
        )

        output = result.stdout.strip() or result.stderr.strip()

        if not output:
            return "命令执行完成，但没有输出内容。"

        max_chars = 8000
        if len(output) > max_chars:
            output = output[:max_chars] + "\n\n……输出内容较长，后面部分已省略。"

        return output

    except subprocess.TimeoutExpired:
        return "命令执行超时，已停止。"

    except Exception as e:
        return f"run_command 工具执行失败：{e}"


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "查看当前项目目录或其子目录中的文件和文件夹。适合回答：当前目录有什么、项目结构是什么、有哪些文件等问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要查看的目录路径。默认是当前项目根目录，用 . 表示。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取当前项目目录中的文本文件内容。适合回答：查看某个 Python 文件、解释某个代码文件、总结某个 README 或配置文件等问题。不要用于读取 .env 或密钥文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要读取的文件路径，例如 backend/agent.py。"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "执行安全的只读命令，例如查看 Python 版本、查看 pip 包列表、查看当前目录。不能用于删除、移动、修改文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的安全命令，例如 python --version、pip list、dir、pwd。"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": (
                "加载指定技能包的 SKILL.md 内容。"
                "当用户遇到 Python 报错、项目阅读、Agent 学习等任务时，"
                "可以先加载对应技能包，再按技能说明完成任务。"
                "可用技能包包括：python_debug、project_reader、agent_learning。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "要加载的技能包名称，例如 python_debug、project_reader、agent_learning。"
                    }
                },
                "required": ["skill_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_memory",
            "description": (
                "把用户明确要求长期记住的信息保存到本地 memory.json。"
                "只有当用户明确说“记住”“以后都”“下次要记得”等表达时才使用。"
                "不要保存 API Key、密码、token、身份证、银行卡等敏感信息。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要长期保存的记忆内容，例如：用户喜欢中文、分步骤解释。"
                    },
                    "category": {
                        "type": "string",
                        "description": "记忆分类，例如 preference、project、learning、general。"
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_memory",
            "description": "查看当前本地长期记忆。适合回答：你记得我什么、当前长期记忆有哪些。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
        {
        "type": "function",
        "function": {
            "name": "update_todos",
            "description": (
                "创建或更新当前任务计划 Todo 列表。"
                "当用户提出复杂任务、需要分步骤完成、要求制定计划时使用。"
                "会用新的 todos 列表覆盖当前 Todo。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "description": "任务列表，每个任务包含 content 和 status。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "任务内容。"
                                },
                                "status": {
                                    "type": "string",
                                    "description": "任务状态，只能是 pending、in_progress、completed。"
                                }
                            },
                            "required": ["content", "status"]
                        }
                    }
                },
                "required": ["todos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_todos",
            "description": "查看当前 Todo 任务列表。适合回答：当前计划是什么、还有哪些任务、进度如何。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


def run_tool(tool_name: str, tool_args: dict) -> str:
    """
    根据模型请求的工具名，调用真正的 Python 函数。
    """
    
    if tool_name == "list_files":
        path = tool_args.get("path", ".")
        return list_files(path)

    if tool_name == "read_file":
        path = tool_args.get("path", "")
        return read_file(path)

    if tool_name == "run_command":
        command = tool_args.get("command", "")
        return run_command(command)

    if tool_name == "load_skill":
        skill_name = tool_args.get("skill_name", "")
        return load_skill(skill_name)

    if tool_name == "remember_memory":
        content = tool_args.get("content", "")
        category = tool_args.get("category", "general")
        return add_memory(content, category)

    if tool_name == "list_memory":
        return list_memories_as_text()
    
    if  tool_name == "remember_memory":
        content = tool_args.get("content", "")
        category = tool_args.get("category", "general")

        try:
                memory = add_memory(content, category)
                return (
                    "已写入长期记忆："
                    f"[{memory['category']}] {memory['content']} "
                    f"(id={memory['id']}, created_at={memory['created_at']})"
                )
        except Exception as e:
                return f"remember_memory 执行失败：{e}"
    if tool_name == "list_memory":
        return list_memories_as_text()
    if tool_name == "update_todos":
        todos = tool_args.get("todos", [])
        return update_todos(todos)
    if tool_name == "list_todos":
        return list_todos_as_text() 
    return f"未知工具：{tool_name}"
    