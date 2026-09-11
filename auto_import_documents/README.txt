============================================================
   HƯỚNG DẪN SỬ DỤNG THƯ MỤC TỰ ĐỘNG NẠP TÀI LIỆU
   Local AI Nội bộ doanh nghiệp
============================================================

1. CÁCH SỬ DỤNG:
   - Kéo/thả hoặc copy bất kỳ tài liệu nào vào thư mục này
   - AI sẽ TỰ ĐỘNG phát hiện và đọc toàn bộ nội dung
   - Kiến thức được lưu vào ChromaDB để AI trả lời khi được hỏi

2. CÁC ĐỊNH DẠNG HỖ TRỢ:

   📄 TÀI LIỆU VĂN BẢN:
   .pdf  .docx  .txt  .md  .csv  .xlsx
   .bat  .ps1   .sh   .sql .json .log .ini .yaml

   🖼️ HÌNH ẢNH (đọc chữ & phân tích nội dung):
   .png  .jpg  .jpeg  .webp  .bmp  .gif  .tiff

   🎬 VIDEO (trích xuất phụ đề & keyframe):
   .mp4  .mkv  .avi  .mov  .webm

3. TỔ CHỨC THƯ MỤC CON (tùy chọn):
   auto_import_documents/
   ├── docs/      ← Tài liệu văn bản
   ├── images/    ← Hình ảnh, screenshot, sơ đồ
   └── videos/    ← Video hướng dẫn, training

   Hoặc đặt trực tiếp vào thư mục gốc, AI sẽ tự nhận diện.

4. CÁCH KHỞI CHẠY WATCHER:
   - Chạy file: chay_tu_dong_hoc_tai_lieu.bat
   - Hoặc lệnh: python scripts/auto_document_watcher.py

5. LƯU Ý:
   - File đã nạp thành công sẽ KHÔNG bị xử lý lại (trừ khi nội dung thay đổi)
   - Các file tạm (.tmp, ~$..., .crdownload) sẽ bị bỏ qua
   - Dung lượng tối đa mỗi file: 100MB
   - Yêu cầu Ollama đang chạy (nomic-embed-text + qwen2.5:3b)
   - Để đọc ảnh, cần pull thêm model vision: ollama pull minicpm-v

============================================================
