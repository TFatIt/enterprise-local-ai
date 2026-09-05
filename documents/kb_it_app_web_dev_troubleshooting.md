# HỆ THỐNG CƠ SỞ TRI THỨC CNTT DOANH NGHIỆP (ENTERPRISE IT KNOWLEDGE BASE)
# CHUYÊN ĐỀ: HỖ TRỢ PHÁT TRIỂN PHẦN MỀM (APP/DEV SUPPORT) & QUẢN TRỊ WEBSITE WORDPRESS DOANH NGHIỆP

---

## Document ID
`KB-DEV-2026-001`

## Category
`Software Development / Web Architecture / WordPress / Developer Support`

## Department
`IT`

## Title
Sổ tay Hỗ trợ Nhà phát triển (React, .NET 8, Flutter, Mobile Emulator, CORS) và Xử lý Sự cố Cổng thông tin Web Doanh nghiệp (WordPress / SSL / LiteSpeed / SMTP)

## Problem
1. **Lập trình viên / Dev Team**: Lỗi biên dịch dự án React/Vite, lỗi Gradle trong Android Studio / Flutter, lỗi CORS khi gọi REST API từ Frontend sang Backend (.NET 8 / Node.js), lỗi kết nối cơ sở dữ liệu hoặc hết Connection Pool.
2. **Quản trị Web & Cổng thông tin**: Website doanh nghiệp (WordPress) bị sập với mã lỗi 502/504 Bad Gateway, lỗi SSL Certificate, email đơn hàng / thông báo không gửi được qua SMTP, hoặc trình chỉnh sửa Elementor bị màn hình trắng (White Screen of Death).

## Symptoms
* **Dev Support**:
  - React/Vite: Console báo lỗi `[vite] WebSocket connection to 'ws://localhost:5173/' failed` hoặc `Module not found: Can't resolve '...'`.
  - React Native / Flutter: Build Android báo `A problem occurred evaluating project ':app'. > Could not resolve all files for configuration...` hoặc `SDK location not found`.
  - API Call: Trình duyệt chặn kết nối API với lỗi đỏ: `Access to XMLHttpRequest at '...' from origin 'http://localhost:5173' has been blocked by CORS policy`.
* **WordPress / Web**:
  - Khách hàng truy cập website gặp thông báo `502 Bad Gateway` hoặc `Error establishing a database connection`.
  - Elementor khi bấm "Edit with Elementor" xoay vòng vô tận hoặc báo `The preview could not be loaded`.
  - Email gửi từ website báo lỗi: `SMTP connect() failed. Could not authenticate`.

## Error Message
* CORS Policy:
  `"Access-Control-Allow-Origin header is missing on the requested resource."`
* Gradle / Android Studio:
  `"Execution failed for task ':app:processDebugResources'. > Android resource linking failed"`
* WordPress Debug Log (`wp-content/debug.log`):
  `"Fatal error: Allowed memory size of 134217728 bytes exhausted (tried to allocate 20971520 bytes) in .../elementor/..."`
  `"PHP Fatal error: Uncaught mysqli_real_connect(): (HY000/2002): Connection refused"`

## Environment
* **Frontend Tech Stack**: React 18, TypeScript, Vite, Node.js 20 LTS.
* **Mobile Stack**: Flutter SDK 3.x, React Native / Expo, Android SDK Platform 34.
* **Backend Tech Stack**: .NET 8 Web API, Node.js / Express, PostgreSQL 16, Microsoft SQL Server 2022.
* **Web Hosting**: Ubuntu Server 22.04 LTS, Nginx / LiteSpeed Web Server, PHP 8.2 / 8.3, MariaDB / MySQL.

---

## Possible Causes

### Nhóm 1: Sự cố Môi trường Lập trình (Developer Environment)
1. **Lỗi chính sách CORS (Cross-Origin Resource Sharing)**: Backend chưa cho phép Origin của môi trường phát triển (`http://localhost:5173` hoặc `http://localhost:3000`) hoặc thiếu các HTTP Headers cho phép (`Authorization`, `Content-Type`).
2. **Kẹt Cache & Sai lệch node_modules**: Phiên bản package trong `package-lock.json` bị xung đột với `node_modules` hoặc cache của Vite / Metro bundler bị lỗi thời.
3. **Thiếu biến môi trường Android SDK**: Chưa khai báo biến môi trường `ANDROID_HOME` trong Windows Environment Variables hoặc file `android/local.properties` thiếu đường dẫn SDK.
4. **Cạn kiệt Connection Pool Database**: Ứng dụng Backend không đóng kết nối (Connection Leak) sau khi thực thi truy vấn hoặc `Max Pool Size` đặt quá nhỏ trong Connection String.

