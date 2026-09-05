# HỆ THỐNG CƠ SỞ TRI THỨC CNTT DOANH NGHIỆP (ENTERPRISE IT KNOWLEDGE BASE)
# CHUYÊN ĐỀ: MÁY IN MẠNG DOANH NGHIỆP & SỰ CỐ MÃ LỖI 0x0000011b (PRINT SERVER / PRINTNIGHTMARE)

---

## Document ID
`KB-PRN-2026-001`

## Category
`Printer / Print Server / Windows Services / Endpoint Support`

## Department
`IT`

## Title
Xử lý Sự cố Máy in Mạng Chia sẻ Lỗi 0x0000011b, Treo Dịch vụ Print Spooler và Triển khai GPO Printer

## Problem
Người dùng tại các phòng ban không thể kết nối hoặc không in được qua máy in chia sẻ nội bộ từ Print Server (hoặc máy trạm đóng vai trò máy chủ in). Khi bấm kết nối máy in, Windows báo mã lỗi dừng `0x0000011b` hoặc `0x00000709`. Ngoài ra, dịch vụ Print Spooler thường xuyên bị dừng đột ngột (Crash) làm kẹt hàng đợi in (Print Queue) của toàn cơ quan.

## Symptoms
1. Máy client kết nối vào máy in chia sẻ `\\printserver\HP_LaserJet_P3` xuất hiện hộp thoại lỗi:
   *"Windows cannot connect to the printer. Operation failed with error 0x0000011b"* hoặc *"Operation failed with error 0x0000007c"*.
2. Máy in hiển thị trạng thái `Offline` mặc dù máy chủ in vẫn bật và ping thông suốt.
3. Khi bấm In tài liệu, lệnh in gửi đi biến mất không in ra giấy, hoặc tài liệu nằm kẹt ở trạng thái `Deleting - Printing` trong hàng đợi máy in.
4. Dịch vụ **Print Spooler** trên máy tính client hoặc Print Server tự động dừng (`Stopped`), khởi động lại được vài phút lại bị sập.
5. Máy tính client đòi nhập tài khoản và mật khẩu Administrator khi kết nối máy in mạng (Point and Print Restriction).

## Error Message
* Windows Printer Error Dialog:
  `"Operation failed with error 0x0000011b."`
  `"Operation failed with error 0x00000709. Make sure that you have typed the name correctly, and that the printer is connected to the network."`
* Event Viewer Log (System):
  `"The Print Spooler service terminated unexpectedly. (Event ID 7031, Source: Service Control Manager)"`
  `"Faulting application name: spoolsv.exe, version: 10.0.19041.1, faulting module name: hpz3r500.dll (Event ID 1000)"`

## Environment
* **Print Server**: Windows Server 2019 / Windows Server 2022, hoặc máy trạm Windows 10/11 Pro chia sẻ máy in qua SMB.
* **Clients**: Windows 10, Windows 11 trong môi trường Active Directory Domain.
* **Dòng máy in**: HP LaserJet Enterprise, Canon imageRUNNER, Ricoh Aficio, Brother DCP.

## Bối cảnh Bảo mật & Nguồn gốc Lỗi 0x0000011b
* Xuất phát từ bản vá bảo mật của Microsoft khắc phục lỗ hổng **PrintNightmare** (CVE-2021-34527 & CVE-2021-1675 - Thực thi mã độc từ xa qua dịch vụ Spooler).
* Bản vá bảo mật (KB5005565, KB5005568) nâng cấp mức độ xác thực của giao thức Remote Procedure Call (RPC). Mặc định, Windows Server yêu cầu mức xác thực bảo mật riêng tư `RPC_C_AUTHN_LEVEL_PKT_PRIVACY` (Packet Privacy).
* Nếu các máy trạm client Windows 10/11 hoặc máy tính chưa cập nhật bản vá tương ứng kết nối bằng kênh RPC không mã hóa gói tin, Print Server sẽ ngay lập tức từ chối và trả về mã lỗi **`0x0000011b`**.

---

