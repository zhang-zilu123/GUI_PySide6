@echo off
REM ============================
REM  Auto-run script for GUI app
REM  - 解压后首次运行会执行 conda-unpack
REM  - 之后直接运行 app.py
REM ============================

REM 切换到当前脚本所在目录
cd /d %~dp0

REM 检查是否存在设备标识文件
if not exist "%~dp0device_id.txt" (
    echo The first run is generating the device identifier...
    call "%~dp0generate_uuid.bat"
)

REM 检查 mineru 是否存在
if not exist "mineru\python.exe" (
    echo [ERROR] mineru not found. Please extract mineru.tar.gz first.
    pause
    exit /b
)

REM 启动 GUI 程序
echo [INFO] Starting GUI program...
mineru\python.exe main.py
pause
