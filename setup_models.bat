@echo off
setlocal enabledelayedexpansion
title Cai dat mo hinh AI - Ollama Models Setup
cls

echo =====================================================================
echo         TAI VA CAI DAT MO HINH AI (OLLAMA PULL QWEN2.5:3B)
echo =====================================================================
echo.

:: 1. Kiem tra xem Ollama da cai dat chua
where ollama >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Khong tim thay Ollama tren he thong!
    echo Vui long cai dat Ollama tai https://ollama.com truoc.
    echo.
    pause
    exit /b 1
)

:: 2. Kiem tra dich vu Ollama
netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [*] Dang bat dich vu Ollama chay ngam...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" (
        start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
    ) else (
        powershell -WindowStyle Hidden -Command "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
    )
    ping -n 4 127.0.0.1 >nul
)

echo.
echo [1/2] Dang tai mo hinh LLM chinh (qwen2.5:3b - dung luong ~1.9GB)...
echo       (Vui long cho trong giay lat neu dang tai lan dau)
ollama pull qwen2.5:3b

echo.
echo [2/2] Dang tai mo hinh Embedding (nomic-embed-text - dung luong ~274MB)...
ollama pull nomic-embed-text

cls
echo =====================================================================
echo         DA TAI VA CAU HINH MO HINH AI THANH CONG!
echo =====================================================================
echo.
echo Danh sach mo hinh hien co tren may:
ollama list
echo.
echo Cua so Backend va Frontend da san sang su dung qwen2.5:3b.
echo Ban co the chay file 'start.bat' de bat he thong ngay bay gio.
echo =====================================================================
echo.
pause
