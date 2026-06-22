import json
import uuid
from datetime import datetime
from pathlib import Path

WORKSPACE_ROOT = Path.cwd().resolve()
DATA_DIR = WORKSPACE_ROOT / "data"
MEMORY_FILE = DATA_DIR / "memory.json"

def ensure_memory_file():
    """
    确保 data/memory.json 存在。
    """

    DATA_DIR.mkdir(exist_ok=True)

    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text("[]", encoding="utf-8")


def read_memories() -> list[dict]:
    """
    读取长期记忆列表。
    """

    ensure_memory_file()

    try:
        content = MEMORY_FILE.read_text(encoding="utf-8")
        memories = json.loads(content)

        if not isinstance(memories, list):
            return []

        return memories

    except Exception:
        return []


def write_memories(memories: list[dict]) -> None:
    """
    写入长期记忆列表。
    """

    ensure_memory_file()

    MEMORY_FILE.write_text(
        json.dumps(memories, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def is_sensitive_memory(content: str) -> bool:
    """
    简单拦截不适合保存的敏感内容。
    """

    lower_content = content.lower()

    sensitive_words = [
        "api_key",
        "apikey",
        "secret",
        "password",
        "token",
        "sk-",
        "密钥",
        "密码",
        "身份证",
        "银行卡",
    ]

    return any(word in lower_content for word in sensitive_words)


def add_memory(content: str, category: str = "general") -> dict:
    """
    添加一条长期记忆。
    """

    content = content.strip()
    category = category.strip() or "general"

    if not content:
        raise ValueError("记忆内容不能为空。")

    if is_sensitive_memory(content):
        raise ValueError("安全限制：不保存 API Key、密码、token、身份证、银行卡等敏感信息。")

    memories = read_memories()

    memory = {
        "id": str(uuid.uuid4())[:8],
        "content": content,
        "category": category,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    memories.append(memory)
    write_memories(memories)

    return memory


def list_memories_as_text() -> str:
    """
    把长期记忆整理成文本，方便返回给模型。
    """

    memories = read_memories()

    if not memories:
        return "当前没有长期记忆。"

    lines = []

    for index, memory in enumerate(memories, start=1):
        lines.append(
            f"{index}. [{memory.get('category', 'general')}] "
            f"{memory.get('content', '')} "
            f"(id={memory.get('id', '')}, created_at={memory.get('created_at', '')})"
        )

    return "\n".join(lines)


def build_memory_context(max_items: int = 20) -> str:
    """
    构建注入 system prompt 的长期记忆上下文。
    """

    memories = read_memories()

    if not memories:
        return "暂无长期记忆。"

    recent_memories = memories[-max_items:]

    lines = []

    for memory in recent_memories:
        lines.append(
            f"- [{memory.get('category', 'general')}] {memory.get('content', '')}"
        )

    return "\n".join(lines)


def clear_memories() -> None:
    """
    清空长期记忆。
    """

    write_memories([])