### Nhóm 2: Sự cố Website Doanh nghiệp (WordPress & Hosting)
1. **Cạn kiệt giới hạn bộ nhớ PHP (PHP Memory Limit Exhausted)**: Các plugin nặng (Elementor, WooCommerce) yêu cầu tối thiểu 256MB - 512MB RAM nhưng cấu hình PHP mặc định chỉ cấp 128MB.
2. **Xung đột Plugin hoặc Trình đệm LiteSpeed Cache**: Cơ chế nén CSS/JS (Minify / Combine) làm sai lệch thứ tự thực thi của JavaScript hoặc lỗi Object Cache (Redis / Memcached) bị ngắt kết nối.
3. **Cấu hình SMTP sai cổng hoặc bị chặn Firewall**: Cổng gửi thư 25 hoặc 465/587 bị nhà cung cấp mạng (ISP/Hosting) chặn cổng đi (Outbound Port Block) hoặc tài khoản email bảo mật 2 lớp chưa tạo Mật khẩu ứng dụng (App Password).

---

## Diagnosis (Quy trình chẩn đoán chuẩn)

### Bước 1: Chẩn đoán lỗi CORS trên Backend
Mở Developer Tools (`F12`) -> Tab **Network** -> Bấm vào request bị lỗi:
1. Quan sát phản hồi của request `OPTIONS` (Preflight request).
2. Kiểm tra Response Headers xem có dòng:
   ```http
   Access-Control-Allow-Origin: http://localhost:5173
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
   Access-Control-Allow-Headers: Content-Type, Authorization
   ```

### Bước 2: Chẩn đoán lỗi Android SDK / Flutter
Mở Terminal tại thư mục dự án:
```powershell
# Đối với Flutter:
flutter doctor -v
# Quan sát xem mục Android toolchain đã có đủ dấu tích xanh chưa (đặc biệt là Android SDK licenses).

# Đối với Android Studio:
echo $env:ANDROID_HOME
# Đường dẫn chuẩn: C:\Users\<Username>\AppData\Local\Android\Sdk
```

### Bước 3: Chẩn đoán lỗi WordPress 502 / PHP Memory Limit
Truy cập máy chủ Web qua SSH:
```bash
# 1. Xem nhật ký lỗi PHP
tail -n 50 /var/log/php8.2-fpm.log

# 2. Xem nhật ký lỗi Nginx
tail -n 50 /var/log/nginx/error.log

# 3. Kiểm tra trạng thái cơ sở dữ liệu MySQL
systemctl status mariadb
```

---

## Solution (Quy trình khắc phục từng nhóm vấn đề)

### Giải pháp 1: Khắc phục triệt để lỗi CORS trên .NET 8 và Node.js Express

#### Trong .NET 8 Web API (`Program.cs`):
```csharp
var builder = WebApplication.CreateBuilder(args);

// Đăng ký chính sách CORS trước builder.Build()
builder.Services.AddCors(options =>
{
    options.AddPolicy("EnterpriseLocalCorsPolicy", policy =>
    {
        policy.WithOrigins("http://localhost:5173", "http://localhost:3000")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

var app = builder.Build();

// BẮT BUỘC: Đặt UseCors giữa UseRouting và UseAuthentication / UseAuthorization
app.UseRouting();
app.UseCors("EnterpriseLocalCorsPolicy");
app.UseAuthentication();
app.UseAuthorization();
```

#### Trong Node.js / Express (`app.js`):
```javascript
const cors = require('cors');
app.use(cors({
    origin: ['http://localhost:5173', 'http://localhost:3000'],
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true
}));
```

---

### Giải pháp 2: Xử lý triệt để kẹt Cache React/Vite và Lỗi Gradle Android

#### Đối với dự án React / Vite:
```powershell
# Dọn dẹp cache và cài đặt lại sạch sẽ
Remove-Item -Recurse -Force node_modules, package-lock.json
npm cache clean --force
npm install
npm run dev -- --force
```

#### Đối với Android Studio / Flutter:
1. Tạo tệp `android/local.properties` nếu chưa có:
   ```properties
   sdk.dir=C:\\Users\\Fat Chu Ai\\AppData\\Local\\Android\\Sdk
   ```
2. Dọn dẹp cache Gradle:
   ```powershell
   cd android
   .\gradlew clean --refresh-dependencies
   cd ..
   flutter clean
   flutter pub get
   ```
3. Chấp thuận toàn bộ giấy phép Android SDK:
   ```powershell
   flutter doctor --android-licenses
   ```

---

### Giải pháp 3: Khắc phục lỗi WordPress 502 & Elementor White Screen

