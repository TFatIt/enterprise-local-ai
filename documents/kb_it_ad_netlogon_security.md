# HỆ THỐNG CƠ SỞ TRI THỨC CNTT DOANH NGHIỆP (ENTERPRISE IT KNOWLEDGE BASE)
# CHUYÊN ĐỀ: ACTIVE DIRECTORY DOMAIN SERVICES & BẢO MẬT NETLOGON SECURE CHANNEL

---

## Document ID
`KB-AD-2026-001`

## Category
`Active Directory / Domain Services / Network Security`

## Department
`IT`

## Title
Xử lý Sự cố Kênh Bảo mật Netlogon (Vulnerable Netlogon Secure Channel) và Mất Quan hệ Tin cậy Domain (Trust Relationship Failed)

## Problem
Máy trạm (Client) hoặc Máy chủ thành viên (Member Server) thuộc Active Directory Domain không thể xác thực tài khoản Domain, xuất hiện lỗi mất quan hệ tin cậy ("The trust relationship between this workstation and the primary domain failed") hoặc Domain Controller từ chối kết nối secure channel với thông báo Event ID 5827 / 5829.

## Symptoms
1. Người dùng không thể đăng nhập vào máy tính bằng tài khoản Domain, nhận thông báo:
   *"The security database on the server does not have a computer account for this workstation trust relationship"* hoặc *"The trust relationship between this workstation and the primary domain failed"*.
2. Đăng nhập bằng tài khoản Local Administrator vẫn hoạt động bình thường.
3. Không truy cập được thư mục chia sẻ nội bộ (`\\domain.local\sysvol`, `\\fileserver`).
4. Trên Domain Controller, Event Viewer ghi nhận liên tiếp:
   - **Event ID 5827 (Error)**: *"The Netlogon service denied a vulnerable Netlogon secure channel connection from a machine account."*
   - **Event ID 5829 (Warning)**: *"The Netlogon service allowed a vulnerable Netlogon secure channel connection because machine account is specified in the 'Domain controller: Allow vulnerable Netlogon secure channel connections' group policy."*

## Error Message
* Client: `"The trust relationship between this workstation and the primary domain failed."`
* Domain Controller Netlogon Log / Event Viewer:
  `"The Netlogon service denied a vulnerable Netlogon secure channel connection from a machine account [MACHINENAME$]. (Event ID 5827)"`

## Environment
* **Domain Controller**: Windows Server 2019 / 2022 Datacenter, Forest Functional Level Windows Server 2016+.
* **Client**: Windows 10 Pro / Enterprise (21H2, 22H2), Windows 11 Pro / Enterprise (23H2).
* **Network**: Mạng LAN nội bộ doanh nghiệp, DNS trỏ về Domain Controller (192.168.1.10).

## Security Context & CVE Reference
* **CVE-2020-1472 (Zerologon)**: Lỗ hổng nghiêm trọng trong giao thức Netlogon Remote Protocol (MS-NRPC) sử dụng thuật toán mã hóa AES-CFB8 với Initialization Vector (IV) toàn số 0. Kẻ tấn công có thể giả mạo tài khoản máy tính hoặc chiếm đoạt Domain Controller.
* Bản vá bảo mật của Microsoft (Netlogon Enforcement Mode) bắt buộc mọi máy trạm phải sử dụng Secure RPC cho Netlogon. Bất kỳ máy trạm chạy OS cũ, firmware lỗi thời hoặc máy tính bị sai lệch mật khẩu tài khoản máy (`machine account password`) không gửi đúng authenticator sẽ bị DC lập tức từ chối (`Event ID 5827`).

