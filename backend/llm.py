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


client_config = {
    "api_key": API_KEY
}

if BASE_URL:
    client_config["base_url"] = BASE_URL

client = OpenAI(**client_config)