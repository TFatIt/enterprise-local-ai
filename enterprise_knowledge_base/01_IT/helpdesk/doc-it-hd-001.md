# HƯỚNG DẪN XỬ LÝ SỰ CỐ MÀN HÌNH XANH (BSOD) TRÊN WINDOWS 10 / WINDOWS 11
**Mã tài liệu:** DOC-IT-HD-001  
**Phòng ban:** IT HelpDesk  
**Thẩm quyền:** Microsoft Learn Official Guidance  
**Phiên bản:** 2.1 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Giới thiệu và Nguyên nhân Gốc rễ
Lỗi màn hình xanh chết chóc (Blue Screen of Death - BSOD) xuất hiện khi nhân hệ điều hành Windows (Windows Kernel) gặp phải sự cố nghiêm trọng không thể tiếp tục vận hành an toàn. 
Các mã dừng (Bugcheck Stop Codes) phổ biến trong môi trường doanh nghiệp:
- `IRQL_NOT_LESS_OR_EQUAL (0x0000000A)`: Thường do driver thiết bị bị lỗi truy cập sai vùng nhớ bộ nhớ RAM.
- `PAGE_FAULT_IN_NONPAGED_AREA (0x00000050)`: Xung đột bộ nhớ vật lý (RAM) hoặc tệp hệ thống bị hỏng.
- `CRITICAL_PROCESS_DIED (0x000000EF)`: Một tiến trình cốt lõi của Windows (svchost, csrss, wininit) bị dừng đột ngột.

---

## 2. Quy trình Xử lý Sự cố Chuẩn hóa (Step-by-Step SOP)

### Bước 1: Thu thập thông tin từ Tệp Minidump
1. Điều hướng đến thư mục `C:\Windows\Minidump\`.
2. Sử dụng công cụ **WinDbg (Windows Debugger)** hoặc **BlueScreenView** để mở tệp `.dmp` mới nhất.
3. Chạy lệnh phân tích tự động:
   ```cmd
   !analyze -v
   ```
4. Xác định tên module gây lỗi tại dòng `MODULE_NAME` hoặc `IMAGE_NAME` (ví dụ: `nvlddmkm.sys` là driver card đồ họa NVIDIA).

### Bước 2: Kiểm tra và Phục hồi Tệp Tin Hệ thống
Mở Command Prompt (cmd) với quyền Administrator và chạy tuần tự hai lệnh sau:
```cmd
DISM.exe /Online /Cleanup-image /Restorehealth
sfc /scannow
```
*Lưu ý:* Chờ lệnh DISM tải các gói tệp sạch từ Windows Update về để sửa chữa kho lưu trữ thành phần trước khi chạy lệnh SFC.

### Bước 3: Kiểm tra Lỗi Bộ Nhớ Vật lý (RAM)
1. Bấm tổ hợp phím `Windows + R`, gõ:
   ```cmd
   mdsched.exe
   ```
2. Chọn **Restart now and check for problems**.
3. Máy tính sẽ khởi động lại vào công cụ **Windows Memory Diagnostic** để quét lỗi phần cứng RAM.

### Bước 4: Khởi động vào Chế độ Safe Mode nếu Máy tính Liên tục Reboot
1. Giữ phím `Shift` và bấm **Restart** tại màn hình đăng nhập Windows.
2. Chọn **Troubleshoot** -> **Advanced options** -> **Startup Settings** -> Bấm **Restart**.
3. Bấm phím `4` hoặc `F4` để kích hoạt **Enable Safe Mode**.
4. Gỡ cài đặt driver hoặc phần mềm vừa cài đặt gần nhất.
