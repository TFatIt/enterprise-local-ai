# HỆ THỐNG CƠ SỞ TRI THỨC CNTT DOANH NGHIỆP (ENTERPRISE IT KNOWLEDGE BASE)
# CHUYÊN ĐỀ: OUTLOOK 365, CHỮ KÝ SỐ DOANH NGHIỆP & SỰ CỐ "VALUE CANNOT BE NULL. PARAMETER NAME: SOURCE"

---

## Document ID
`KB-APP-2026-001`

## Category
`Enterprise Software / Outlook Email / Digital Signature (Chữ ký số) / PKI`

## Department
`IT`

## Title
Xử lý Sự cố Ký số Doanh nghiệp (Lỗi "Value cannot be null. Parameter name: source"), Lỗi Token Chữ ký số và Xử lý Lặp Xác thực Outlook 365

## Problem
Nhân viên phòng Kế toán, Nhân sự hoặc Ban Giám đốc khi ký số nộp báo cáo thuế (eTax), bảo hiểm xã hội (BHXH điện tử) hoặc hóa đơn điện tử xuất hiện thông báo lỗi nghiêm trọng *"Value cannot be null. Parameter name: source"* hoặc trình duyệt không nhận USB Token. Đồng thời, tài khoản Outlook trên máy tính nhân viên liên tục hiện hộp thoại đòi nhập mật khẩu (Password Prompt Loop) không thể gửi/nhận email.

## Symptoms
1. Khi bấm nút "Ký điện tử" trên cổng Dịch vụ công hoặc phần mềm BHXH/Thuế, màn hình xuất hiện popup báo lỗi:
   *"Value cannot be null. Parameter name: source"*.
2. Phần mềm quản lý chữ ký số (Token Manager của VNPT-CA, Viettel-CA, FPT-CA, MISA eSign) báo *"Chưa cắm USB Token"* hoặc cắm Token nhưng danh sách chứng thư số bị trống trơn.
3. Trình duyệt Chrome / Edge báo lỗi không thể kết nối tới phần mềm ký số nội bộ (Component signing qua WebSocket `wss://localhost:19999` hoặc `http://127.0.0.1:10888`).
4. Trên phần mềm Microsoft Outlook:
   - Thanh trạng thái hiển thị *"Need Password"* hoặc *"Disconnected"*.
   - Hộp thoại đăng nhập Microsoft 365 nhấp nháy rồi tắt, lặp lại liên tục (Modern Authentication Loop).
   - Tệp dữ liệu thư `.ost` bị lỗi không thể mở Outlook (`"Cannot open your default e-mail folders. The file C:\...\outlook.ost is not an Outlook data file"`).

## Error Message
* Cổng Dịch vụ công / Phần mềm Ký điện tử:
  `"Lỗi hệ thống: Value cannot be null. Parameter name: source tại System.Linq.Enumerable.Cast[TResult](IEnumerable source) hoặc System.Security.Cryptography.X509Certificates"`
* Cổng Thuế / BHXH:
  `"Không tìm thấy chứng thư số hợp lệ hoặc Token chưa được cắm vào máy tính."`
* Outlook Error:
  `"The server is unavailable. Error 0x80040115 / 0x800CCC0E"`
  `"Cannot start Microsoft Outlook. Cannot open the Outlook window."`

## Environment
* **Hệ điều hành**: Windows 10, Windows 11 (64-bit).
* **Trình duyệt**: Google Chrome, Microsoft Edge, Cốc Cốc.
* **Hạ tầng Chữ ký số (CA)**: VNPT-CA, Viettel-CA, BKAV-CA, FPT-CA, NewCA.
* **Ứng dụng Email**: Microsoft 365 Apps for Enterprise, Office 2019 / 2021 Pro Plus (Outlook Desktop).

---

## Phân tích Chuyên sâu: Lỗi "Value cannot be null. Parameter name: source"

### Bản chất kỹ thuật
Lỗi này xuất phát từ thư viện nền tảng **.NET Framework** (cụ thể là phương thức LINQ `System.Linq.Enumerable` khi thực thi các toán tử như `.Select()`, `.Where()`, `.Cast<T>()` trên một tập hợp đối tượng bị `null`).

Trong ngữ cảnh Ký số (Digital Signing Middleware):
Ứng dụng ký số gửi truy vấn tới kho chứng thư số của Windows (Windows Certificate Store - `Cert:\CurrentUser\My`) hoặc truy vấn API PKCS#11 của USB Token để lấy danh sách chứng thư số:
```csharp
// Đoạn mã nguồn gây lỗi trong middleware ký số:
X509Store store = new X509Store(StoreName.My, StoreLocation.CurrentUser);
store.Open(OpenFlags.ReadOnly);
var certs = store.Certificates; // Trả về null nếu CSP driver lỗi hoặc không cấp quyền truy cập
var validCerts = certs.Cast<X509Certificate2>().Where(...); // Bắn Exception: "Value cannot be null. Parameter name: source"
```

