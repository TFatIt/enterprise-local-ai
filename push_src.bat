@echo off
setlocal enabledelayedexpansion
title Auto Push Source Code to GitHub
cls

echo =====================================================================
echo          TU DONG DAY TOAN BO SOURCE CODE (SRC) LEN GITHUB
echo =====================================================================
echo.

:: Di chuyen ve thu muc goc cua du an
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"

:: 1. Kiem tra Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git chua duoc cai dat hoac chua co trong PATH.
    echo Vui long cai dat Git: https://git-scm.com/
    echo.
    pause
    exit /b 1
)

:: 2. Nhan dien Nhanh hien tai
set "BRANCH="
for /f "tokens=*" %%b in ('git branch --show-current 2^>nul') do set "BRANCH=%%b"
if "!BRANCH!"=="" set "BRANCH=main"

:: 3. Nhan dien Remote URL
set "REMOTE_URL="
for /f "tokens=*" %%u in ('git config --get remote.origin.url 2^>nul') do set "REMOTE_URL=%%u"
if "!REMOTE_URL!"=="" (
    for /f "tokens=*" %%u in ('git remote get-url origin 2^>nul') do set "REMOTE_URL=%%u"
)

echo [*] Thu muc du an : !ROOT_DIR!
echo [*] Nhanh lam viec: !BRANCH!
echo [*] Remote GitHub : !REMOTE_URL!
echo.

:: 4. Xac dinh thong diep commit
set "COMMIT_MSG=%~1"
if "!COMMIT_MSG!"=="" (
    set "CLEAN_TIME=%TIME: =0%"
    for /f "tokens=1 delims=.," %%t in ("!CLEAN_TIME!") do set "CLEAN_TIME=%%t"
    set "COMMIT_MSG=feat(src): auto sync code on %DATE% !CLEAN_TIME!"
)

echo [*] Commit Message: "!COMMIT_MSG!"
echo.

:: 5. Danh sach file thay doi
echo ---------------------------------------------------------------------
echo [*] Danh sach tep thay doi:
echo ---------------------------------------------------------------------
git status --short
echo ---------------------------------------------------------------------
echo.

:: 6. Dua tat ca tep vao staging
echo [*] Dang chuan bi tep (git add -A)...
git add -A
if %errorlevel% neq 0 (
    echo [ERROR] Thao tac git add that bai!
    pause
    exit /b 1
)

:: 7. Tao commit
git diff --cached --quiet
if %errorlevel% neq 0 (
    echo [*] Dang tao commit moi...
    git commit -m "!COMMIT_MSG!"
    if %errorlevel% neq 0 (
        echo [ERROR] Khong the tao commit!
        pause
        exit /b 1
    )
    echo [OK] Da tao commit thanh cong.
) else (
    echo [INFO] Khong co tep ma nguon moi can commit.
)

:: 8. Dong bo rebase tu Remote truoc khi day
echo.
echo [*] Kiem tra va keo cap nhat moi tu GitHub (git pull --rebase)...
git pull origin !BRANCH! --rebase
if %errorlevel% neq 0 (
    echo [WARN] Rebase gap canh bao hoac xung dot. Hoan tac rebase de bao ve code local...
    git rebase --abort >nul 2>&1
)

:: 9. Day code len GitHub
echo.
echo =====================================================================
echo [*] Dang day source code len GitHub (origin/!BRANCH!)...
echo =====================================================================
git push -u origin !BRANCH!

if %errorlevel% equ 0 (
    echo.
    echo =====================================================================
    echo [THANH CONG] DA DAY TOAN BO SOURCE CODE LEN GITHUB THANH CONG!
    echo =====================================================================
    for /f "tokens=*" %%h in ('git rev-parse --short HEAD 2^>nul') do echo [*] Commit Hash : %%h
    echo [*] Nhanh       : !BRANCH!
    echo [*] Kho luu tru : !REMOTE_URL!
    echo =====================================================================
) else (
    echo.
    echo =====================================================================
    echo [THAT BAI] KHONG THE DAY CODE LEN GITHUB!
    echo =====================================================================
    echo Goi y kiem tra:
    echo 1. Kiem tra ket noi mang Internet.
    echo 2. Kiem tra quyen truy cap repository tren GitHub (Personal Access Token / SSH).
    echo 3. Kiem tra 'git status' de xem chi tiet.
    echo =====================================================================
)

echo.
if "%~2"=="--no-pause" goto end
pause
:end
