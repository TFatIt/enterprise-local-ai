@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Enterprise Local AI - Docker Launcher
cls

echo =====================================================================
echo           ENTERPRISE LOCAL AI ASSISTANT - DOCKER RUN
echo =====================================================================
echo.

:: 1. Chuyen ve thu muc goc cua du an
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"

:: 2. Kiem tra Docker da duoc cai dat chua
where docker >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Docker chua duoc cai dat hoac chua co trong bien moi truong PATH.
    echo Vui long cai dat Docker Desktop: https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

:: 3. Kiem tra Docker Daemon dang chay hay chua
echo [*] Kiem tra ket noi Docker Desktop Engine...
docker info >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Docker Desktop chua bat, dang thu tu dong khoi dong Docker Desktop...
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) else (
        echo [!] Vui long bat ung dung Docker Desktop bang tay.
    )

    echo [*] Dang cho Docker Engine khoi tao (khoang 15-30 giay)...
    set "WAIT_COUNT=0"
    :WAIT_DOCKER
    ping -n 3 127.0.0.1 >nul
    docker info >nul 2>&1
    if !errorlevel! equ 0 goto DOCKER_READY
    set /a WAIT_COUNT+=1
    if !WAIT_COUNT! geq 15 (
        echo [ERROR] Docker Desktop chua san sang. Vui long kiem tra lai Docker Desktop!
        pause
        exit /b 1
    )
    echo     ... Dang cho Docker Engine ready (!WAIT_COUNT!/15)
    goto WAIT_DOCKER
)

:DOCKER_READY
echo [OK] Docker Desktop Engine dang hoat dong tot!
echo.

:: 4. Kiem tra dich vu Ollama AI (port 11434)
echo [*] Kiem tra dich vu Ollama Local AI...
netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Ollama service dang hoat dong san sang tren cong 11434.
) else (
    echo [!] Cong 11434 chua bat, dang tu dong khoi dong Ollama serve...
    where ollama >nul 2>&1
    if !errorlevel! equ 0 (
        if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" (
            start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
        ) else (
            powershell -WindowStyle Hidden -Command "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
        )
        ping -n 4 127.0.0.1 >nul
    ) else (
        echo [WARN] Khong tim thay lenh ollama trong PATH. AI chat se can bat Ollama thu cong.
    )
)
echo.

:: 5. Khoi dong toan bo he thong bang Docker Compose
echo [*] Dang khoi dong cac containers (Postgres, Backend, Frontend)...
docker compose up -d

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Khong the khoi dong Docker Compose!
    echo Vui long kiem tra file docker-compose.yml hoac logs.
    pause
    exit /b 1
)

echo.
cls
echo =====================================================================
echo      HE THONG ENTERPRISE LOCAL AI DANG CHAY TREN DOCKER
echo =====================================================================
echo.
echo  Cac dich vu dang hoat dong:
echo   [1] Giao dien Web (Frontend)   : http://localhost:3000
echo   [2] Tai lieu API (Swagger UI)  : http://localhost:8000/docs
echo   [3] Co so du lieu PostgreSQL   : localhost:5433 (User: enterprise_admin)
echo   [4] Dich vu Ollama LLM         : http://host.docker.internal:11434
echo.
echo  Tai khoan thu nghiem:
echo   - Super Admin : superadmin / Admin@123456
echo   - IT Admin    : itadmin    / Admin@123456
echo   - Employee    : employee   / Employee@123456
echo.
echo =====================================================================
echo [*] Dang tu dong mo trinh duyet den: http://localhost:3000 ...
start "" "http://localhost:3000"
echo.
echo Tuy chon quan ly:
echo   [L] Xem nhat ky hoat dong realtime (docker compose logs -f)
echo   [S] Dung toan bo he thong Docker (docker compose stop)
echo   [Enter] De he thong tiep tuc chay ngam va thoat cua so nay.
echo.
set /p "CHOICE=Nhap lua chon cua ban (L / S / Enter): "

if /i "!CHOICE!"=="L" (
    docker compose logs -f
) else if /i "!CHOICE!"=="S" (
    echo [*] Dang dung he thong...
    docker compose stop
    echo [OK] Da dung he thong thanh cong.
    pause
) else (
    echo [*] He thong Docker dang tiep tuc chay an duoi nen.
)
