@echo off
chcp 65001 >nul
echo ========================================
echo   Task Management API - 启动中...
echo ========================================
echo.

set "PYTHON=python"

REM 检查虚拟环境是否存在
if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
    echo [INFO] 使用虚拟环境: venv\Scripts\python.exe
) else (
    echo [WARNING] 未检测到虚拟环境，尝试使用系统 Python
    echo [TIP] 建议先创建虚拟环境: python -m venv venv
)

REM 检查依赖是否已安装
%PYTHON% -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [INFO] 正在安装依赖...
    %PYTHON% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] 依赖安装失败，请检查 Python 环境配置
        pause
        exit /b 1
    )
)

echo.
echo [INFO] 启动服务: http://localhost:8000
echo [INFO] API 文档: http://localhost:8000/api/v1/docs
echo [INFO] 按 Ctrl+C 停止服务
echo.
%PYTHON% -m uvicorn task_api.main:app --reload --host 0.0.0.0 --port 8000

pause
