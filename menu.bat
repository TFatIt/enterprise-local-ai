@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Enterprise Local AI - Control Center

:: Di chuyen ve thu muc goc cua du an
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"

:MENU
cls
echo ====================================================================================
echo                 ENTERPRISE LOCAL AI ASSISTANT - TRUNG TÂM ĐIỀU KHIỂN
echo ====================================================================================
echo.
echo   [ DOCKER CONTAINERS ]
echo     1. 🐳 Bật toàn bộ hệ thống bằng Docker (Web: 3000, API: 8000, DB: 5433)
echo     2. 🛑 Dừng toàn bộ hệ thống Docker
echo     3. 📜 Xem nhật ký hoạt động (Docker Logs realtime)
echo.
echo   [ NATIVE LOCAL DEV ]
echo     4. 💻 Bật hệ thống chế độ Dev Local (Python Uvicorn: 8000, Vite: 5173)
echo     5. ⛔ Dừng hệ thống chế độ Dev Local (Tắt port 8000 & 5173)
echo.
echo   [ CÔNG CỤ & HỆ THỐNG ]
echo     6. 🚀 Tự động Commit & Đẩy toàn bộ mã nguồn lên GitHub (Git Auto Push)
echo     7. ⚙️ Tải / Cập nhật mô hình AI Ollama (qwen2.5:3b & nomic-embed-text)
echo     8. 🔍 Kiểm tra trạng thái kết nối toàn bộ hệ thống (Health Check)
echo.
echo     0. ❌ Thoát (Exit)
echo ====================================================================================
set "CHOICE="
set /p "CHOICE=Nhập lựa chọn của bạn [0-8]: "

if "%CHOICE%"=="1" goto DOCKER_RUN
if "%CHOICE%"=="2" goto DOCKER_STOP
if "%CHOICE%"=="3" goto DOCKER_LOGS
if "%CHOICE%"=="4" goto LOCAL_RUN
if "%CHOICE%"=="5" goto LOCAL_STOP
if "%CHOICE%"=="6" goto GIT_PUSH
if "%CHOICE%"=="7" goto SETUP_MODELS
if "%CHOICE%"=="8" goto HEALTH_CHECK
if "%CHOICE%"=="0" goto EXIT_SCRIPT

echo.
echo [!] Lựa chọn không hợp lệ, vui lòng thử lại.
ping -n 2 127.0.0.1 >nul
goto MENU


:: ====================================================================================
:: 1. DOCKER RUN
:: ====================================================================================
:DOCKER_RUN
cls
echo =====================================================================
echo           KHOI DONG HE THONG ENTERPRISE LOCAL AI VOI DOCKER
echo =====================================================================
echo.

where docker >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Docker chua duoc cai dat hoac chua co trong PATH.
    echo Vui long cai dat Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    goto MENU
)

echo [*] Kiem tra ket noi Docker Desktop Engine...
docker info >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Docker Desktop chua bat, dang thu tu dong bat Docker Desktop...
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    )
    set "WAIT_COUNT=0"
    :WAIT_DOCKER_LOOP
    ping -n 3 127.0.0.1 >nul
    docker info >nul 2>&1
    if !errorlevel! equ 0 goto DOCKER_ENGINE_READY
    set /a WAIT_COUNT+=1
    if !WAIT_COUNT! geq 15 (
        echo [ERROR] Docker Desktop chua san sang. Vui long bat Docker Desktop thu cong!
        pause
        goto MENU
    )
    echo     ... Dang cho Docker Engine khoi tao (!WAIT_COUNT!/15)
    goto WAIT_DOCKER_LOOP
)

:DOCKER_ENGINE_READY
echo [OK] Docker Desktop Engine dang hoat dong tot!
echo.

:: Kiem tra Ollama port 11434
echo [*] Kiem tra dich vu Ollama AI (port 11434)...
netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Ollama dang hoat dong san sang.
) else (
    echo [!] Cong 11434 chua bat, dang tu dong khoi dong Ollama serve ngam...
    where ollama >nul 2>&1
    if !errorlevel! equ 0 (
        if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" (
            start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
        ) else (
            powershell -WindowStyle Hidden -Command "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
        )
        ping -n 4 127.0.0.1 >nul
    )
)
echo.

echo [*] Dang khoi dong cac containers Docker (Postgres, Backend, Frontend)...
docker compose up -d

if !errorlevel! equ 0 (
    echo.
    echo =====================================================================
    echo [THANH CONG] HE THONG DANG CHAY TREN DOCKER!
    echo =====================================================================
    echo   - Giao dien Web (Frontend)  : http://localhost:3000
    echo   - Tai lieu API (Swagger UI) : http://localhost:8000/docs
    echo   - Co so du lieu PostgreSQL  : localhost:5433
    echo.
    echo   Tai khoan thu nghiem:
    echo     * Super Admin : superadmin / Admin@123456
    echo     * IT Admin    : itadmin    / Admin@123456
    echo     * Employee    : employee   / Employee@123456
    echo =====================================================================
    echo [*] Dang mo trinh duyet den http://localhost:3000 ...
    start "" "http://localhost:3000"
) else (
    echo [ERROR] Khong the khoi dong Docker Compose!
)
echo.
pause
goto MENU


