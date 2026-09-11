@echo off
chcp 65001 >nul
title CÔNG CỤ TỰ ĐỘNG SỬA LỖI MÁY IN KẸT LỆNH IN & KHỞI ĐỘNG PRINT SPOOLER
cls
echo ====================================================================
echo      HỆ THỐNG IT SUPPORT DOANH NGHIỆP - TỰ ĐỘNG SỬA LỖI MÁY IN
echo ====================================================================
echo.
echo Đang kiểm tra quyền Quản trị viên (Administrator)...

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [LỖI] Vui lòng chuột phải vào file này và chọn "Run as administrator"!
    echo.
    pause
    exit /b 1
)

echo [1/3] Đang dừng dịch vụ Print Spooler...
net stop spooler >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] Đang dọn sạch toàn bộ các lệnh in bị kẹt trong hàng đợi...
del /Q /F /S "%systemroot%\System32\spool\PRINTERS\*.*" >nul 2>&1

echo [3/3] Đang khởi động lại dịch vụ Print Spooler...
net start spooler >nul 2>&1

echo.
echo ====================================================================
echo [THÀNH CÔNG] Đã giải phóng toàn bộ lệnh in bị kẹt!
echo Dịch vụ Print Spooler đã hoạt động bình thường trở lại.
echo Bạn có thể gửi lại lệnh in mới ngay bây giờ.
echo ====================================================================
echo.
pause
