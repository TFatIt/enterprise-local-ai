# API.md

# Đặc tả RESTful API Enterprise Local AI Assistant

Tài liệu này quy định chuẩn thiết kế API, cấu trúc URL, phương thức xác thực (Authentication), định dạng JSON Request/Response và danh mục toàn bộ các endpoints trong hệ thống.

---

## 1. Quy ước Chung (Conventions & Standards)

* **Base URL**: `/api/v1`
* **Content-Type**: `application/json` (trừ upload file sử dụng `multipart/form-data`)
* **Xác thực**: HTTP Bearer Token qua Header: `Authorization: Bearer <JWT_ACCESS_TOKEN>`
* **Định dạng thời gian**: Chuẩn ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`)
* **Mã lỗi HTTP (HTTP Status Codes)**:
  - `200 OK`: Yêu cầu thành công.
  - `201 Created`: Tạo mới tài nguyên thành công.
  - `400 Bad Request`: Dữ liệu đầu vào không hợp lệ (Validation error).
  - `401 Unauthorized`: Chưa đăng nhập hoặc Token hết hạn/không hợp lệ.
  - `403 Forbidden`: Người dùng không có quyền truy cập tài nguyên (RBAC).
  - `404 Not Found`: Không tìm thấy tài nguyên.
  - `500 Internal Server Error`: Lỗi máy chủ cục bộ.

### Định dạng Phản hồi Chuẩn (Response Envelope)

**Thành công (Success Response):**
```json
{
  "success": true,
  "data": { ... },
  "message": "Thao tác thành công",
  "timestamp": "2026-09-05T00:00:00Z"
}
```

**Thất bại (Error Response):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email không đúng định dạng",
    "details": null
  },
  "timestamp": "2026-09-05T00:00:00Z"
}
```

---

## 2. Danh mục Endpoints

### 2.1. Module Xác thực (Authentication) - `/api/v1/auth`

| Phương thức | Đường dẫn | Phân quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Public | Đăng nhập bằng Email/Username & Mật khẩu, nhận JWT Token |
| `POST` | `/api/v1/auth/refresh` | Public | Làm mới Access Token thông qua Refresh Token |
| `GET` | `/api/v1/auth/me` | Authenticated | Lấy thông tin tài khoản, vai trò và phòng ban hiện tại |
| `POST` | `/api/v1/auth/logout` | Authenticated | Đăng xuất và vô hiệu hóa phiên làm việc |

#### Ví dụ `POST /api/v1/auth/login`
* **Request Body:**
```json
{
  "username_or_email": "admin@enterprise.local",
  "password": "SecurePassword123!"
}
```
* **Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "c3b9b46e-1d54-4a5f-9df9-34b7a13d80a1",
      "email": "admin@enterprise.local",
      "full_name": "System Administrator",
      "role": "SUPER_ADMIN",
      "department": "IT"
    }
  }
}
```

---

### 2.2. Module Quản trị Người dùng & Phòng ban - `/api/v1/users` & `/api/v1/departments`

| Phương thức | Đường dẫn | Phân quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users` | `SUPER_ADMIN` | Lấy danh sách tài khoản (hỗ trợ phân trang, lọc theo phòng ban, vai trò) |
| `POST` | `/api/v1/users` | `SUPER_ADMIN` | Tạo tài khoản nhân viên mới |
| `GET` | `/api/v1/users/{id}` | `SUPER_ADMIN` | Xem chi tiết thông tin một tài khoản |
| `PUT` | `/api/v1/users/{id}` | `SUPER_ADMIN` | Cập nhật thông tin tài khoản, đổi vai trò (Role), phòng ban |
| `DELETE` | `/api/v1/users/{id}` | `SUPER_ADMIN` | Khóa / Vô hiệu hóa tài khoản (`is_active = false`) |
| `GET` | `/api/v1/departments`| Authenticated | Lấy danh sách các phòng ban trong công ty |
| `POST` | `/api/v1/departments`| `SUPER_ADMIN` | Tạo mới phòng ban |

---

### 2.3. Module Quản lý Tài liệu - `/api/v1/documents`