:: ====================================================================================
:: 2. DOCKER STOP
:: ====================================================================================
:DOCKER_STOP
cls
echo =====================================================================
echo                DUNG HE THONG DOCKER CONTAINERS
echo =====================================================================
echo.
echo [*] Dang dung tat ca cac containers Docker...
docker compose stop
echo.
echo [OK] Da dung tat ca containers Docker thanh cong. Du lieu van duoc luu an toan.
echo.
pause
goto MENU


:: ====================================================================================
:: 3. DOCKER LOGS
:: ====================================================================================
:DOCKER_LOGS
cls
echo =====================================================================
echo              NHAT KY HOAT DONG DOCKER (NHAN CTRL+C DE THOAT)
echo =====================================================================
echo.
docker compose logs -f
goto MENU


:: ====================================================================================
:: 4. LOCAL RUN (NATIVE DEV)
:: ====================================================================================
:LOCAL_RUN
cls
echo =====================================================================
echo           KHOI DONG HE THONG CHE DO DEV LOCAL (KHONG DOCKER)
echo =====================================================================
echo.

:: 1. Kiem tra Python Virtual Environment
set "PYTHON_VENV="
if exist "%ROOT_DIR%\.venv\Scripts\uvicorn.exe" (
    set "PYTHON_VENV=%ROOT_DIR%\.venv"
) else if exist "%ROOT_DIR%\backend\venv\Scripts\uvicorn.exe" (
    set "PYTHON_VENV=%ROOT_DIR%\backend\venv"
)

if "%PYTHON_VENV%"=="" (
    echo [ERROR] Khong tim thay Python Virtual Environment (.venv hoac backend\venv).
    pause
    goto MENU
)

:: 2. Kiem tra Ollama
netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !errorlevel! neq 0 (
    echo [*] Bat dich vu Ollama ngam...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" (
        start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
    ) else (
        powershell -WindowStyle Hidden -Command "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
    )
    ping -n 3 127.0.0.1 >nul
)

:: 3. Chay Backend tren cua so rieng
echo [*] Dang khoi dong Backend FastAPI tai cong 8000...
start "Enterprise Local AI - Backend" cmd /k "cd /d "%ROOT_DIR%\backend" && "%PYTHON_VENV%\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000 --reload"

ping -n 3 127.0.0.1 >nul

:: 4. Chay Frontend tren cua so rieng
echo [*] Dang khoi dong Frontend Vite tai cong 5173...
start "Enterprise Local AI - Frontend" cmd /k "cd /d "%ROOT_DIR%\frontend" && npm run dev"

ping -n 4 127.0.0.1 >nul

echo.
echo [OK] He thong Dev Local da khoi dong thanh cong!
echo   - Giao dien Web: http://localhost:5173
echo   - API Docs     : http://localhost:8000/docs
start "" "http://localhost:5173"
echo.
pause
goto MENU


:: ====================================================================================
:: 5. LOCAL STOP
:: ====================================================================================
:LOCAL_STOP
cls
echo =====================================================================
echo                DUNG HE THONG DEV LOCAL (PORTS 8000, 5173)
echo =====================================================================
echo.
echo [*] Dang dong cac tien trinh tren cong 8000 va 5173...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo [*] Tat Backend PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo [*] Tat Frontend PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [OK] Da dung tat ca dich vu Local Dev thanh cong!
echo.
pause
goto MENU


:: ====================================================================================
:: 6. GIT AUTO PUSH
:: ====================================================================================
:GIT_PUSH
cls
echo =====================================================================
echo                TU DONG DAY SOURCE CODE LEN GITHUB
echo =====================================================================
echo.

where git >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Git chua duoc cai dat hoac chua co trong PATH.
    pause
    goto MENU
)

set "BRANCH="
for /f "tokens=*" %%b in ('git branch --show-current 2^>nul') do set "BRANCH=%%b"
if "!BRANCH!"=="" set "BRANCH=main"

set "REMOTE_URL="
for /f "tokens=*" %%u in ('git config --get remote.origin.url 2^>nul') do set "REMOTE_URL=%%u"

echo [*] Nhanh lam viec : !BRANCH!
echo [*] Remote GitHub  : !REMOTE_URL!
echo.

echo ---------------------------------------------------------------------
echo [*] Danh sach tep thay doi:
echo ---------------------------------------------------------------------
git status --short
echo ---------------------------------------------------------------------
echo.

