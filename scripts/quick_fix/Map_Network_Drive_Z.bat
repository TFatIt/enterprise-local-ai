@echo off
chcp 65001 >nul
title CÔNG CỤ TỰ ĐỘNG KẾT NỐI Ổ ĐĨA MẠNG NỘI BỘ (Ổ Z:)
cls
echo ====================================================================
echo      HỆ THỐNG IT SUPPORT DOANH NGHIỆP - KẾT NỐI Ổ ĐĨA DÙNG CHUNG
echo ====================================================================
echo.
set SERVER_IP=192.168.1.10
set SHARE_FOLDER=DULIEU_CONGTY

echo [1/3] Đang kiểm tra kết nối mạng tới máy chủ file (%SERVER_IP%)...
ping -n 1 %SERVER_IP% >nul 2>&1
if %errorLevel% neq 0 (
    echo [CẢNH BÁO] Không thể kết nối tới IP %SERVER_IP%.
    echo Vui lòng đảm bảo máy tính đã cắm dây mạng LAN hoặc kết nối đúng Wifi công ty!
    echo.
    pause
    exit /b 1
)

echo [2/3] Đang ngắt kết nối ổ Z cũ (nếu có)...
net use Z: /delete /y >nul 2>&1

echo [3/3] Đang kết nối ổ Z vào \\%SERVER_IP%\%SHARE_FOLDER%...
net use Z: \\%SERVER_IP%\%SHARE_FOLDER% /persistent:yes

if %errorLevel% equ 0 (
    echo.
    echo ====================================================================
    echo [THÀNH CÔNG] Đã kết nối thành công Ổ đĩa mạng Z: vào máy tính của bạn!
    echo Bạn có thể vào "This PC" và mở ổ Z: để truy cập dữ liệu công ty.
    echo ====================================================================
    explorer.exe Z:
) else (
    echo.
    echo [LỖI] Kết nối thất bại. Vui lòng kiểm tra quyền truy cập hoặc liên hệ IT Support.
)

echo.
pause
