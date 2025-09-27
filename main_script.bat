@echo off
setlocal enabledelayedexpansion

REM 检查是否存在设备标识文件
if not exist "%~dp0device_id.txt" (
    echo 首次运行，正在生成设备标识...
    call "%~dp0generate_uuid.bat"
)

REM 读取设备标识
set /p DEVICE_ID=<"%~dp0device_id.txt"
echo 当前设备标识: %DEVICE_ID%

REM 上传标识到服务器（这里只是示例）
echo 正在向服务器注册设备...
REM curl -X POST -d "device_id=%DEVICE_ID%" http://your-server.com/register

REM 你的主要业务逻辑
echo 执行主要程序...
REM 在这里添加你的核心功能代码

pause
