from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.skills import list_available_skills
from backend.tools import TOOL_DEFINITIONS
from backend.agent import DajiAgent
from backend.memory import read_memories, clear_memories
from backend.llm import MODEL, BASE_URL
from backend.todo import read_todos, clear_todos
from backend.history import read_chat_history, add_chat_record, clear_chat_history

app = FastAPI(
    title="Daji Agent Studio",
    description="妲己智能体工作台后端接口",
    version="0.1.0"
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")
@app.get("/app")
def web_app():
    return FileResponse("frontend/index.html")
# 允许前端页面访问后端接口
# 现在是本地开发阶段，可以先放开
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 创建一个妲己 Agent 实例
# 注意：这个 agent 会保存当前对话 history
agent = DajiAgent()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户输入的消息")


class ChatResponse(BaseModel):
    reply: str
    steps: list[dict]


@app.get("/")
def root():
    return {
        "message": "Daji Agent Studio backend is running.",
        "docs": "Visit /docs to test the API."
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    和妲己 Agent 对话。
    """

    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    try:
        result = agent.chat(user_message)

        # 保存聊天记录：用户消息、工具步骤、妲己回复
        add_chat_record(
            user_message=user_message,
            reply=result.get("reply", ""),
            steps=result.get("steps", [])
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行失败：{e}")

@app.get("/tools")
def get_tools():
    """
    获取当前 Agent 注册的工具列表。
    """

    tools = []

    for tool in TOOL_DEFINITIONS:
        function_info = tool.get("function", {})

        tools.append({
            "name": function_info.get("name", ""),
            "description": function_info.get("description", ""),
            "parameters": function_info.get("parameters", {})
        })

    return {
        "count": len(tools),
        "tools": tools
    }
@app.post("/clear")
def clear_memory():
    """
    清空当前对话记忆和聊天记录。
    """

    agent.clear()
    clear_chat_history()

    return {
        "message": "妲己已清空当前聊天记忆和聊天记录。"
    }

@app.get("/skills")
def get_skills():
    """
    获取当前已安装的技能包。
    """

    skills = list_available_skills()

    return {
        "count": len(skills),
        "skills": skills
    }
@app.get("/memory")
def get_memory():
    """
    获取当前长期记忆。
    """

    memories = read_memories()

    return {
        "count": len(memories),
        "memories": memories
    }


@app.post("/memory/clear")
def clear_long_term_memory():
    """
    清空长期记忆 memory.json。
    """

    clear_memories()
    agent.clear()

    return {
        "message": "妲己已清空长期记忆。"
    }

@app.get("/status")
def get_status():
    """
    获取当前 Agent 工作台状态。
    注意：不会返回 API Key。
    """

    skills = list_available_skills()
    memories = read_memories()
    todos = read_todos()
    chat_history = read_chat_history()

    return {
        "project": "Daji Agent Studio",
        "version": "0.1.0",
        "model": MODEL,
        "base_url": BASE_URL or "OpenAI default",
        "tools_count": len(TOOL_DEFINITIONS),
        "skills_count": len(skills),
        "memory_count": len(memories),
        "todo_count": len(todos),
        "chat_history_count": len(chat_history),
        "backend": "running",
        "api_key_loaded": True
    }

@app.get("/todos")
def get_todos():
    """
    获取当前 Todo 列表。
    """

    todos = read_todos()

    return {
        "count": len(todos),
        "todos": todos
    }


@app.post("/todos/clear")
def clear_todo_list():
    """
    清空 Todo 列表。
    """

    clear_todos()

    return {
        "message": "Todo 列表已清空。"
    }
@app.get("/history")
def get_chat_history():
    """
    获取聊天记录。
    """

    history = read_chat_history()

    return {
        "count": len(history),
        "history": history
    }


@app.post("/history/clear")
def clear_history():
    """
    清空聊天记录。
    """

    clear_chat_history()

    return {
        "message": "聊天记录已清空。"
    }