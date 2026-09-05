# HỆ THỐNG CƠ SỞ TRI THỨC CNTT DOANH NGHIỆP (ENTERPRISE IT KNOWLEDGE BASE)
# CHUYÊN ĐỀ: HỆ ĐIỀU HÀNH WINDOWS, PHỤC HỒI TỔN HẠI HỆ THỐNG & XỬ LÝ SỰ CỐ MÀN HÌNH XANH (BSOD)

---

## Document ID
`KB-WIN-2026-001`

## Category
`Windows Operating System / Client & Server Support / System Recovery`

## Department
`IT`

## Title
Quy trình Khắc phục Tổn hại Hệ thống Windows (DISM / SFC / CHKDSK) và Xử lý Lỗi Màn hình Xanh Chết chóc (BSOD BugCheck)

## Problem
Máy trạm Windows 10, Windows 11 hoặc Windows Server bị lỗi sập hệ thống bất ngờ kèm màn hình xanh chết chóc (BSOD), treo đơ khi khởi động (Boot Loop), báo hỏng tệp tin hệ thống (Component Store Corruption) hoặc các dịch vụ cốt lõi (Windows Update, RPC, Print Spooler, WMI) bị lỗi không thể kích hoạt.

## Symptoms
1. Máy tính xuất hiện màn hình xanh kèm mã dừng (Stop Code):
   - `CRITICAL_PROCESS_DIED` (0x000000EF)
   - `INACCESSIBLE_BOOT_DEVICE` (0x0000007B)
   - `DRIVER_IRQL_NOT_LESS_OR_EQUAL` (0x000000D1)
   - `SYSTEM_SERVICE_EXCEPTION` (0x0000003B)
   - `PAGE_FAULT_IN_NONPAGED_AREA` (0x00000050)
2. Chạy lệnh kiểm tra `sfc /scannow` báo lỗi: *"Windows Resource Protection found corrupt files but was unable to fix some of them"*.
3. Windows Update thất bại liên tục với các mã lỗi `0x80070002`, `0x80070003`, `0x800F081F`, hoặc `0x80240034`.
4. Event Viewer trong mục `System` ghi nhận hàng loạt lỗi Source: `Service Control Manager`, `Kernel-Power (Event ID 41)`, `Disk (Event ID 7, 11, 51)`.

## Error Message
* Màn hình BSOD: `"Your device ran into a problem and needs to restart. Stop Code: DRIVER_IRQL_NOT_LESS_OR_EQUAL (What failed: ntoskrnl.exe hoặc tcpip.sys hoặc nvlddmkm.sys)"`
* DISM Console: `"Error: 0x800f081f - The source files could not be found."`
* SFC Console: `"Windows Resource Protection could not perform the requested operation."`

## Environment
* **Hệ điều hành**: Windows 10 Pro / Enterprise (21H2, 22H2), Windows 11 Pro / Enterprise (22H2, 23H2), Windows Server 2019 / 2022.
* **Hệ thống tệp tin**: NTFS, ReFS, phân vùng GPT chuẩn UEFI Boot.

## Possible Causes
1. **Hỏng hóc tệp tin kho lưu trữ thành phần (WinSxS Component Store Corruption)**: Tắt máy đột ngột khi đang cài đặt bản vá Windows Update làm dở dang giao dịch Registry và DLL hệ thống.
2. **Xung đột hoặc lỗi Driver phần cứng (Faulty Kernel-Mode Driver)**: Driver card đồ họa (NVIDIA/Intel), driver card mạng (Realtek/Intel) hoặc driver chipset can thiệp vào vùng nhớ nhân (Kernel memory) trái phép.
3. **Lỗi vật lý ổ cứng hoặc Sector hỏng (Bad Sectors / File System Errors)**: Cấu trúc Master File Table (MFT) của NTFS bị hỏng hoặc chip nhớ SSD bị lỗi controller.
4. **Hỏng hóc cấu hình khởi động BCD (Boot Configuration Data)**: Cấu hình AHCI/RAID trong BIOS bị thay đổi hoặc mất phân vùng EFI System Partition (ESP).
5. **Dịch vụ cốt lõi bị vô hiệu hóa**: Các dịch vụ `Remote Procedure Call (RPC)`, `Windows Management Instrumentation (WMI)` hoặc `Cryptographic Services` bị tắt hoặc xung đột quyền bảo mật NTFS.

---

## Diagnosis (Quy trình chẩn đoán chi tiết)

