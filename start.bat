@echo off
chcp 65001 >nul
cd /d "C:\Users\张和坤\Documents\AIAgent"
title 校园知识问答 Agent
echo.
echo   ================================
echo     校园知识问答 Agent 正在启动
echo   ================================
echo.
echo   浏览器打开: http://localhost:8000
echo   管理后台:   http://localhost:8000/admin
echo   按 Ctrl+C 停止服务器
echo.
venv\Scripts\python.exe server\main.py
pause
