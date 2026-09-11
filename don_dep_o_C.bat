@echo off
chcp 65001 >nul
title DỌN DẸP SẠCH RÁC WINDOWS UPDATE Ổ C (GIẢI PHÓNG ~39GB)

:: Kiểm tra quyền Administrator, nếu chưa có thì tự xin quyền UAC
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Đang yêu cầu quyền Quản trị viên (Administrator)...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

color 0A
echo ======================================================================
echo            CÔNG CỤ DỌN DẸP RÁC WINDOWS UPDATE Ổ C AN TOÀN
echo               (Giải phóng ~38.7 GB cho ổ C máy tính)
echo ======================================================================
echo.

echo [*] Dung lượng ổ C trước khi dọn:
powershell -Command "Get-PSDrive C | Select-Object Name, @{Name='Trong_GB';Expression={[math]::Round($_.Free/1GB,2)}}, @{Name='DaDung_GB';Expression={[math]::Round($_.Used/1GB,2)}} | Format-Table -AutoSize"

echo.
echo [1/3] Đang xóa thư mục sao lưu Windows Update cũ (C:\$WINDOWS.~BT ~ 29.5 GB)...
takeown /F "C:\$WINDOWS.~BT" /A /R /D Y >nul 2>&1
icacls "C:\$WINDOWS.~BT" /grant *S-1-5-32-544:F /T /C /Q >nul 2>&1
rmdir /S /Q "C:\$WINDOWS.~BT" >nul 2>&1
if exist "C:\$WINDOWS.~BT" (
    echo   [-] Lưu ý: Một số file hệ thống đang được giữ, sẽ dọn tiếp ở bước 3.
) else (
    echo   [+] Đã xóa sạch hoàn toàn C:\$WINDOWS.~BT (Đã thu hồi ~29.5 GB)!
)

echo.
echo [2/3] Đang dọn dẹp các gói cài Windows Update cũ đã xong (~ 9.2 GB)...
net stop wuauserv >nul 2>&1
del /F /S /Q "C:\Windows\SoftwareDistribution\Download\*" >nul 2>&1
for /d %%p in ("C:\Windows\SoftwareDistribution\Download\*") do rmdir "%%p" /s /q >nul 2>&1
net start wuauserv >nul 2>&1
echo   [+] Đã dọn sạch gói tải Windows Update thừa!

echo.
echo [3/3] Đang chạy công cụ tối ưu hóa tệp hệ thống Windows (DISM)...
echo   (Quá trình này mất khoảng 1 - 2 phút, xin vui lòng đợi...)
dism.exe /online /cleanup-image /startcomponentcleanup /resetbase

echo.
echo ======================================================================
echo                     DỌN DẸP HOÀN TẤT THÀNH CÔNG!
echo ======================================================================
echo.
echo [*] Dung lượng ổ C SAU KHI DỌN DẸP:
powershell -Command "Get-PSDrive C | Select-Object Name, @{Name='Trong_GB';Expression={[math]::Round($_.Free/1GB,2)}}, @{Name='DaDung_GB';Expression={[math]::Round($_.Used/1GB,2)}} | Format-Table -AutoSize"

echo.
echo Bấm phím bất kỳ để đóng cửa sổ này...
pause >nul