#### Bước 1: Nâng giới hạn bộ nhớ PHP Memory Limit lên 512MB
Chỉnh sửa tệp `wp-config.php` (thêm vào trước dòng `/* That's all, stop editing! */`):
```php
define('WP_MEMORY_LIMIT', '512M');
define('WP_MAX_MEMORY_LIMIT', '512M');
```
Đồng thời cấu hình trong `/etc/php/8.2/fpm/php.ini`:
```ini
memory_limit = 512M
max_execution_time = 300
upload_max_filesize = 64M
post_max_size = 64M
```
Khởi động lại dịch vụ: `sudo systemctl restart php8.2-fpm && sudo systemctl restart nginx`.

#### Bước 2: Bật chế độ Safe Mode của Elementor để sửa lỗi White Screen
1. Vào trang Quản trị WordPress -> **Elementor** -> **Tools** (Công cụ).
2. Tại mục **Safe Mode**, chọn **Enable** -> Bấm Save Changes.
3. Chế độ Safe Mode sẽ cô lập Elementor khỏi các plugin xung đột (Theme/Addon), cho phép kỹ thuật viên mở lại trang và xác định plugin gây lỗi để gỡ bỏ.
4. Tái tạo lại tệp CSS của Elementor: Vào **Elementor** -> **Tools** -> **Regenerate Files & Data** -> Bấm **Regenerate Files**.

#### Bước 3: Cấu hình FluentSMTP chuẩn doanh nghiệp (Office 365 / Google Workspace)
1. Cài đặt plugin **FluentSMTP**.
2. Chọn kết nối **Microsoft (Outlook 365)** hoặc **Google Workspace**:
   - Sử dụng phương thức xác thực **OAuth 2.0 (API)** thay vì SMTP mật khẩu thuần.
   - Nếu dùng SMTP thường:
     * Máy chủ SMTP: `smtp.office365.com` (hoặc `smtp.gmail.com`).
     * Cổng: `587`.
     * Giao thức mã hóa: `STARTTLS` (TLS).
     * Mật khẩu: Sử dụng **Mật khẩu Ứng dụng (App Password)** 16 ký tự.
3. Bấm **Send Test Email** để kiểm tra log gửi thư thành công.

---

## Verification (Xác nhận kết quả)
1. **Kiểm tra CORS**: Gọi API từ giao diện React `localhost:5173` ➔ Nhận mã phản hồi `200 OK`, dữ liệu JSON trả về đầy đủ, không còn thông báo chặn CORS trong console.
2. **Kiểm tra Build Mobile**: Chạy `flutter run` hoặc mở Android Studio ➔ Trình giả lập (Emulator) khởi động mượt mà, ứng dụng nạp thành công (Hot Reload / HMR hoạt động tức thì).
3. **Kiểm tra Website**: Trang web WordPress tải trong < 1.5 giây, trang chỉnh sửa Elementor mở trong < 3 giây, công cụ FluentSMTP gửi email test trả về trạng thái `Success` với bản ghi SPF/DKIM hợp lệ.

## Prevention (Biện pháp phòng ngừa)
1. Trong môi trường phát triển phần mềm nội bộ, luôn tạo tệp `.env.example` và tài liệu hướng dẫn setup môi trường biến (`ANDROID_HOME`, `JAVA_HOME`) cho lập trình viên mới.
2. Thiết lập cơ chế sao lưu tự động hàng ngày (Daily Backup) cho website WordPress qua plugin UpdraftPlus lưu trữ ngoại vi (Google Drive / S3).
3. Sử dụng Git Hooks hoặc CI/CD pipeline kiểm tra linting và build test trước khi merge vào nhánh chính.

## Escalation
* Chuyển cấp **Level 3 (DevOps / Lead Software Architect)** nếu: Cơ sở dữ liệu bị deadlock nghiêm trọng, rò rỉ bộ nhớ (Memory Leak) trong ứng dụng Backend, hoặc website bị tấn công DDoS / chèn mã độc vào mã nguồn PHP.

## Risk Level
`Medium` (Ảnh hưởng đến tiến độ dự án của phòng phát triển và kênh truyền thông của công ty)

## Required Permission
* Lập trình viên: `Local Administrator trên máy dev`
* Website: `WordPress Administrator / Server Root Access via SSH`

## Related Documents
* `KB-SYS-2026-001`: Cấu hình Hạ tầng Local AI & Khởi chạy Backend FastAPI.
* `KB-NET-2026-001`: Quy trình Chẩn đoán Mạng Doanh nghiệp theo Mô hình 5 Tầng OSI.

## Tags
`React`, `Vite`, `CORS`, `.NET 8`, `Flutter`, `Android Studio`, `WordPress`, `Elementor`, `FluentSMTP`, `LiteSpeed`, `PHP Memory Limit`