### Nguyên nhân gây ra lỗi:
1. **Kho chứng chỉ Windows (Certificate Store) trả về null**: Driver PKCS#11 / CSP của USB Token bị hỏng hoặc chưa cài đặt module mã hóa Cryptographic Service Provider (CSP).
2. **Chứng thư số đã hết hạn hoặc bị thu hồi (Expired / Revoked Certificate)**: Token vẫn cắm nhưng ngày hiệu lực của chứng thư số đã quá hạn.
3. **Thiếu quyền truy cập vào khóa riêng tư (Private Key Permission)**: Tài khoản người dùng Windows Standard User không có quyền đọc container khóa riêng tư trên USB Token.
4. **Xung đột phiên bản .NET Framework**: Ứng dụng ký số yêu cầu .NET Framework 4.8 hoặc 3.5 nhưng máy tính bị thiếu hoặc hỏng tệp runtime.
5. **Dịch vụ Ký số cục bộ (Local Signer Service / WebSocket Server) bị tắt**: Dịch vụ nền chạy trên cổng `localhost:10888` hoặc `19999` chưa được khởi động hoặc bị Tường lửa / Antivirus chặn kết nối WebSocket.

---

## Diagnosis (Quy trình chẩn đoán từng bước)

### Bước 1: Kiểm tra chứng thư số trong Windows Certificate Store
Nhấn `Win + R`, gõ:
```cmd
certmgr.msc
```
1. Điều hướng tới thư mục: `Personal` (Cá nhân) -> `Certificates`.
2. Kiểm tra xem có chứng thư số của công ty mang tên nhà cấp phép (VNPT-CA, Viettel-CA,...) hay không.
3. Nhấp đúp vào chứng chỉ kiểm tra:
   - **Valid from ... to ...**: Đã hết hạn hay chưa?
   - Dưới đáy có dòng biểu tượng chiếc chìa khóa vàng: *"You have a private key that corresponds to this certificate"* hay không. Nếu không có chìa khóa, client không thể ký số!

### Bước 2: Kiểm tra USB Token bằng công cụ Token Manager của hãng
1. Mở phần mềm quản lý Token (ví dụ: *VNPT-CA Token Manager* hoặc *Viettel-CA Token Manager*).
2. Vào mục **Chứng thư số** -> Nhập mã PIN của USB Token.
3. Nếu phần mềm báo: *"Không tìm thấy thiết bị"* ➔ Kiểm tra cổng USB (cắm trực tiếp vào cổng sau mainboard, không cắm qua hub chia USB) hoặc driver chip Smart Card bị thiếu.

### Bước 3: Kiểm tra cổng kết nối WebSocket của phần mềm Ký số cục bộ
Mở PowerShell (Run as Administrator):
```powershell
# Kiểm tra dịch vụ ký số có đang lắng nghe cổng không
Get-NetTCPConnection | Where-Object { $_.LocalPort -in 10888, 19999, 8080, 21089 } | Select-Object LocalAddress, LocalPort, State, OwningProcess
```
*Nếu không có kết quả ➔ Phần mềm ký số nền (Signer Service / Plugin ký số) chưa khởi động!*

### Bước 4: Kiểm tra sự cố xác thực trên Outlook (Modern Authentication Loop)
Mở Command Prompt:
```cmd
dsregcmd /status
```
*Kiểm tra trạng thái `AzureAdJoined: YES` và `WAMDefaultSet: YES`. Nếu WAM (Web Account Manager) bị lỗi, Outlook sẽ lặp hộp thoại đăng nhập liên tục.*

---

## Solution (Quy trình xử lý dứt điểm)

### Phần A: Khắc phục lỗi Chữ ký số "Value cannot be null. Parameter name: source"

#### Bước 1: Cài đặt lại Driver PKCS#11 CSP mới nhất của hãng cấp Token
1. Rút USB Token ra khỏi máy tính.
2. Vào `Control Panel` -> `Programs and Features`: Gỡ bỏ phần mềm Token Manager cũ.
3. Khởi động lại máy tính.
4. Cắm lại USB Token:
   - Mở ổ đĩa ảo xuất hiện trong `This PC` (ổ đĩa quang ảo tích hợp trong USB Token).
   - Chuột phải vào file `setup.exe` (hoặc `autorun.exe`) -> Chọn **Run as administrator**.
   - Cài đặt đầy đủ phần mềm Token Manager và nạp Root CA.

#### Bước 2: Đăng ký lại thư viện Cryptographic Service Provider (CSP)
Mở Command Prompt với quyền Administrator:
```cmd
cd /d C:\Windows\System32
regsvr32 /u /s bit4xpki.dll
regsvr32 /s bit4xpki.dll
regsvr32 /s actprxy.dll
```
*(Đối với VNPT-CA: Mở VNPT-CA Token Manager -> Chọn menu Cấu hình -> Bấm nút **"Đăng ký thư viện CSP"** hoặc **"Cập nhật chứng thư số vào Windows Store"**).*

#### Bước 3: Cài đặt và cấu hình Plugin Ký số Cổng Dịch vụ công / Thuế
1. Tải và cài đặt phần mềm ký số chuẩn từ cơ quan chức năng:
   - Thuế điện tử: **eTax Viewer** và tiện ích **eSigner Java Plugin** (hoặc Extension eSigner 1.0.8 trên Chrome).
   - Bảo hiểm xã hội: Phần mềm **BHXH Kê khai điện tử** (VssID / EFY-eBHXH / VNPT-BHXH).
