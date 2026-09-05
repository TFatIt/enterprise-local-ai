@echo off
setlocal enabledelayedexpansion
title Dung dich vu Ollama
cls

echo =====================================================================
echo                 DUNG DICH VU OLLAMA CHAY NGAM
echo =====================================================================
echo.
echo [*] Dang tim va tat tien trinh Ollama chay ngam...

taskkill /F /IM ollama.exe >nul 2>&1
taskkill /F /IM "ollama app.exe" >nul 2>&1

ping -n 2 127.0.0.1 >nul

netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo [!] Cong 11434 van con tien trinh, dang dong bat buoc...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":11434" ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo [OK] Da dung dich vu Ollama va giai phong bo nho RAM / VRAM thanh cong.
echo.
pause
