# HỆ THỐNG CƠ SỞ TRI THỨC CNTT DOANH NGHIỆP (ENTERPRISE IT KNOWLEDGE BASE)
# CHUYÊN ĐỀ: BIOS/BOOT/PHẦN CỨNG & HẠ TẦNG CÔNG NGHỆ LOCAL AI / RAG SYSTEM

---

## Document ID
`KB-SYS-2026-001`

## Category
`Hardware & BIOS / Local AI & RAG Architecture / Enterprise Infrastructure`

## Department
`IT`

## Title
Hướng dẫn Cấu hình Chuẩn UEFI/TPM 2.0/NVMe và Vận hành Hạ tầng Trợ lý AI Cục bộ (Local AI / Ollama / ChromaDB / RAG Pipeline)

## Problem
1. **Phần cứng & Khởi động**: Máy tính không nhận ổ cứng NVMe SSD sau khi cài đặt lại, báo lỗi *"No Bootable Device Found"*, hoặc Windows 11 yêu cầu TPM 2.0 và Secure Boot; màn hình khóa BitLocker Recovery đòi khóa khôi phục 48 chữ số.
2. **Hạ tầng Local AI & RAG**: Dịch vụ Local AI (Ollama) bị mất kết nối (`Connection Refused`), mô hình ngôn ngữ lớn (Qwen 2.5 3B) ngốn sạch VRAM GPU hoặc tràn RAM hệ thống, ChromaDB báo lỗi không tìm thấy vector index hoặc phản hồi của AI bị ảo giác do phân mảnh chunk sai quy cách.

## Symptoms
* **Hardware/Boot**:
  - Máy trạm Dell/Lenovo khởi động lên màn hình đen báo *"Default Boot Device Missing or Boot Failed"*.
  - Khởi động vào Windows xuất hiện màn hình xanh BitLocker: *"Enter the recovery key for this drive"*.
  - Bộ cài Windows 11 không cho cài đặt: *"This PC doesn't meet the minimum system requirements (TPM 2.0 / Secure Boot)"*.
* **Local AI / RAG**:
  - Backend FastAPI báo log: `httpx.ConnectError: [Errno 111] Connection refused: http://127.0.0.1:11434`.
  - Ollama báo lỗi `CUDA out of memory` hoặc rơi vào trạng thái chạy CPU cực chậm (> 25 giây cho một câu trả lời).
  - Kết quả tìm kiếm RAG trả về các đoạn trích dẫn không liên quan đến câu hỏi kỹ thuật của nhân viên.

## Error Message
* Boot Screen: `"No bootable device -- insert boot disk and press any key"`
* Windows 11 Setup: `"Windows cannot be installed to this disk. The selected disk has an MBR partition table."`
* Backend Python Log:
  `"ollama._types.ResponseError: model 'qwen2.5:3b' not found, try pulling it first"`
  `"chromadb.errors.InvalidDimensionException: Embedding dimension 1536 does not match collection dimension 768"`

## Environment
* **Phần cứng Endpoint**: Laptop / Desktop doanh nghiệp (Dell OptiPlex, Latitude, ThinkPad, HP ProBook) hỗ trợ UEFI, TPM 2.0.
* **Môi trường AI Máy chủ/Máy trạm Local**:
  - CPU: AMD Ryzen 7 / Intel Core i7 (8 cores/16 threads trở lên).
  - RAM: 16GB - 32GB DDR4/DDR5.
  - GPU: NVIDIA GeForce GTX 1650 Ti / RTX 3060 trở lên (VRAM $\ge 4\text{GB}$).
  - LLM Runtime: Ollama chạy mô hình `qwen2.5:3b` (sinh chữ) và `nomic-embed-text` (vector embedding 768 chiều).
  - Vector Database: ChromaDB cục bộ (`./chroma_data`).
  - Reranker: FlashRank ONNX Runtime (`ms-marco-TinyBERT-L-2-v2`).

---

## Possible Causes

### Nhóm 1: Sự cố BIOS / Boot / Hardware
1. **Sai lệch chế độ Boot (UEFI vs Legacy CSM)**: Ổ đĩa định dạng chuẩn GPT nhưng BIOS lại thiết lập ở chế độ Legacy Boot (hoặc ngược lại định dạng MBR trên hệ thống UEFI thuần).
2. **Chế độ điều khiển lưu trữ VMD / Intel RST**: Các dòng máy tính Intel Gen 11+ bật mặc định tính năng Intel Volume Management Device (VMD/RST), bộ cài Windows thiếu driver `iaStorVD.sys` khiến không nhận thấy ổ cứng SSD.
3. **Thay đổi phần cứng kích hoạt BitLocker**: Cập nhật firmware BIOS, thay đổi thứ tự cắm ổ cứng hoặc tắt/bật Secure Boot làm sai lệch chữ ký PCR (Platform Configuration Register) của chip TPM 2.0 khiến BitLocker khóa ổ đĩa để bảo vệ an toàn dữ liệu.