2. Kiểm tra Extension trên trình duyệt Chrome / Edge:
   - Vào `chrome://extensions/` ➔ Đảm bảo Extension ký điện tử đã được **BẬT (Enabled)** và cho phép *"Truy cập vào các tệp URL"*.

---

### Phần B: Khắc phục lỗi Outlook đòi mật khẩu liên tục & Hỏng tệp OST

#### Bước 1: Kích hoạt lại xác thực hiện đại (Modern Auth) qua Registry
Mở Command Prompt (Administrator):
```cmd
reg add "HKEY_CURRENT_USER\Software\Microsoft\Exchange" /v AlwaysUseMSOAuthForAutoDiscover /t REG_DWORD /d 1 /f
reg add "HKEY_CURRENT_USER\Software\Microsoft\Office\16.0\Common\Identity" /v EnableADAL /t REG_DWORD /d 1 /f
reg add "HKEY_CURRENT_USER\Software\Microsoft\Office\16.0\Common\Identity" /v DisableADALatopWAMOverride /t REG_DWORD /d 1 /f
```

#### Bước 2: Xóa sạch thông tin đăng nhập bị lỗi trong Windows Credential Manager
1. Đóng hoàn toàn Microsoft Outlook và Teams.
2. Mở `control keymgr.dll` (Credential Manager).
3. Chọn mục **Windows Credentials**.
4. Tìm và xóa toàn bộ các mục liên quan đến:
   - `MicrosoftOffice16_Data:...`
   - `MS.Outlook:...`
   - `adal_cache...`
5. Khởi động lại Outlook ➔ Nhập mật khẩu tài khoản M365 và xác thực ứng dụng Microsoft Authenticator một lần duy nhất.

#### Bước 3: Sửa chữa tệp tin dữ liệu hỏng (.OST / .PST)
Nếu Outlook báo tệp tin bị hỏng:
1. Đóng Outlook.
2. Nhấn `Win + R`, chạy công cụ:
   ```cmd
   "C:\Program Files\Microsoft Office\root\Office16\SCANPST.EXE"
   ```
   *(Hoặc tại `C:\Program Files (x86)\Microsoft Office\root\Office16\SCANPST.EXE`)*.
3. Bấm **Browse** -> Chọn tệp tin `.ost` của tài khoản (mặc định tại `%LOCALAPPDATA%\Microsoft\Outlook\`).
4. Bấm **Start** để quét ➔ Khi phát hiện lỗi, tích chọn *"Make a backup of scanned file before repairing"* ➔ Bấm **Repair**.

---

## Verification (Xác nhận kết quả)
1. **Kiểm tra ký số**: Mở cổng Dịch vụ công / Thuế điện tử ➔ Bấm "Ký điện tử" ➔ Hộp thoại chọn chứng thư số hiện lên đầy đủ thông tin Tên Công ty, Mã số thuế, Nhà cấp phép ➔ Nhập mã PIN và ký văn bản thành công, không còn thông báo *"Value cannot be null. Parameter name: source"*.
2. **Kiểm tra Outlook**: Mở Outlook ➔ Góc dưới bên phải hiển thị trạng thái *"Connected to: Microsoft Exchange"* ➔ Thử gửi và nhận email nội bộ, độ trễ nhận mail < 5 giây.

## Prevention (Biện pháp phòng ngừa)
1. Thiết lập nhắc nhở tự động trước 30 ngày khi chứng thư số công ty sắp hết hạn để phòng Tài chính - Kế toán chủ động gia hạn với nhà mạng.
2. Hướng dẫn nhân viên rút USB Token an toàn (Eject) trước khi tháo khỏi máy, tránh làm hỏng phân vùng nhớ chip EEPROM trên Token.
3. Không đăng nhập cùng một tài khoản email M365 trên quá 5 thiết bị cá nhân để tránh bị khóa bảo vệ Identity Protection.

## Escalation
* Chuyển cấp **Level 2 / Application Support** nếu: Token bị khóa mã PIN (nhập sai quá 3-5 lần) cần liên hệ tổng đài nhà cấp phép (VNPT/Viettel CA) bằng mã PUK để mở khóa thiết bị.

## Risk Level
`Medium` (Ảnh hưởng trực tiếp đến nghiệp vụ kê khai thuế, hải quan và giao dịch chứng từ điện tử)

## Required Permission
`Local Administrator` (Để cài đặt CSP Driver và sửa Registry)

## Related Documents
* `KB-WIN-2026-001`: Khắc phục lỗi Hệ điều hành Windows và sập dịch vụ cốt lõi.
* `KB-SEC-2026-001`: Quy định Quản lý Thiết bị Lưu trữ USB và Chữ ký số Doanh nghiệp.

## Tags
`Digital Signature`, `Chữ ký số`, `USB Token`, `VNPT-CA`, `Viettel-CA`, `Value cannot be null`, `Outlook 365`, `Modern Authentication`, `SCANPST`, `Credential Manager`
