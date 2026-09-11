@echo off
chcp 65001 >nul 2>&1
title Auto Document Watcher - Local AI Nội bộ doanh nghiệp

echo ============================================================
echo   🤖 AUTO DOCUMENT WATCHER
echo   Local AI Nội bộ doanh nghiệp
echo ============================================================
echo.
echo   Hệ thống sẽ tự động giám sát thư mục:
echo   auto_import_documents\
echo.
echo   Khi bạn thả file vào thư mục đó, AI sẽ:
echo   - Đọc toàn bộ nội dung văn bản (PDF, DOCX, TXT, Excel...)
echo   - Phân tích hình ảnh bằng Vision AI (PNG, JPG...)
echo   - Trích xuất kiến thức từ video (MP4, MKV...)
echo   - Lưu vào kho tri thức ChromaDB
echo.
echo   Nhấn Ctrl+C để dừng.
echo ============================================================
echo.

cd /d "%~dp0"

:: Check if Python venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Không tìm thấy Python virtual environment!
    echo        Vui lòng chạy: python -m venv .venv
    pause
    exit /b 1
)

:: Check if Ollama is running
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [CẢNH BÁO] Ollama chưa khởi động. Đang thử khởi động...
    start /b ollama serve
    timeout /t 3 /nobreak >nul
)

:: Create auto_import_documents directory if not exists
if not exist "auto_import_documents" (
    mkdir "auto_import_documents"
    mkdir "auto_import_documents\docs"
    mkdir "auto_import_documents\images"
    mkdir "auto_import_documents\videos"
)

:: Run the watcher
echo [INFO] Đang khởi chạy Auto Document Watcher...
echo.
.venv\Scripts\python.exe scripts\auto_document_watcher.py --interval 15

echo.
echo [INFO] Auto Document Watcher đã dừng.
pause
