import json

from backend.llm import client, MODEL
from backend.prompts import DAJI_SYSTEM_PROMPT
from backend.tools import TOOL_DEFINITIONS, run_tool
from backend.memory import build_memory_context
from backend.history import build_recent_chat_messages


class DajiAgent:
    """
    妲己 Agent 核心类。

    负责：
    1. 保存短期对话历史
    2. 注入长期记忆
    3. 后端启动时恢复最近聊天上下文
    4. 调用大模型
    5. 判断是否需要工具
    6. 支持多轮工具调用
    7. 返回最终回复
    """

    def __init__(self):
        # 后端启动时，恢复最近聊天上下文
        self.messages = self._new_messages(restore_chat_history=True)

    def _build_system_prompt(self) -> str:
        """
        构建带长期记忆的 system prompt。
        """

        memory_context = build_memory_context()

        return (
            DAJI_SYSTEM_PROMPT
            + "\n\n【长期记忆】\n"
            + memory_context
        )

    def _new_messages(self, restore_chat_history: bool = False) -> list[dict]:
        """
        创建新的 messages。

        restore_chat_history=True：
        后端启动时恢复最近聊天记录。

        restore_chat_history=False：
        清空当前会话时，不恢复旧聊天。
        """

        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt()
            }
        ]

        if restore_chat_history:
            recent_messages = build_recent_chat_messages(limit=10)
            messages.extend(recent_messages)

        return messages

    def clear(self):
        """
        清空当前聊天记忆。
        注意：
        这里只重置后端短期上下文，不恢复 chat_history。
        main.py 里的 /clear 会同时清空 data/chat_history.json。
        """

        self.messages = self._new_messages(restore_chat_history=False)

    def _append_assistant_tool_message(self, assistant_message):
        """
        把带 tool_calls 的 assistant 消息加入历史。

        关键点：
        DeepSeek 的 OpenAI 兼容接口要求 content 必须是字符串，不能是 None。
        """

        assistant_tool_message = {
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                tool_call.model_dump(exclude_none=True)
                for tool_call in assistant_message.tool_calls
            ]
        }

        self.messages.append(assistant_tool_message)

    def _run_tool_calls(self, assistant_message, steps: list):
        """
        执行模型请求的所有工具调用，并把工具结果写回 messages。
        """

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args_text = tool_call.function.arguments or "{}"

            try:
                tool_args = json.loads(tool_args_text)
            except json.JSONDecodeError:
                tool_args = {}

            tool_result = run_tool(tool_name, tool_args)

            steps.append({
                "tool": tool_name,
                "args": tool_args,
                "result": str(tool_result)
            })

            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(tool_result)
            })

    def chat(self, user_input: str) -> dict:
        """
        和妲己对话一次。

        多轮工具循环逻辑：

        用户输入
        ↓
        模型判断是否调用工具
        ↓
        如果调用工具：Python 执行工具，把结果返回给模型
        ↓
        模型继续判断是否还要调用工具
        ↓
        最终没有工具调用时，输出最终回答
        """

        steps = []

        self.messages.append({
            "role": "user",
            "content": user_input
        })

        max_tool_rounds = 5

        for _ in range(max_tool_rounds):
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # 情况一：模型没有继续调用工具，说明可以最终回答
            if not assistant_message.tool_calls:
                final_reply = assistant_message.content or ""

                self.messages.append({
                    "role": "assistant",
                    "content": final_reply
                })

                return {
                    "reply": final_reply,
                    "steps": steps
                }

            # 情况二：模型调用了工具
            self._append_assistant_tool_message(assistant_message)
            self._run_tool_calls(assistant_message, steps)

        # 如果超过最大工具轮数，强制让模型总结已有结果，避免无限循环
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=self.messages + [
                {
                    "role": "user",
                    "content": (
                        "你已经进行了多轮工具调用。现在请停止继续调用工具，"
                        "根据已有工具结果给出最终总结。"
                    )
                }
            ]
        )

        final_reply = final_response.choices[0].message.content or ""

        self.messages.append({
            "role": "assistant",
            "content": final_reply
        })

        return {
            "reply": final_reply,
            "steps": steps
        }