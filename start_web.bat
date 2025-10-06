@echo off
chcp 65001 >nul
title JiuCi AI伴侣 - Web服务启动器

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🌸 九辞AI伴侣 Web版 🌸                      ║
echo ║                                                              ║
echo ║  💕 青春可爱的AI女朋友聊天网页                                   ║
echo ║  🎵 支持语音合成和播放                                          ║
echo ║  🧠 集成情感分析系统                                            ║
echo ║  🌈 全新架构，更稳定更强大                                       ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ 检测到Python环境

:: 检查是否需要安装依赖
if not exist "venv\" (
    echo 📦 首次运行，正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 激活虚拟环境失败
    pause
    exit /b 1
)

echo ✅ 虚拟环境已激活

:: 安装依赖
echo 📦 检查并安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo ✅ 依赖检查完成

:: 启动Web服务
echo 🚀 启动Web服务...
echo.
echo 🌐 服务将在 http://localhost:5000 启动
echo 📡 API状态: http://localhost:5000/api/status
echo.
echo 按 Ctrl+C 停止服务
echo.

cd Web
python app.py

echo.
echo 👋 服务已停止
pause