@echo off
setlocal enabledelayedexpansion
title Enterprise Local AI Assistant - Shutdown
cls

echo =====================================================================
echo             ENTERPRISE LOCAL AI ASSISTANT - SHUTDOWN
echo =====================================================================
echo.
echo [*] Dang tim va tat cac tien trinh tai cong 8000 va 5173...

:: Tat port 8000 (Backend FastAPI)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo [*] Dung Backend PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

:: Tat port 5173 (Frontend Vite)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo [*] Dung Frontend PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [OK] Da dung tat ca dich vu thanh cong.
echo.
pause
