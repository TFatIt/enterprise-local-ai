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
if !errorlevel! neq 0 (
    echo [ERROR] Git chua duoc cai dat hoac chua co trong PATH.
    echo Vui long cai dat Git: https://git-scm.com/
    echo.
    if not "%~2"=="--no-pause" pause
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

:: 6. Dua tat ca tep vao staging va commit
echo [*] Dang chuan bi tep (git add -A)...
git add -A

echo [*] Kiem tra va commit ma nguon...
git commit -m "!COMMIT_MSG!" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Da tao commit thanh cong.
) else (
    echo [INFO] Working tree da sach hoac khong co thay doi moi.
)

:: 7. Dong bo rebase tu Remote truoc khi day
echo.
echo [*] Kiem tra va dong bo tu GitHub (git pull --rebase)...
git pull origin !BRANCH! --rebase
if !errorlevel! neq 0 (
    echo [WARN] Rebase gap canh bao. Hoan tac rebase de bao ve code local...
    git rebase --abort >nul 2>&1
)

:: 8. Day code len GitHub
echo.
echo =====================================================================
echo [*] Dang day source code len GitHub (origin/!BRANCH!)...
echo =====================================================================
git push -u origin !BRANCH!

if !errorlevel! equ 0 (
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
    echo - Kiem tra ket noi mang Internet hoac bat VPN neu nha mang chan port 443.
    echo - Kiem tra quyen truy cap repository tren GitHub.
    echo - Chay 'git status' de xem chi tiet.
    echo =====================================================================
)

echo.
if not "%~2"=="--no-pause" pause