echo [?] Nhap thong diep commit (Nhan Enter de lay mac dinh theo ngay gio):
set "USER_MSG="
set /p "USER_MSG=> "

if "!USER_MSG!"=="" (
    set "CLEAN_TIME=%TIME: =0%"
    for /f "tokens=1 delims=.," %%t in ("!CLEAN_TIME!") do set "CLEAN_TIME=%%t"
    set "COMMIT_MSG=feat(src): auto sync code on %DATE% !CLEAN_TIME!"
) else (
    set "COMMIT_MSG=!USER_MSG!"
)

echo.
echo [*] Commit Message: "!COMMIT_MSG!"
echo [*] Dang dua tep vao staging (git add -A)...
git add -A

echo [*] Dang tao commit...
git commit -m "!COMMIT_MSG!" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Da tao commit thanh cong.
) else (
    echo [INFO] Working tree da sach hoac khong co thay doi moi.
)

echo.
echo [*] Dong bo tu remote (git pull --rebase)...
git pull origin !BRANCH! --rebase
if !errorlevel! neq 0 (
    echo [WARN] Rebase gap canh bao. Dang huy rebase de giu an toan code...
    git rebase --abort >nul 2>&1
)

echo.
echo [*] Dang day len GitHub (git push origin !BRANCH!)...
git push -u origin !BRANCH!

if !errorlevel! equ 0 (
    echo.
    echo =====================================================================
    echo [THANH CONG] DA DAY TOAN BO SOURCE CODE LEN GITHUB!
    echo =====================================================================
    for /f "tokens=*" %%h in ('git rev-parse --short HEAD 2^>nul') do echo [*] Commit Hash : %%h
    echo [*] Nhanh       : !BRANCH!
    echo =====================================================================
) else (
    echo.
    echo =====================================================================
    echo [THAT BAI] KHONG THE DAY CODE LEN GITHUB!
    echo Goi y: Kiem tra ket noi mang Internet hoac bat VPN neu nha mang chan port 443.
    echo =====================================================================
)
echo.
pause
goto MENU


:: ====================================================================================
:: 7. SETUP OLLAMA MODELS
:: ====================================================================================
:SETUP_MODELS
cls
echo =====================================================================
echo           TAI VA CAI DAT MO HINH AI OLLAMA (QWEN2.5 & EMBED)
echo =====================================================================
echo.

where ollama >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Khong tim thay Ollama tren he thong!
    echo Vui long cai dat Ollama tai https://ollama.com truoc.
    pause
    goto MENU
)

netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if !errorlevel! neq 0 (
    echo [*] Dang bat dich vu Ollama ngam...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" (
        start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
    ) else (
        powershell -WindowStyle Hidden -Command "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
    )
    ping -n 4 127.0.0.1 >nul
)

echo.
echo [1/2] Dang tai / cap nhat mo hinh LLM chinh (qwen2.5:3b - ~1.9GB)...
ollama pull qwen2.5:3b

echo.
echo [2/2] Dang tai / cap nhat mo hinh Embedding (nomic-embed-text - ~274MB)...
ollama pull nomic-embed-text

echo.
echo =====================================================================
echo [OK] CAC MO HINH AI DA SAN SANG!
echo =====================================================================
ollama list
echo =====================================================================
echo.
pause
goto MENU


:: ====================================================================================
:: 8. HEALTH CHECK
:: ====================================================================================
:HEALTH_CHECK
cls
echo =====================================================================
echo              KIEM TRA TRANG THAI TOAN BO HE THONG
echo =====================================================================
echo.

echo --- 1. Trang thai Docker Containers ---
where docker >nul 2>&1
if !errorlevel! equ 0 (
    docker compose ps
) else (
    echo [!] Docker chua duoc cai dat.
)
echo.

echo --- 2. Trang thai Cong mang (Listening Ports) ---
for %%p in (3000 5173 5432 5433 8000 11434) do (
    netstat -ano | findstr ":%%p" | findstr "LISTENING" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OPEN] Cong %%p dang hoat dong ^(LISTENING^)
    ) else (
        echo   [----] Cong %%p dang dong
    )
)
echo.

echo --- 3. Trang thai Ollama AI Models ---
where ollama >nul 2>&1
if !errorlevel! equ 0 (
    ollama list
) else (
    echo [!] Ollama chua cai dat.
)
echo.

echo --- 4. Trang thai Git Repository ---
where git >nul 2>&1
if !errorlevel! equ 0 (
    git status --short
)
echo.
echo =====================================================================
pause
goto MENU


:: ====================================================================================
:: 0. EXIT
:: ====================================================================================
:EXIT_SCRIPT
cls
echo Cam on ban da su dung Enterprise Local AI Control Center!
ping -n 2 127.0.0.1 >nul
exit /b 0