## Possible Causes
1. **Lệch mật khẩu tài khoản máy tính (Machine Account Password Desynchronization)**: Máy trạm phục hồi từ snapshot cũ, restore backup, hoặc bị ngắt mạng quá 30 ngày trong khi DC đã tự động xoay vòng computer password.
2. **Thiếu bản vá Netlogon Secure RPC**: Thiết bị mạng hoặc thiết bị client chưa cập nhật hỗ trợ RPC signing & sealing.
3. **Lệch thời gian hệ thống (Kerberos Clock Skew)**: Giờ trên máy trạm chênh lệch quá 5 phút (300 giây) so với Domain Controller (PDC Emulator).
4. **Xung đột tên máy tính (Duplicate Computer Name / SID)**: Máy tính clone từ image chưa sysprep dẫn đến trùng SID với máy tính khác trên AD.
5. **DNS phân giải sai SRV Record**: Client không trỏ đúng về Domain Controller hoặc trỏ nhầm ra DNS ngoài (8.8.8.8) khiến Netlogon secure channel không thiết lập được.

## Diagnosis (Quy trình chẩn đoán từng bước)

### Bước 1: Kiểm tra kết nối mạng và phân giải DNS
Tại máy trạm, mở PowerShell (Administrator):
```powershell
# 1. Kiểm tra DNS Server hiện tại
Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, DNSServer

# 2. Kiểm tra phân giải bản ghi SRV của Domain Controller
Resolve-DnsName -Name _ldap._tcp.dc._msdcs.enterprise.local -Type SRV

# 3. Kiểm tra ping Domain Controller
Test-NetConnection -ComputerName dc01.enterprise.local -Port 389
Test-NetConnection -ComputerName dc01.enterprise.local -Port 88  # Kerberos
```

### Bước 2: Kiểm tra độ lệch thời gian (Clock Skew)
```powershell
# So sánh giờ máy trạm với Domain Controller
w32tm /stripchart /computer:dc01.enterprise.local /samples:3 /dataonly
```
*Nếu chênh lệch > 5 giây, cần đồng bộ lại NTP trước khi sửa domain join.*

### Bước 3: Kiểm tra trạng thái Secure Channel
```powershell
# Kiểm tra quan hệ tin cậy Secure Channel
Test-ComputerSecureChannel -Verbose
```
*Nếu trả về `False`, Secure Channel đã bị hỏng.*

### Bước 4: Kiểm tra Event Viewer trên Domain Controller
1. Mở `eventvwr.msc` trên Domain Controller.
2. Điều hướng tới: `Applications and Services Logs` -> `System`.
3. Lọc theo Source: `Netlogon`.
4. Tìm các Event ID:
   - **5827**: DC chủ động từ chối kết nối không an toàn từ client.
   - **5828**: Kết nối bị từ chối do chính sách máy tính.
   - **5829**: Cảnh báo kết nối dễ bị tổn thương được cho phép tạm thời qua GPO.
   - **5722 / 5723**: Không thể xác thực session key của máy tính client.

## Solution (Quy trình xử lý an toàn)

> [!WARNING]
> **PRODUCTION IMPACT & SECURITY PRINCIPLE**:
> Tuyệt đối KHÔNG vô hiệu hóa chính sách thực thi Netlogon Enforcement (`FullSecureChannelProtection = 0`) trên Domain Controller vì điều này mở toang cửa cho cuộc tấn công Zerologon (CVE-2020-1472). Phải khắc phục từ phía máy trạm!

### Phương án 1: Sửa chữa Secure Channel không cần khởi động lại (Ưu tiên số 1)
Đăng nhập vào máy trạm bằng tài khoản **Local Administrator** (ví dụ `.\Administrator`):
Mở PowerShell (Run as Administrator):
```powershell
# Bước 1: Đồng bộ thời gian với Domain Controller
w32tm /config /syncfromflags:domhier /update
net stop w32time ; net start w32time
w32tm /resync /force

# Bước 2: Sửa chữa Secure Channel bằng tài khoản Domain Admin / IT Admin
$cred = Get-Credential  # Nhập: enterprise\itadmin và mật khẩu
Test-ComputerSecureChannel -Repair -Credential $cred -Verbose
```
*Nếu lệnh trả về `True`, sự cố đã được khắc phục ngay lập tức mà không cần Unjoin domain.*

