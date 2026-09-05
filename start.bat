@echo off
setlocal enabledelayedexpansion
title Enterprise Local AI Assistant - Launcher
cls

echo =====================================================================
echo           ENTERPRISE LOCAL AI ASSISTANT - LAUNCHER
echo =====================================================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: 1. Kiem tra Python Virtual Environment
set "PYTHON_VENV="
if exist "%ROOT_DIR%\.venv\Scripts\uvicorn.exe" (
    set "PYTHON_VENV=%ROOT_DIR%\.venv"
) else if exist "%ROOT_DIR%\backend\venv\Scripts\uvicorn.exe" (
    set "PYTHON_VENV=%ROOT_DIR%\backend\venv"
)

if "%PYTHON_VENV%"=="" (
    echo [ERROR] Khong tim thay Python Virtual Environment: .venv hoac backend\venv
    echo Vui long kiem tra lai thu muc du an.
    echo.
    pause
    exit /b 1
)
echo [*] Python Virtual Environment: %PYTHON_VENV%

:: 2. Kiem tra Ollama Service
echo [*] Kiem tra dich vu Ollama LLM...
netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo [*] Ollama service dang hoat dong tai cong 11434.
) else (
    echo [!] Cong 11434 chua mo, dang thu khoi dong Ollama serve...
    where ollama >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" (
            start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
        ) else (
            powershell -WindowStyle Hidden -Command "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
        )
        ping -n 3 127.0.0.1 >nul
    ) else (
        echo [WARNING] Khong tim thay lenh ollama trong PATH.
    )
)

:: 3. Khoi dong Backend FastAPI
echo [*] Dang khoi dong Backend FastAPI tai cong 8000...
pushd "%ROOT_DIR%\backend"
start "Enterprise AI - Backend API" "%PYTHON_VENV%\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000 --reload
popd

:: 4. Khoi dong Frontend React Vite
echo [*] Dang khoi dong Frontend React Vite tai cong 5173...
pushd "%ROOT_DIR%\frontend"
start "Enterprise AI - Frontend UI" cmd /k "npm run dev"
popd

:: 5. Cho server khoi dong va kiem tra trang thai ket noi
echo [*] Dang doi Backend (Port 8000) va Frontend (Port 5173) san sang...
set /a RETRY=0
:WAIT_LOOP
set "B_OK=0"
set "F_OK=0"
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 set "B_OK=1"
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 set "F_OK=1"

if !B_OK! EQU 1 if !F_OK! EQU 1 goto :SERVERS_READY

set /a RETRY+=1
if !RETRY! GEQ 15 goto :SERVERS_TIMEOUT
ping -n 2 127.0.0.1 >nul
goto :WAIT_LOOP

:SERVERS_READY
echo [OK] Backend va Frontend da khoi dong thanh cong va san sang ket noi!
goto :OPEN_BROWSER

:SERVERS_TIMEOUT
echo [!] He thong mat nhieu thoi gian khoi dong hon du kien, van se mo trinh duyet...

:OPEN_BROWSER
ping -n 2 127.0.0.1 >nul
start http://localhost:5173

cls
echo =====================================================================
echo      ENTERPRISE LOCAL AI ASSISTANT DA DUOC KHOI DONG THANH CONG!
echo =====================================================================
echo.
echo  Dia chi truy cap:
echo   - Giao dien Web (Frontend)  : http://localhost:5173
echo   - Tai lieu API (Swagger UI) : http://localhost:8000/docs
echo   - Ollama LLM Service        : http://127.0.0.1:11434
echo.
echo  Tai khoan thu nghiem:
echo   - Super Admin : superadmin / Admin@123456
echo   - IT Admin    : itadmin    / Admin@123456
echo   - Employee    : employee   / Employee@123456
echo.
echo  Huong dan tat he thong:
echo   - Chay file stop.bat de tat toan bo he thong.
echo =====================================================================
echo.
pause