## Possible Causes
1. **Yêu cầu RPC Authentication Level Privacy**: Khóa Registry `RpcAuthnLevelPrivacyEnabled` trên Print Server đang đặt giá trị 1 và từ chối các máy client kết nối RPC không mã hóa.
2. **Xung đột Driver máy in bên thứ ba (Corrupt / Incompatible V3 Driver)**: Sử dụng driver cũ (Type 3) chạy chung tiến trình với `spoolsv.exe` làm sập toàn bộ dịch vụ Spooler khi gặp file in chứa font chữ lạ hoặc bảng tính Excel phức tạp.
3. **Kẹt tệp đệm hàng đợi in (Corrupt Spooler Cache Files)**: Các tệp `.SPL` và `.SHD` trong thư mục đệm `C:\Windows\System32\spool\PRINTERS\` bị khóa hoặc hỏng dữ liệu.
4. **Chính sách Point and Print Restrictions của Group Policy (GPO)**: GPO chặn nhân viên không có quyền Admin cài đặt driver máy in tự động từ máy chủ.
5. **Cổng giao tiếp máy in bị sai (WSD Port vs Standard TCP/IP Port)**: Windows tự động nhận diện máy in qua cổng WSD (Web Services for Devices) chập chờn thay vì dùng địa chỉ IP tĩnh cố định.

---

## Diagnosis (Quy trình chẩn đoán từng bước)

### Bước 1: Kiểm tra trạng thái dịch vụ Print Spooler
Mở PowerShell (Run as Administrator):
```powershell
Get-Service -Name Spooler
```
Nếu Status là `Stopped`, khởi động lại dịch vụ và kiểm tra Event Viewer xem module nào gây sập:
```powershell
Start-Service -Name Spooler
Get-WinEvent -LogName System -MaxEvents 5 | Where-Object { $_.ProviderName -eq "Service Control Manager" }
```

### Bước 2: Kiểm tra kết nối mạng và cổng RPC đến Print Server
Từ máy trạm client, chạy lệnh:
```powershell
Test-NetConnection -ComputerName 192.168.1.50 -Port 445  # SMB File/Printer Sharing
Test-NetConnection -ComputerName 192.168.1.50 -Port 135  # RPC Endpoint Mapper
```

### Bước 3: Kiểm tra cấu hình Registry khóa RPC trên Print Server
```cmd
reg query "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Print" /v RpcAuthnLevelPrivacyEnabled
```

---

## Solution (Quy trình xử lý chuẩn hóa an toàn)

### Giải pháp 1: Khắc phục triệt để lỗi 0x0000011b

> [!WARNING]
> **PRODUCTION PRINCIPLE**: Trong môi trường mạng nội bộ doanh nghiệp đã được bảo vệ bởi tường lửa, giải pháp xử lý nhanh lỗi 0x0000011b là điều chỉnh khóa `RpcAuthnLevelPrivacyEnabled` trên **Máy chủ In (Print Server)**.

#### Bước 1: Thao tác trên Print Server (hoặc máy tính đang cắm dây chia sẻ máy in)
1. Mở Command Prompt (Run as Administrator):
2. Chạy lệnh tắt ràng buộc mã hóa RPC gói tin:
   ```cmd
   reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Print" /v RpcAuthnLevelPrivacyEnabled /t REG_DWORD /d 0 /f
   ```
3. Khởi động lại dịch vụ Print Spooler:
   ```cmd
   net stop spooler
   net start spooler
   ```

#### Bước 2: Thao tác trên Máy trạm Client
1. Xóa kết nối máy in cũ bị lỗi:
   - Mở `Control Panel` -> `Devices and Printers`.
   - Chuột phải vào máy in bị lỗi -> Chọn **Remove device**.
2. Kết nối lại máy in qua đường dẫn mạng:
   - Nhấn `Win + R`, gõ: `\\192.168.1.50` (hoặc tên máy chủ in `\\printserver`).
   - Chuột phải vào máy in -> Chọn **Connect**.
   - Máy tính sẽ tải driver và kết nối thành công 100%, không còn báo lỗi `0x0000011b`!

---

### Giải pháp 2: Xử lý triệt để Hàng đợi in bị kẹt & Sập Print Spooler (Spooler Crash Clean)
Tạo script dọn sạch bộ đệm hàng đợi in bị tắc nghẽn:
Mở PowerShell (Administrator) và thực thi script:
```powershell
# 1. Dừng dịch vụ Spooler
Stop-Service -Name Spooler -Force

# 2. Xóa sạch toàn bộ tệp lệnh in bị kẹt (.spl và .shd)
Get-ChildItem -Path "$env:SystemRoot\System32\spool\PRINTERS\*" -Force | Remove-Item -Force -Verbose

# 3. Khởi động lại Spooler
Start-Service -Name Spooler