### Bước 1: Thu thập và phân tích Memory Dump (BSOD Minidump)
1. Truy cập thư mục chứa file dump: `C:\Windows\Minidump\` hoặc `C:\Windows\MEMORY.DMP`.
2. Sử dụng công cụ **WinDbg (Windows Debugger)** hoặc **BlueScreenView**:
   - Mở file `.dmp` mới nhất.
   - Chạy lệnh phân tích tự động: `!analyze -v`.
   - Tìm 2 dòng quan trọng nhất:
     * `MODULE_NAME: <tên_driver_lỗi>` (Ví dụ: `nvlddmkm.sys` ➔ Driver đồ họa NVIDIA; `e1d68x64.sys` ➔ Driver mạng Intel; `fltmgr.sys` ➔ Trình lọc Antivirus).
     * `PROCESS_NAME: <tên_tiến_trình>` (Ví dụ: `chrome.exe`, `lsass.exe`, `System`).

### Bước 2: Kiểm tra nhật ký hệ thống Event Viewer
1. Mở `eventvwr.msc`.
2. Điều hướng tới `Windows Logs` -> `System`.
3. Lọc theo Level: `Critical`, `Error`.
4. Tìm kiếm:
   - **Event ID 41 (Kernel-Power)**: Máy bị mất nguồn đột ngột hoặc treo cứng.
   - **Event ID 1001 (BugCheck)**: Ghi nhận mã lỗi BSOD và tham số bộ nhớ.
   - **Event ID 7 / 51 / 153 (Disk / Ntfs)**: Cảnh báo ổ cứng có bad blocks hoặc lỗi I/O controller!

### Bước 3: Kiểm tra tính toàn vẹn của ổ cứng
Mở PowerShell (Run as Administrator):
```powershell
Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, OperationalStatus, HealthStatus
Get-Volume | Select-Object DriveLetter, FileSystemType, HealthStatus
```

---

## Solution (Quy trình khắc phục chuyên sâu chuẩn IT)

### Quy trình 1: Chuẩn hóa quy trình 3 bước phục hồi tổn hại Windows (DISM ➔ SFC ➔ CHKDSK)

> [!IMPORTANT]
> **THỨ TỰ BẮT BUỘC**: Phải chạy **DISM trước** để khôi phục kho tệp tin nguồn WinSxS, sau đó mới chạy **SFC** để sửa các file hệ điều hành đang hỏng từ kho WinSxS sạch!

Mở Command Prompt / PowerShell với quyền **Administrator**:

#### Bước 1.1: Quét và sửa chữa Component Store bằng DISM
```cmd
:: 1. Kiểm tra xem kho thành phần có bị lỗi không
DISM /Online /Cleanup-Image /CheckHealth
DISM /Online /Cleanup-Image /ScanHealth

:: 2. Khôi phục trực tiếp từ Windows Update Server
DISM /Online /Cleanup-Image /RestoreHealth
```
*Lưu ý: Nếu máy tính nội bộ bị chặn Internet và báo lỗi `Error: 0x800f081f`, hãy cắm USB cài Windows (hoặc mount file ISO Windows cùng phiên bản vào ổ `E:`) và chạy lệnh chỉ định nguồn nội bộ:*
```cmd
DISM /Online /Cleanup-Image /RestoreHealth /Source:WIM:E:\sources\install.wim:1 /LimitAccess
```

#### Bước 1.2: Quét và thay thế file hệ điều hành hỏng bằng SFC
```cmd
sfc /scannow
```
*Kỳ vọng kết quả:*
`"Windows Resource Protection found corrupt files and successfully repaired them."`

#### Bước 1.3: Quét và sửa chữa lỗi cấu trúc tệp tin ổ đĩa bằng CHKDSK
```cmd
chkdsk C: /f /r /x
```
*Nhấn `Y` để đồng ý quét khi khởi động lại máy tính.*

---

### Quy trình 2: Xử lý BSOD do xung đột Driver (Safe Mode & Driver Rollback)
1. **Khởi động vào Safe Mode**:
   - Nhấn giữ phím `Shift` và bấm **Restart** từ màn hình Windows Login.
   - Chọn `Troubleshoot` -> `Advanced options` -> `Startup Settings` -> Bấm `Restart` -> Nhấn phím `4` hoặc `F4` (Enable Safe Mode).
2. **Gỡ bỏ hoặc Rollback Driver gây lỗi**:
   - Mở `devmgmt.msc` (Device Manager).
   - Tìm thiết bị tương ứng với driver bị WinDbg cảnh báo (ví dụ Display Adapters hoặc Network Adapters).
   - Chuột phải -> **Properties** -> Tab **Driver**:
     * Bấm **Roll Back Driver** (nếu vừa cập nhật driver mới bị lỗi).
     * Hoặc chọn **Uninstall device** (tích chọn *"Attempt to remove the driver for this device"*).
3. Sử dụng công cụ **Display Driver Uninstaller (DDU)** trong Safe Mode nếu lỗi liên quan đến card đồ họa rời.

---

### Quy trình 3: Khắc phục lỗi dừng `INACCESSIBLE_BOOT_DEVICE` (0x0000007B)
Lỗi này thường xảy ra khi chuyển đổi chế độ lưu trữ trong BIOS hoặc mất driver AHCI/VMD:
1. Khởi động lại máy, nhấn phím `F2` hoặc `Del` vào BIOS Setup.
2. Tìm mục **System Configuration** -> **SATA Operation** (hoặc **Storage VMD Controller**):
   - Nếu đang để `RAID On` ➔ Đổi sang `AHCI/NVMe`.
   - Nếu đang để `AHCI` ➔ Đổi thử sang `RAID On`.
   - Nhấn `F10` lưu lại và khởi động.
3. Nếu vẫn không boot được, vào Windows Recovery Environment (WinRE) mở Command Prompt:
   ```cmd
   bootrec /fixmbr
   bootrec /fixboot
   bootrec /scanos
   bootrec /rebuildbcd
   ```

---

### Quy trình 4: Khắc phục sự cố Dịch vụ Windows cốt lõi (Windows Services & WMI Repair)
Nếu dịch vụ Print Spooler hoặc Windows Update bị kẹt:
```cmd
:: Reset dịch vụ Windows Update
net stop wuauserv
net stop cryptSvc
net stop bits
net stop msiserver

