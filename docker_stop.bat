@echo off
setlocal enabledelayedexpansion
title Enterprise Local AI - Docker Stop
cls

echo =====================================================================
echo           ENTERPRISE LOCAL AI ASSISTANT - DOCKER STOP
echo =====================================================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"

echo [*] Dang dung tat ca Docker containers...
docker compose stop

echo.
echo [OK] Da dung tat ca dich vu Docker thanh cong!
echo (Cac du lieu trong database va volumes van duoc luu tru an toan).
echo.
pause