### Nhóm 2: Sự cố Local AI & RAG Engine
1. **Dịch vụ Ollama Daemon chưa khởi chạy**: Tiến trình `ollama app` hoặc `ollama serve` chưa được kích hoạt ở chế độ nền trên cổng 11434.
2. **Lệch số chiều Vector (Dimension Mismatch)**: Nạp tài liệu bằng mô hình embedding kích thước 1536 chiều (như text-embedding-ada-002) vào collection ChromaDB được khởi tạo với chuẩn 768 chiều (`nomic-embed-text`).
3. **Tràn bộ nhớ VRAM GPU (VRAM Exhaustion)**: Khởi chạy mô hình 7B/14B quá nặng trên card đồ họa 4GB VRAM khiến hệ thống hoán đổi trang nhớ sang RAM hệ thống làm sụt giảm tốc độ suy luận nghiêm trọng.
4. **Phân đoạn văn bản (Chunking) sai tỷ lệ**: Chunk size quá nhỏ (< 200 ký tự) làm mất ngữ cảnh; hoặc chunk size quá lớn (> 2000 ký tự) chứa quá nhiều thông tin gây nhiễu cho Cross-Encoder Reranker.

---

## Diagnosis (Quy trình chẩn đoán chuẩn)

### Bước 1: Chẩn đoán BIOS / Phân vùng ổ đĩa
1. Khởi động máy, nhấn `F2` hoặc `F12` vào BIOS Setup.
2. Kiểm tra:
   - **Boot Mode**: Đảm bảo là `UEFI Only` (Tắt Legacy Option ROMs / CSM).
   - **Secure Boot**: Đảm bảo trạng thái `Enabled`.
   - **Security** -> **TPM 2.0 Security**: Trạng thái `On`, `Enabled`, và `PPI Bypass` được kích hoạt.
3. Trong màn hình cài đặt Windows (hoặc WinRE), nhấn `Shift + F10` mở Command Prompt:
   ```cmd
   diskpart
   list disk
   ```
   *Quan sát cột `Gpt`: Nếu ổ đĩa có dấu sao `*` ➔ Đã đúng chuẩn GPT. Nếu trống ➔ Ổ đĩa đang là MBR, bắt buộc phải chuyển đổi sang GPT!*

### Bước 2: Chẩn đoán Dịch vụ Local AI (Ollama)
Mở PowerShell tại máy chủ AI:
```powershell
# 1. Kiểm tra tiến trình Ollama
Get-Process -Name ollama -ErrorAction SilentlyContinue

# 2. Kiểm tra cổng lắng nghe 11434
Test-NetConnection -ComputerName 127.0.0.1 -Port 11434

# 3. Liệt kê các model đã tải về cục bộ
ollama list
```

### Bước 3: Kiểm tra mức tiêu thụ GPU VRAM và suy luận
```powershell
# Đối với card đồ họa NVIDIA:
nvidia-smi
```
*Quan sát mục Memory-Usage: Đảm bảo mô hình Qwen 2.5 3B chiếm ~2.1GB - 2.8GB VRAM trên tổng số 4GB VRAM, mức sử dụng GPU duy trì dưới 85%.*

---

## Solution (Quy trình khắc phục chuyên sâu)

### Phần 1: Khắc phục Sự cố BIOS & Không nhận SSD NVMe

#### Bước 1: Tắt Intel VMD Controller trong BIOS khi cài Windows
1. Vào BIOS Setup (nhấn `F2` hoặc `Del`).
2. Tìm mục **System Configuration** -> **Storage** -> **VMD Setup Menu**:
   - Chuyển `Enable VMD Controller` sang **Disabled**.
3. Lưu lại (`F10`) và khởi động lại. Bộ cài Windows sẽ nhận diện ngay lập tức ổ SSD NVMe tốc độ cao mà không cần nạp driver bên ngoài.

#### Bước 2: Chuyển đổi ổ cứng từ MBR sang GPT không mất dữ liệu (MBR2GPT)
Từ WinRE Command Prompt (hoặc Windows PE):
```cmd
:: 1. Kiểm tra tính hợp lệ trước khi chuyển đổi
mbr2gpt /validate /disk:0 /allowFullOS

:: 2. Thực hiện chuyển đổi sang GPT cho UEFI Boot
mbr2gpt /convert /disk:0 /allowFullOS
```

#### Bước 3: Sửa lỗi phân vùng khởi động BCD của chuẩn UEFI
Nếu máy báo thiếu Boot Manager:
```cmd
diskpart
select disk 0
list partition
:: Tìm phân vùng EFI System (định dạng FAT32, dung lượng ~100MB-500MB), giả sử là phân vùng 2:
select partition 2
assign letter=S
exit

:: Tạo lại cấu hình khởi động BCD cho phân vùng EFI:
bcdboot C:\Windows /s S: /f UEFI
```

---

### Phần 2: Khắc phục & Tối ưu Hạ tầng Local AI & RAG

#### Bước 1: Khởi chạy và cố định dịch vụ Ollama Local Daemon
1. Khởi động Ollama ở chế độ nền (Background Service):
   ```powershell
   ollama serve
   ```
