import json
import uuid
from datetime import datetime
from pathlib import Path


WORKSPACE_ROOT = Path.cwd().resolve()
DATA_DIR = WORKSPACE_ROOT / "data"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"


def ensure_history_file():
    """
    确保 data/chat_history.json 存在。
    """

    DATA_DIR.mkdir(exist_ok=True)

    if not CHAT_HISTORY_FILE.exists():
        CHAT_HISTORY_FILE.write_text("[]", encoding="utf-8")


def read_chat_history() -> list[dict]:
    """
    读取聊天记录。
    """

    ensure_history_file()

    try:
        content = CHAT_HISTORY_FILE.read_text(encoding="utf-8")
        history = json.loads(content)

        if not isinstance(history, list):
            return []

        return history

    except Exception:
        return []


def write_chat_history(history: list[dict]) -> None:
    """
    写入聊天记录。
    """

    ensure_history_file()

    CHAT_HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def add_chat_record(user_message: str, reply: str, steps: list[dict]) -> dict:
    """
    新增一条聊天记录。
    """

    history = read_chat_history()

    record = {
        "id": str(uuid.uuid4())[:8],
        "user": user_message,
        "reply": reply,
        "steps": steps,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    history.append(record)

    # 最多保留最近 100 条，避免文件无限变大
    history = history[-100:]

    write_chat_history(history)

    return record


def clear_chat_history() -> None:
    """
    清空聊天记录。
    """

    write_chat_history([])

def build_recent_chat_messages(limit: int = 10) -> list[dict]:
    """
    把最近的聊天记录转换成可注入大模型 messages 的格式。

    注意：
    这里只恢复 user 和 assistant 的最终回复。
    不恢复 tool 消息，避免 tool_call_id 配对错误。
    """

    history = read_chat_history()

    if not history:
        return []

    recent_history = history[-limit:]

    messages = []

    for record in recent_history:
        user_message = str(record.get("user", "")).strip()
        assistant_reply = str(record.get("reply", "")).strip()

        if user_message:
            messages.append({
                "role": "user",
                "content": user_message
            })

        if assistant_reply:
            messages.append({
                "role": "assistant",
                "content": assistant_reply
            })

    return messages