### Phương án 2: Reset Computer Account Password từ Client qua `Reset-ComputerMachinePassword`
Nếu lệnh `Test-ComputerSecureChannel` báo lỗi xác thực:
```powershell
# Reset mật khẩu tài khoản máy tính trực tiếp lên DC
Reset-ComputerMachinePassword -Credential $cred -Server "dc01.enterprise.local"
```
Hoặc dùng lệnh CMD cổ điển:
```cmd
netdom resetpwd /s:dc01.enterprise.local /ud:enterprise\itadmin /pd:*
```

### Phương án 3: Reset tài khoản máy tính trên Domain Controller (Nếu máy trạm bị khóa hoàn toàn)
1. Trên máy chủ Domain Controller, mở **Active Directory Users and Computers** (`dsa.msc`).
2. Tìm máy tính bị sự cố trong OU tương ứng.
3. Click chuột phải vào tài khoản máy tính -> Chọn **Reset Account**.
4. Trên máy trạm, chạy lệnh:
   ```cmd
   nltest /sc_reset:enterprise.local\dc01.enterprise.local
   ```

### Phương án 4: Unjoin và Rejoin Domain an toàn (Giải pháp cuối cùng)
Chỉ thực hiện khi các phương án trên thất bại do trùng GUID hoặc hỏng sâu SAM:
1. Sao lưu cấu hình profile người dùng local: `C:\Users\<username>`.
2. Chuyển máy tính về WORKGROUP:
   ```powershell
   Remove-Computer -UnjoinDomainCredential $cred -Workgroup "WORKGROUP" -Force -Restart
   ```
3. Sau khi máy khởi động lại, kiểm tra DNS IPv4 trỏ về `192.168.1.10`.
4. Gia nhập lại Domain:
   ```powershell
   Add-Computer -DomainName "enterprise.local" -Credential $cred -Restart
   ```

## Verification (Xác nhận thành công)
1. Chạy lệnh: `Test-ComputerSecureChannel -Verbose` ➔ Kết quả: `True`.
2. Chạy lệnh: `nltest /sc_query:enterprise.local` ➔ Kết quả: `Flags: 0 Connection Status = 0 0x0 NERR_Success The command completed successfully`.
3. Đăng xuất tài khoản Local, đăng nhập bằng tài khoản Domain User ➔ Đăng nhập thành công, nạp đúng Group Policy và mapped network drives.
4. Trên DC không còn xuất hiện Event ID 5827 cho máy tính này.

## Prevention (Phòng ngừa tái diễn)
1. **Không revert snapshot VM** của máy trạm hoặc máy chủ domain member mà không ngắt card mạng trước.
2. Đảm bảo dịch vụ **Windows Time (W32Time)** luôn chạy tự động trên tất cả các máy trạm trong domain.
3. Định kỳ chạy script kiểm tra các máy tính không liên lạc với DC quá 45 ngày để thu hồi tài khoản (`Get-ADComputer -Filter {LastLogonDate -lt (Get-Date).AddDays(-45)}`).

## Escalation
* Chuyển cấp **Level 3 (System Architect / Security Lead)** nếu: Xuất hiện Event ID 5827 trên diện rộng cho hàng loạt máy tính, nghi ngờ DC bị mất đồng bộ Kerberos krbtgt key hoặc xảy ra tấn công giả mạo Netlogon.

## Risk Level
`High` (Ảnh hưởng trực tiếp đến khả năng đăng nhập và vận hành của nhân viên)

## Required Permission
* Client: `Local Administrator`
* Domain: `Domain Admins` hoặc Tài khoản IT Support được ủy quyền (Delegation) quyền Reset Computer Account trong OU.

## Related Documents
* `KB-AD-2026-002`: Hướng dẫn Xử lý Sự cố GPO không áp dụng (Group Policy Processing Failure).
* `KB-DNS-2026-001`: Khắc phục lỗi phân giải DNS trong Active Directory Domain.

## Tags
`Active Directory`, `Netlogon`, `CVE-2020-1472`, `Secure Channel`, `Trust Relationship`, `Event ID 5827`, `Domain Join`, `Kerberos`
