@echo off
setlocal enabledelayedexpansion
title Ollama Local AI - Background Service
cls

echo =====================================================================
echo         KHOI DONG DICH VU OLLAMA CHAY NGAM - CHO CHAT AI
echo =====================================================================
echo.

:: 1. Kiem tra xem cong 11434 da mo chua
netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo [*] Ollama da duoc bat va dang chay ngam san sang tren cong 11434.
    goto :DONE
)

echo [*] Dang khoi dong Ollama serve chay ngam...

:: Uu tien 1: Khoi dong qua Ollama App (khay he thong) neu co
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" (
    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
) else (
    where ollama >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        powershell -WindowStyle Hidden -Command "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
    ) else (
        echo [ERROR] Khong tim thay Ollama tren may tinh!
        echo Vui long cai dat Ollama tai https://ollama.com truoc khi tiep tuc.
        echo.
        pause
        exit /b 1
    )
)

:: Cho 3 giay de server khoi tao
ping -n 4 127.0.0.1 >nul

netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo [OK] Khoi dong Ollama chay ngam thanh cong!
) else (
    echo [!] Server dang tiep tuc khoi dong, vui long doi them vai giay...
)

:DONE
cls
echo =====================================================================
echo           DICH VU OLLAMA LOCAL AI DANG CHAY NGAM
echo =====================================================================
echo.
echo  Trang thai    : DANG HOAT DONG - Chay an duoi nen (Background)
echo  Dia chi API   : http://127.0.0.1:11434
echo  Mo hinh Chat  : qwen2.5:3b
echo  Mo hinh Embed : nomic-embed-text
echo.
echo  He thong da san sang phuc vu Chat AI va Vector Search.
echo  De tat Ollama chay ngam, ban chi can chay file stop_ollama.bat
echo =====================================================================
echo.
pause
