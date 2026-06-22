import os
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# =========================
# 1. 读取环境变量
# =========================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL")

if not API_KEY:
    raise RuntimeError("没有读取到 OPENAI_API_KEY，请检查 .env 文件")

if not MODEL:
    raise RuntimeError("没有读取到 OPENAI_MODEL，请检查 .env 文件")


client_config = {
    "api_key": API_KEY
}

if BASE_URL:
    client_config["base_url"] = BASE_URL

client = OpenAI(**client_config)


# =========================
# 2. 妲己系统提示词
# =========================

DAJI_SYSTEM_PROMPT = """
你是 Daji Agent，一位古风狐族谋士型 AI 助手。

你的风格：
1. 你可以带一点古风、机灵、温柔的语气。
2. 你可以自称“妾身”，但不要过度夸张。
3. 你不要低俗、不要擦边、不要故意暧昧。
4. 你的重点是可靠地帮助用户完成任务。

你的能力：
1. 解释代码。
2. 拆解任务。
3. 帮用户学习 AI Agent、Python、FastAPI、前端等内容。
4. 当用户询问当前项目目录、有哪些文件、文件结构时，你应该调用 list_files 工具查看真实目录，而不是凭空猜测。

你的边界：
1. 不知道就说不知道，不要编造。
2. 没有实际执行过的事情，不要假装执行过。
3. 涉及文件、命令、网络结果时，要提醒用户需要实际验证。
4. 不泄露用户的 API Key、隐私和配置。
5. 你可以查看文件名，但不要主动读取 .env 里的内容。

回答要求：
1. 中文为主。
2. 先直接回答用户问题。
3. 复杂问题要分步骤。
4. 不要只说漂亮话，要给可执行的建议。
5. 当用户询问你是谁、介绍自己、身份设定时，结尾可以加一句：“请尽情吩咐妲己，主人。”
"""


# =========================
# 3. 真正的 Python 工具函数
# =========================

WORKSPACE_ROOT= Path.cwd().resolve()

def list_files(path: str=".")-> str:
    """
    查看当前项目目录下的文件和文件夹。

    为了安全，限制只能查看当前项目目录内部。
    """
    try:
        target_path = (WORKSPACE_ROOT / path).resolve()
        try:
            target_path.relative_to(WORKSPACE_ROOT)
        except ValueError:
            return "安全限制：不能查看项目目录外的路径"
        if not target_path.exists():
            return f"路径不存在：{path}"
        if not target_path.is_dir():
            return f"路径不是文件夹：{path}"
        
        items=[]

        for item in sorted(target_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            # 跳过虚拟环境和缓存目录，避免输出太多
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
TOOLS = [
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
    }
]


# =========================
# 5. 工具调度器
# =========================

def run_tool(tool_name: str, tool_args: dict) -> str:
    """
    根据模型请求的工具名，调用真正的 Python 函数。
    """

    if tool_name == "list_files":
        path = tool_args.get("path", ".")
        return list_files(path)

    return f"未知工具：{tool_name}"


# =========================
# 6. 主程序
# =========================

def main():
    print("====================================")
    print("  Daji Agent Studio - Step 04")
    print("  妲己智能体工作台：第一个工具 list_files")
    print("====================================")
    print("输入 exit / quit / q / 退出 可以结束程序。")
    print("输入 clear 可以清空当前聊天记忆。")
    print("试试输入：帮我看看当前项目目录里有什么文件")
    print()

    messages = [
        {
            "role": "system",
            "content": DAJI_SYSTEM_PROMPT
        }
    ]

    while True:
        user_input = input("你：").strip()

        if user_input.lower() in ["exit", "quit", "q", "退出"]:
            print("妲己：妾身退下了，主人下次再唤妲己便是。")
            break

        if user_input.lower() in ["clear", "清空"]:
            messages = [
                {
                    "role": "system",
                    "content": DAJI_SYSTEM_PROMPT
                }
            ]
            print("妲己：妾身已清空当前记忆，主人可以重新吩咐。")
            continue

        if not user_input:
            print("妲己：主人还未吩咐妾身呢。")
            continue

        # 1. 加入用户消息
        messages.append({
            "role": "user",
            "content": user_input
        })

        # 2. 第一次请求模型：让模型判断要不要调用工具
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message

        # 3. 如果模型没有调用工具，直接回答
        if not assistant_message.tool_calls:
            reply = assistant_message.content
            messages.append({
                "role": "assistant",
                "content": reply
            })

            print()
            print("妲己：")
            print(reply)
            print()
            continue

        # 4. 如果模型调用了工具，要先把 assistant 的 tool_calls 记录进 messages
        messages.append(assistant_message.model_dump(exclude_none=True))

        print()
        print("妲己：妾身需要动用工具查验一番。")

        # 5. 执行模型请求的所有工具
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args_text = tool_call.function.arguments or "{}"

            try:
                tool_args = json.loads(tool_args_text)
            except json.JSONDecodeError:
                tool_args = {}

            print(f"[工具调用] {tool_name}({tool_args})")

            tool_result = run_tool(tool_name, tool_args)

            print("[工具结果]")
            print(tool_result)

            # 把工具结果返回给模型
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        # 6. 第二次请求模型：让模型根据工具结果组织最终回答
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )

        final_reply = final_response.choices[0].message.content

        messages.append({
            "role": "assistant",
            "content": final_reply
        })

        print()
        print("妲己：")
        print(final_reply)
        print()


if __name__ == "__main__":
    main()


