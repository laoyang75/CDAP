@echo off
REM CDID 数据分析平台一键启动脚本 (Windows)

cd /d "%~dp0"

echo 🚀 启动 CDID 数据分析平台...
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未找到，请先安装 Python 3.11+
    pause
    exit /b 1
)

REM 运行启动器
python launcher.py

pause