2. Đảm bảo 2 mô hình cốt lõi của hệ thống đã sẵn sàng trong cache:
   ```powershell
   ollama pull qwen2.5:3b
   ollama pull nomic-embed-text
   ```

#### Bước 2: Chuẩn hóa Thông số Chunking & Vector Dimension
Tuân thủ cấu hình chuẩn hóa của hệ thống tại [`backend/app/rag/chunker.py`](file:///d:/Maytinh-data/Downloads/AI/backend/app/rag/chunker.py):
* **Chunk Size**: `700` ký tự (tương đương khoảng 140-180 tokens, vừa vặn một đoạn văn quy trình hoàn chỉnh).
* **Chunk Overlap**: `120` ký tự (duy trì tính mạch lạc giữa các câu liên tiếp).
* **Vector Dimension**: Cố định **768 chiều** (chuẩn toán học của `nomic-embed-text`).

#### Bước 3: Quy trình Two-Tier Grounding RAG chống Ảo giác (Zero Hallucination)
1. **Tầng 1 (Vector Gate)**: Lọc các đoạn trích xuất có điểm tương đồng Cosine $\ge 0.42$. Nếu không có chunk nào vượt ngưỡng ➔ Lập tức trả về câu từ chối an toàn và kích hoạt nút Tạo IT Ticket.
2. **Tầng 1.5 (Local Reranker)**: Sử dụng `FlashRank` (`ms-marco-TinyBERT-L-2-v2`) tính toán tương quan ngữ nghĩa sâu trên CPU (15-25ms), chọn lọc Top-3 hoặc Top-5 chunks chính xác nhất.
3. **Tầng 2 (LLM Truthfulness Gate)**: Bắt buộc mô hình sinh chữ theo System Prompt nghiêm ngặt: *"Chỉ trả lời dựa trên CONTEXT được cung cấp. Tuyệt đối không tự bịa đặt thông tin ngoài tài liệu."* Nếu LLM phát hiện câu hỏi ngoài phạm vi, tự động trả về câu từ chối và đề xuất hỗ trợ từ IT Helpdesk.

---

## Verification (Xác nhận kết quả)
1. **Kiểm tra Boot**: Máy tính khởi động thẳng vào Windows 11 trong vòng 8-12 giây qua chuẩn UEFI NVMe SSD, TPM 2.0 hiển thị trạng thái `Ready for use` trong `tpm.msc`.
2. **Kiểm tra RAG Benchmark Suite**:
   Chạy lệnh kiểm thử tự động toàn diện:
   ```powershell
   pytest tests/test_rag_benchmark.py -v
   ```
   ➔ Kết quả đạt **5/5 PASSED (100%)**, thời gian phản hồi câu hỏi kỹ thuật từ 1.2s - 1.8s, trích xuất chính xác nguồn tài liệu và từ chối 100% câu hỏi ngoài phạm vi.

## Prevention (Biện pháp phòng ngừa)
1. **Sao lưu khóa khôi phục BitLocker (BitLocker Recovery Key)**: Tự động sao lưu khóa 48 ký tự của mọi máy trạm lên Active Directory thông qua Group Policy (`Store BitLocker recovery information in Active Directory Domain Services`).
2. Khóa mật khẩu BIOS (Admin Password) trên toàn bộ máy trạm doanh nghiệp để ngăn nhân viên tự ý đổi chế độ SATA từ AHCI sang RAID hoặc tắt Secure Boot.
3. Định kỳ sao lưu thư mục Vector Store ChromaDB (`./chroma_data`) và cơ sở dữ liệu PostgreSQL.

## Escalation
* Chuyển cấp **Level 3 (Data Science / AI Engineer)** nếu: Ollama gặp lỗi tràn bộ nhớ ngữ cảnh (Context Window Overflow) khi nạp tài liệu bảng tính vượt quá 8,192 tokens hoặc cần tinh chỉnh (Fine-tune) mô hình ngôn ngữ chuyên sâu cho thuật ngữ nội bộ.

## Risk Level
`High` (Liên quan trực tiếp đến khả năng khởi động của thiết bị phần cứng và tính sẵn sàng của trợ lý AI toàn doanh nghiệp)

## Required Permission
* BIOS/Hardware: `Local Administrator / Physical Access / BIOS Admin Password`
* Local AI: `System Administrator / Root Access trên AI Server`

## Related Documents
* `KB-WIN-2026-001`: Quy trình Khắc phục Tổn hại Hệ thống Windows và Xử lý Lỗi Màn hình Xanh (BSOD).
* `KB-NET-2026-001`: Quy trình Chẩn đoán Mạng Doanh nghiệp theo Mô hình 5 Tầng OSI.

## Tags
`BIOS`, `UEFI`, `NVMe`, `TPM 2.0`, `Secure Boot`, `BitLocker`, `Local AI`, `Ollama`, `Qwen 2.5`, `ChromaDB`, `FlashRank`, `Reranker`, `RAG Architecture`
