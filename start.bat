@echo off
chcp 65001 >nul
title Daji Agent Studio

echo ====================================
echo   Daji Agent Studio
echo   妲己智能体工作台启动中...
echo ====================================
echo.

if not exist .venv (
    echo [ERROR] 未找到 .venv 虚拟环境。
    echo 请先运行：
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    pause
    exit /b
)

if not exist .env (
    echo [ERROR] 未找到 .env 配置文件。
    echo 请复制 .env.example 为 .env，并填写 API Key。
    echo.
    echo copy .env.example .env
    pause
    exit /b
)

call .venv\Scripts\activate

echo [INFO] 正在启动 FastAPI 后端...
echo [INFO] 启动成功后，请打开：
echo http://127.0.0.1:8000/app
echo.

uvicorn backend.main:app --reload

pause