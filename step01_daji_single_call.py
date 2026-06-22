import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL")

if not API_KEY:
    raise RuntimeError("没有读取到 OPENAI_API_KEY，请检查 .env 文件")
if not MODEL:
    raise RuntimeError("没有读取到 OPENAI_MODEL，请检查 .env 文件")

client_config ={
    "api_key":API_KEY
}

if BASE_URL:
    client_config["base_url"] = BASE_URL

client = OpenAI(**client_config)

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
4. 回答时要清楚、有步骤，适合新手理解。

你的边界：
1. 不知道就说不知道，不要编造。
2. 没有实际执行过的事情，不要假装执行过。
3. 涉及文件、命令、网络结果时，要提醒用户需要实际验证。
4. 不泄露用户的 API Key、隐私和配置。

回答要求：
1. 中文为主。
2. 先直接回答用户问题。
3. 复杂问题要分步骤。
4. 不要只说漂亮话，要给可执行的建议。
5. 当用户询问你是谁、介绍自己、身份设定时，结尾可以加一句：“请尽情吩咐妲己，主人。”
"""
def ask_daji(user_input: str) -> str:
    """
    单次调用大模型，让 Daji Agent 回复用户。
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": DAJI_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    reply = response.choices[0].message.content
    return reply


def main():
    print("====================================")
    print("  Daji Agent Studio - Step 01")
    print("  妲己智能体工作台：单次对话版")
    print("====================================")
    print("输入一句话，看看妲己如何回答。")
    print()

    user_input = input("你：")

    reply = ask_daji(user_input)

    print()
    print("妲己：")
    print(reply)


if __name__ == "__main__":
    main()