import json
import uuid
from datetime import datetime
from pathlib import Path


WORKSPACE_ROOT = Path.cwd().resolve()
DATA_DIR = WORKSPACE_ROOT / "data"
TODO_FILE = DATA_DIR / "todos.json"


VALID_STATUS = {"pending", "in_progress", "completed"}


def ensure_todo_file():
    """
    确保 data/todos.json 存在。
    """

    DATA_DIR.mkdir(exist_ok=True)

    if not TODO_FILE.exists():
        TODO_FILE.write_text("[]", encoding="utf-8")


def read_todos() -> list[dict]:
    """
    读取 Todo 列表。
    """

    ensure_todo_file()

    try:
        content = TODO_FILE.read_text(encoding="utf-8")
        todos = json.loads(content)

        if not isinstance(todos, list):
            return []

        return todos

    except Exception:
        return []


def write_todos(todos: list[dict]) -> None:
    """
    写入 Todo 列表。
    """

    ensure_todo_file()

    TODO_FILE.write_text(
        json.dumps(todos, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def normalize_status(status: str) -> str:
    """
    规范化任务状态。
    """

    status = (status or "pending").strip()

    if status not in VALID_STATUS:
        return "pending"

    return status


def update_todos(todos: list[dict]) -> str:
    """
    用新的 Todo 列表覆盖当前 Todo。
    """

    if not isinstance(todos, list):
        return "update_todos 失败：todos 必须是列表。"

    normalized_todos = []

    for index, item in enumerate(todos, start=1):
        if not isinstance(item, dict):
            continue

        content = str(item.get("content", "")).strip()
        status = normalize_status(str(item.get("status", "pending")))

        if not content:
            continue

        normalized_todos.append({
            "id": item.get("id") or str(uuid.uuid4())[:8],
            "content": content,
            "status": status,
            "order": index,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    write_todos(normalized_todos)

    if not normalized_todos:
        return "Todo 列表已清空。"

    lines = ["Todo 列表已更新："]

    for todo in normalized_todos:
        lines.append(
            f"{todo['order']}. [{todo['status']}] {todo['content']} "
            f"(id={todo['id']})"
        )

    return "\n".join(lines)


def list_todos_as_text() -> str:
    """
    把 Todo 列表整理成文本。
    """

    todos = read_todos()

    if not todos:
        return "当前没有 Todo 任务。"

    lines = []

    for todo in sorted(todos, key=lambda x: x.get("order", 999)):
        lines.append(
            f"{todo.get('order', '')}. "
            f"[{todo.get('status', 'pending')}] "
            f"{todo.get('content', '')} "
            f"(id={todo.get('id', '')}, updated_at={todo.get('updated_at', '')})"
        )

    return "\n".join(lines)


def clear_todos() -> None:
    """
    清空 Todo。
    """

    write_todos([])