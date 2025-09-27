@echo off
setlocal enabledelayedexpansion

REM 生成基于硬件信息的唯一标识
for /f "tokens=2 delims==" %%a in ('wmic csproduct get uuid /value') do set MACHINE_UUID=%%a
for /f "tokens=2 delims==" %%a in ('wmic bios get serialnumber /value') do set BIOS_SERIAL=%%a

REM 如果获取不到UUID，使用MAC地址作为备用
if "%MACHINE_UUID%"=="" (
    for /f "skip=3 tokens=2" %%a in ('getmac /fo csv /nh') do (
        set MAC_ADDR=%%a
        goto :break
    )
    :break
    set IDENTIFIER=!MAC_ADDR:"=!
) else (
    set IDENTIFIER=%MACHINE_UUID%
)

REM 保存到本地文件
echo %IDENTIFIER% > "%~dp0device_id.txt"
echo 设备唯一标识已生成: %IDENTIFIER%