ren C:\Windows\SoftwareDistribution SoftwareDistribution.old
ren C:\Windows\System32\catroot2 catroot2.old

net start wuauserv
net start cryptSvc
net start bits
net start msiserver

:: Kiểm tra và sửa chữa cơ sở dữ liệu WMI Repository
winmgmt /verifyrepository
:: Nếu báo inconsistent, chạy lệnh salavaged:
winmgmt /salvagerepository
```

---

## Verification (Xác nhận kết quả sau xử lý)
1. **Kiểm tra tệp tin hệ thống**: Chạy lại `sfc /scannow` ➔ Kết quả: `"Windows Resource Protection did not find any integrity violations."`
2. **Kiểm tra độ ổn định**: Cho máy trạm chạy bài kiểm tra tải CPU/RAM hoặc khởi động lại 3 lần liên tiếp, không xuất hiện bất kỳ màn hình BSOD nào.
3. **Kiểm tra Event Viewer**: Không còn các Event ID 41 (Kernel-Power) hoặc Event ID 1001 (BugCheck) mới.
4. **Kiểm tra Windows Update**: Bấm `Check for updates` ➔ Tải về và cài đặt các bản vá tích lũy thành công 100%.

## Prevention (Biện pháp phòng ngừa)
1. Luôn tạo điểm khôi phục hệ thống (System Restore Point) trước khi cập nhật các bản vá lớn hoặc cài đặt phần mềm chuyên ngành.
2. Tắt tính năng Fast Startup trên Windows nếu máy thường xuyên gặp lỗi khởi động driver (`Control Panel` -> `Power Options` -> bỏ tích *"Turn on fast startup"*).
3. Đảm bảo dung lượng trống trên ổ `C:` luôn duy trì tối thiểu **$\ge 25 \text{ GB}$** cho việc hoán đổi tệp trang nhớ (Pagefile) và temp files.

## Escalation
* Chuyển cấp **Level 3 (Hardware Specialist / Vendor Warranty Support)** nếu: Mã BSOD `0x00000050` hoặc `0x0000001E` tái diễn liên tục sau khi đã cài đặt lại Windows sạch (Clean Install), nghi ngờ lỗi thanh nhớ RAM vật lý hoặc lỗi khe cắm bo mạch chủ (Motherboard).

## Risk Level
`High` (Nguy cơ mất dữ liệu người dùng nếu ổ cứng bị lỗi vật lý không được sao lưu kịp thời)

## Required Permission
`Local Administrator`

## Related Documents
* `KB-AD-2026-001`: Xử lý Sự cố Kênh Bảo mật Netlogon và Mất Quan hệ Tin cậy Domain.
* `KB-BOOT-2026-001`: Khắc phục lỗi Không nhận SSD NVMe và Sửa BCD Boot Configuration.

## Tags
`Windows 10`, `Windows 11`, `BSOD`, `DISM`, `SFC`, `CHKDSK`, `Minidump`, `WinDbg`, `Safe Mode`, `BugCheck`, `Driver Conflict`