| Phương thức | Đường dẫn | Phân quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/documents` | Authenticated | Danh sách tài liệu (lọc theo phòng ban, trạng thái indexing) |
| `POST` | `/api/v1/documents/upload` | `IT_ADMIN`, `SUPER_ADMIN` | Upload tệp tài liệu mới (`PDF`, `DOCX`, `TXT`) |
| `GET` | `/api/v1/documents/{id}` | Authenticated | Lấy chi tiết tài liệu và tiến độ Indexing |
| `POST` | `/api/v1/documents/{id}/reindex`| `IT_ADMIN`, `SUPER_ADMIN` | Yêu cầu trích xuất và nạp lại vector (Re-index) |
| `DELETE` | `/api/v1/documents/{id}` | `IT_ADMIN`, `SUPER_ADMIN` | Xóa tài liệu khỏi PostgreSQL và xóa vectors trong ChromaDB |

#### Ví dụ `POST /api/v1/documents/upload`
* **Content-Type**: `multipart/form-data`
* **Form Fields**:
  - `file`: binary data
  - `title`: "Quy trình kết nối VPN và xử lý sự cố mạng 2026"
  - `department_id`: 1
* **Response 201 Created:**
```json
{
  "success": true,
  "data": {
    "id": "e9b23f5b-6cf2-4411-b0e2-63bfaec98b09",
    "title": "Quy trình kết nối VPN và xử lý sự cố mạng 2026",
    "file_name": "vpn_troubleshooting_guide.pdf",
    "file_type": "PDF",
    "file_size": 245890,
    "status": "PROCESSING",
    "department_id": 1,
    "uploaded_at": "2026-09-05T00:05:00Z"
  }
}
```

---

### 2.4. Module AI Chat & RAG - `/api/v1/chat`

| Phương thức | Đường dẫn | Phân quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/chat/sessions` | Authenticated | Lấy danh sách các phiên trò chuyện của user |
| `POST` | `/api/v1/chat/sessions` | Authenticated | Khởi tạo phiên trò chuyện mới |
| `GET` | `/api/v1/chat/sessions/{id}/messages`| Authenticated | Lấy toàn bộ lịch sử tin nhắn trong phiên chat |
| `POST` | `/api/v1/chat/sessions/{id}/messages`| Authenticated | Gửi câu hỏi cho AI (thực thi RAG Pipeline và trả về câu trả lời + nguồn) |
| `DELETE` | `/api/v1/chat/sessions/{id}`| Authenticated | Xóa phiên trò chuyện |

#### Ví dụ `POST /api/v1/chat/sessions/{id}/messages`
* **Request Body:**
```json
{
  "question": "Tại sao máy tính của tôi không join được domain công ty?"
}
```
* **Response 200 OK:**
```json
{
  "success": true,
  "data": {
    "message_id": "8f31b26a-93a8-4e89-a5e2-2a911e3b0c55",
    "sender_type": "ASSISTANT",
    "content": "Máy tính có thể không gia nhập (join) được domain do các nguyên nhân phổ biến sau:\n1. **Cấu hình DNS**: Card mạng chưa trỏ DNS về IP của Domain Controller nội bộ.\n2. **Sai lệch thời gian**: Giờ trên máy tính chênh lệch quá 5 phút so với máy chủ Kerberos.\n3. **Quyền hạn**: Tài khoản của bạn chưa được cấp quyền thêm máy vào miền Active Directory.\n\nNếu đã kiểm tra các bước trên nhưng vẫn gặp lỗi, bạn có thể tạo IT Ticket để quản trị viên hỗ trợ trực tiếp.",
    "sources": [
      {
        "document_id": "e9b23f5b-6cf2-4411-b0e2-63bfaec98b09",
        "document_title": "Hướng dẫn cấu hình mạng & Active Directory.pdf",
        "file_name": "ad_network_guide.pdf",
        "page_number": 14,
        "similarity_score": 0.89,
        "snippet": "...khi client báo lỗi không tìm thấy domain controller, kiểm tra cấu hình DNS server trên card mạng IPv4..."
      }
    ],
    "suggest_ticket": false,
    "response_time_ms": 1420
  }
}
```

---

### 2.5. Module Quản lý IT Ticket - `/api/v1/tickets`

| Phương thức | Đường dẫn | Phân quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/tickets` | Authenticated | Danh sách ticket (Employee chỉ thấy ticket của mình; IT/Super Admin thấy toàn bộ) |
| `POST` | `/api/v1/tickets` | Authenticated | Tạo yêu cầu hỗ trợ IT mới (có thể liên kết từ `chat_session_id`) |
| `GET` | `/api/v1/tickets/{id}` | Authenticated | Xem chi tiết ticket và tiến độ giải quyết |
| `PATCH` | `/api/v1/tickets/{id}` | `IT_ADMIN`, `SUPER_ADMIN` | Cập nhật trạng thái (`status`), phân công (`assigned_to`), ghi chú giải pháp |
| `GET` | `/api/v1/tickets/{id}/comments`| Authenticated | Lấy danh sách trao đổi trong ticket |
| `POST` | `/api/v1/tickets/{id}/comments`| Authenticated | Đăng phản hồi / trao đổi vào ticket |

---

### 2.6. Module Bảng điều khiển Quản trị (Dashboard) - `/api/v1/dashboard`

| Phương thức | Đường dẫn | Phân quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/stats` | `IT_ADMIN`, `SUPER_ADMIN` | Thống kê tổng số: Người dùng, Tài liệu, Câu hỏi, Ticket, Tỷ lệ AI xử lý thành công |
| `GET` | `/api/v1/dashboard/charts`| `IT_ADMIN`, `SUPER_ADMIN` | Dữ liệu biểu đồ: Số câu hỏi theo ngày, Ticket theo nhóm sự cố, Top tài liệu tra cứu |