# 4. Kiểm tra lại trạng thái
Get-Service -Name Spooler
```

---

### Giải pháp 3: Chuyển đổi từ Cổng WSD sang Standard TCP/IP Port (Khắc phục Printer Offline)
1. Mở `printmanagement.msc` (Print Management) hoặc `control printers`.
2. Chuột phải vào máy in -> **Printer properties** -> Tab **Ports**.
3. Bấm nút **Add Port...** -> Chọn **Standard TCP/IP Port** -> Bấm **New Port**.
4. Nhập địa chỉ IP tĩnh của máy in văn phòng (Ví dụ: `192.168.1.50`).
5. Bỏ tích ô *"SNMP Status Enabled"* nếu máy in thường xuyên bị báo Offline giả mạo.
6. Bấm **Apply** và **OK**.

---

### Giải pháp 4: Cấu hình Group Policy (GPO) triển khai Point and Print không đòi mật khẩu Admin
Để toàn bộ nhân viên trong Domain tự động nhận máy in mà không bị hỏi mật khẩu:
1. Mở **Group Policy Management** (`gpmc.msc`) trên Domain Controller.
2. Tạo hoặc chỉnh sửa GPO: `Default Domain Policy` (hoặc GPO chuyên biệt cho Clients).
3. Điều hướng tới:
   `Computer Configuration` -> `Administrative Templates` -> `Printers`:
   * **Point and Print Restrictions**: Chọn `Enabled`.
     - Tích chọn *"Users can only point and print to these servers"*: Nhập tên FQDN của Print Server (ví dụ: `printserver.enterprise.local`).
     - Mục *"When installing drivers for a new connection"*: Chọn **Do not show warning or elevation prompt**.
     - Mục *"When updating drivers for an existing connection"*: Chọn **Do not show warning or elevation prompt**.
   * **Package Point and Print - Approved servers**: Chọn `Enabled` -> Nhập `printserver.enterprise.local`.
4. Trên máy client, chạy lệnh cập nhật chính sách ngay:
   ```cmd
   gpupdate /force
   ```

---

## Verification (Quy trình xác nhận)
1. **Kiểm tra kết nối**: Client kết nối máy in mạng không xuất hiện hộp thoại lỗi `0x0000011b`.
2. **In trang thử nghiệm (Print Test Page)**:
   - Vào `Printer properties` -> Bấm **Print Test Page**.
   - Lệnh in gửi đi lập tức, trang in ra khỏi khay giấy trong vòng 5 giây, hàng đợi in trở về số 0.
3. **Kiểm tra dịch vụ Spooler**: Chạy lệnh `Get-Service Spooler` sau 1 giờ hoạt động liên tục ➔ Trạng thái luôn duy trì `Running`.

## Prevention (Biện pháp phòng ngừa)
1. **Sử dụng Driver Type 4 (V4) hoặc kích hoạt Driver Isolation**:
   - Trong `Print Management`, chuột phải vào driver -> Chọn **Set Driver Isolation** -> **Isolated**. Điều này giúp driver chạy trên tiến trình riêng biệt (`PrintIsolationHost.exe`), nếu driver bị lỗi sẽ không làm sập tiến trình `spoolsv.exe` của toàn máy chủ!
2. **Luôn đặt IP tĩnh cho máy in văn phòng** và cấu hình cấp phát DHCP Reservation tương ứng.
3. Định kỳ dọn dẹp các máy in chia sẻ cũ không còn sử dụng trong Domain.

## Escalation
* Chuyển cấp **Level 2 / System Administrator** nếu: Dịch vụ Spooler sập liên tục do driver máy in đa năng chuyên dụng (máy in photocopy Ricoh/Canon công nghiệp) cần cấu hình cổng RAW 9100 và cài gói driver PCL6 chuyên biệt của hãng.

## Risk Level
`Medium` (Ảnh hưởng đến công tác in ấn chứng từ của phòng ban)

## Required Permission
* Print Server: `Local Administrator / Domain Admins`
* GPO: `Domain Admins`
* Client: `Domain Users`

## Related Documents
* `KB-WIN-2026-001`: Quy trình Khắc phục Tổn hại Hệ thống Windows và Xử lý Lỗi Màn hình Xanh (BSOD).
* `KB-AD-2026-002`: Hướng dẫn Cấu hình Group Policy triển khai tài nguyên mạng.

## Tags
`Printer`, `Print Server`, `0x0000011b`, `PrintNightmare`, `Print Spooler`, `Point and Print`, `GPO Deployment`, `WSD Port`, `TCP/IP Port`
