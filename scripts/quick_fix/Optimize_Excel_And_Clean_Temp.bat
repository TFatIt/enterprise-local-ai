@echo off
chcp 65001 >nul
title CÔNG CỤ DỌN DẸP CACHE OFFICE & TỐI ƯU HÓA TỐC ĐỘ EXCEL
cls
echo ====================================================================
echo      HỆ THỐNG IT SUPPORT DOANH NGHIỆP - DỌN RÁC & TỐI ƯU HÓA EXCEL
echo ====================================================================
echo.
echo Vui lòng lưu và đóng toàn bộ các file Excel, Word, Outlook trước khi chạy.
echo.
pause

echo.
echo [1/3] Đang dọn dẹp các tệp tin tạm (Temp files) của hệ điều hành...
del /s /f /q "%TEMP%\*.*" >nul 2>&1
for /d %%p in ("%TEMP%\*.*") do rmdir "%%p" /s /q >nul 2>&1

echo [2/3] Đang dọn dẹp bộ nhớ đệm Office File Cache...
if exist "%LOCALAPPDATA%\Microsoft\Office\16.0\OfficeFileCache" (
    del /s /f /q "%LOCALAPPDATA%\Microsoft\Office\16.0\OfficeFileCache\*.*" >nul 2>&1
)

echo [3/3] Đang dọn dẹp bộ đệm tạm của Excel (AutoRecover & XLSTART temp)...
if exist "%APPDATA%\Microsoft\Excel" (
    del /s /f /q "%APPDATA%\Microsoft\Excel\*.tmp" >nul 2>&1
    del /s /f /q "%APPDATA%\Microsoft\Excel\*.xar" >nul 2>&1
)

echo.
echo ====================================================================
echo [THÀNH CÔNG] Đã dọn dẹp toàn bộ bộ đệm rác của Excel và Office!
echo Máy tính của bạn đã được giải phóng bộ nhớ RAM và ổ cứng.
echo Bạn có thể mở lại Excel và tiếp tục làm việc mượt mà.
echo ====================================================================
echo.
pause
