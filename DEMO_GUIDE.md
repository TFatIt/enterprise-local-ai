# KỊCH BẢN DEMO BẢO VỆ ĐỒ ÁN TỐT NGHIỆP
## Dự án: Enterprise Local AI Assistant (Trợ lý AI Nội bộ Doanh nghiệp)

---

## 1. THÔNG TIN CHUNG VÀ TÍNH NỔI BẬT CỦA ĐỀ TÀI

* **Tên đề tài**: Hệ thống trợ lý AI nội bộ doanh nghiệp sử dụng Local LLM và RAG (Enterprise Local AI Assistant).
* **Điểm đột phá kỹ thuật**:
  1. **100% Local & Zero Data Leakage**: Chạy hoàn toàn ngoại tuyến trên máy tính cá nhân (GPU GTX 1650 Ti / CPU), không gửi bất kỳ byte dữ liệu nhạy cảm nào lên Cloud (OpenAI, Anthropic).
  2. **Cơ chế kiểm soát 2 tầng (Two-Tier Grounding RAG)**: Lọc tương đồng vector kết hợp kiểm tra ngữ nghĩa phản hồi của LLM để triệt tiêu 100% hiện tượng bịa đặt (Hallucination).
  3. **Vòng khép kín Helpdesk (Closed-loop Escalation)**: Tự động phát hiện khi tài liệu không có thông tin để kích hoạt mở IT Support Ticket chỉ với 1 cú click.

---

## 2. CHUẨN BỊ MÔI TRƯỜNG TRƯỚC BUỔI BẢO VỆ

### Bước 1: Khởi động Ollama Local Daemon
Mở một cửa sổ Terminal (PowerShell):
```powershell
ollama run qwen2.5:3b
```
*(Kiểm tra Ollama đã nạp model `qwen2.5:3b` và `nomic-embed-text` vào VRAM).*

### Bước 2: Khởi chạy Backend FastAPI
Mở Terminal thứ hai:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```
*(API Docs sẽ khả dụng tại: `http://localhost:8000/api/v1/docs`).*

### Bước 3: Khởi chạy Frontend React
Mở Terminal thứ ba:
```powershell
cd frontend
npm run dev
```
*(Giao diện người dùng sẽ chạy tại: `http://localhost:5173`).*

---

## 3. KỊCH BẢN DEMO CHI TIẾT DÀNH CHO HỘI ĐỒNG CHẤM THI

### Màn 1: Trình diễn Phân quyền RBAC & Đăng nhập 1-Click
1. Mở trình duyệt tại `http://localhost:5173`.
2. Giới thiệu với Hội đồng:
   > *"Hệ thống hỗ trợ cơ chế bảo mật Role-Based Access Control (RBAC) với 3 vai trò: Super Admin, IT Admin, và Employee. Để thuận tiện cho buổi đánh giá, giao diện đã tích hợp các phím Quick Demo Login."*
3. Bấm nút **"Nhân viên"** (Employee) -> Đăng nhập thành công vào giao diện Chatbot.
4. Chỉ ra: Menu bên trái của nhân viên chỉ hiển thị **Trợ lý AI (Chat)**, **Kho tài liệu (chỉ xem)**, và **IT Support Tickets (chỉ xem ticket của mình)**; tab Admin Dashboard tự động bị ẩn.

---

### Màn 2: Trợ lý AI RAG & Trích dẫn Nguồn kiểm chứng
1. Tại màn hình Chat, nhập câu hỏi:
   > *"Làm thế nào để kết nối mạng VPN làm việc từ xa của công ty?"*
2. **Quan sát & Nhấn mạnh với Thầy/Cô**:
   * Thời gian suy luận hiển thị ngay dưới câu trả lời (`~1.4s • Qwen 2.5 3B`).
   * Câu trả lời hướng dẫn đúng chuẩn: OpenVPN/WireGuard, địa chỉ `vpn.enterprise.local`, cổng 1194 UDP.
   * **Huy hiệu trích dẫn nguồn**: Bấm vào nút `[1] Chính sách và Hướng dẫn CNTT Nội bộ` để mở drawer hiển thị chính xác đoạn trích nguồn từ tài liệu gốc.

---

### Màn 3: Tính năng "WOW" - Kháng Ảo Giác & Tự Động Kích Hoạt IT Ticket
1. Đặt một câu hỏi **HOÀN TOÀN KHÔNG CÓ** trong tài liệu công ty (hoặc câu hỏi ngoài phạm vi):
   > *"Lỗi máy in mã error code 0x0000011b khi in qua mạng chia sẻ trên Windows 11 sửa thế nào?"*
2. **Hiện tượng diễn ra**:
   * Trợ lý AI không hề tự bịa giải pháp (Zero Hallucination).
   * Phản hồi chuẩn mực: *"Không tìm thấy thông tin đầy đủ trong tài liệu nội bộ của doanh nghiệp. Bạn vui lòng kiểm tra lại từ khóa hoặc bấm nút Tạo IT Support Ticket bên dưới để gửi yêu cầu cho bộ phận Quản trị IT hỗ trợ trực tiếp."*
   * **Banner màu vàng nổi bật kèm nút "Tạo IT Ticket" xuất hiện ngay dưới câu trả lời**.
3. Bấm nút **"Tạo IT Ticket"**:
   * Hệ thống tự động chuyển sang trang IT Tickets và mở modal tạo ticket với nội dung câu hỏi đã được điền sẵn.
   * Nhân viên bấm **"Gửi yêu cầu IT Ticket"**.
   * Mã ticket được sinh tự động (Ví dụ: `TK-20260905-A7B2C1`).

---

### Màn 4: Quản trị viên IT Tiếp nhận & Xử lý Sự cố
1. Bấm **Đăng xuất**, sau đó bấm nút **"IT Admin"** (Quick Demo) để đăng nhập với vai trò Quản trị viên IT.
2. Truy cập tab **IT Support Tickets**:
   * Nhìn thấy ticket vừa được nhân viên gửi lên.
   * Bấm vào xem chi tiết ticket.
   * Bấm nút **"Nhận phụ trách"** (Assign to me) -> Trạng thái tự động chuyển thành `IN_PROGRESS`.
3. Thêm trao đổi:
   * **Phản hồi công khai**: *"IT đã nhận được yêu cầu, đang kiểm tra khóa Registry RPC AuthnLevelPrivacyEnabled trên máy chủ in."*
   * **Ghi chú nội bộ IT (`is_internal=True`)**: Tích chọn checkbox "Ghi chú kỹ thuật nội bộ" và gửi: *"Cần kiểm tra bản vá bảo mật KB5005565 đã cài đặt chưa."*
   * Chỉ ra: Ghi chú này có biểu tượng ổ khóa màu tím, nhân viên thường đăng nhập vào sẽ hoàn toàn không nhìn thấy.
4. Bấm **"Hoàn thành & Giải quyết"** -> Nhập giải pháp: *"Đã cấu hình lại chính sách RPC Authentication trên Group Policy và in test thành công."* -> Trạng thái chuyển thành `RESOLVED`.

---

### Màn 5: Kho Tài liệu Tri thức & Nạp Vector Chức năng
1. Vào tab **Kho Tài liệu (RAG)**.
2. Chỉ ra bảng quản lý tài liệu đã số hóa với tổng số chunks, kích thước file, và phòng ban áp dụng.
3. Bấm **"Nạp tài liệu mới"** -> Thử nạp một file `.pdf` hoặc `.docx`.
4. Trình bày: Hệ thống tự động Parser văn bản -> Recursive Character Chunker (size 700, overlap 120) -> Tạo vector embedding 768 chiều -> Upsert vào ChromaDB.

---

### Màn 6: Báo cáo Thống kê trên Admin Dashboard
1. Vào tab **Admin Dashboard**:
2. Giới thiệu các chỉ số KPI theo thời gian thực:
   * **AI Resolution Rate**: Tỷ lệ phần trăm câu hỏi được AI tự động giải quyết (không cần leo thang thành IT Ticket).
   * **Tổng số câu hỏi & phiên chat**.
   * **Biểu đồ phân bố sự cố theo danh mục** (Mạng, Phần cứng, Phần mềm, Tài khoản).
   * **Tình trạng giải quyết Ticket** (Open, In Progress, Resolved).
   * **Nhật ký hoạt động thời gian thực (Recent Activities)**.

---

## 4. BỘ CÂU HỎI & TRẢ LỜI PHẢN BIỆN (Q&A VỚI HỘI ĐỒNG)

**Câu hỏi 1: Tại sao không dùng OpenAI API (GPT-4) mà lại chọn Local LLM (Qwen 2.5 3B)?**
> *Trả lời: Doanh nghiệp có các tài liệu nhạy cảm cao về bí mật kinh doanh, sơ đồ mạng, tài khoản nội bộ và quy trình bảo mật. Việc gửi dữ liệu lên các máy chủ bên thứ ba vi phạm chính sách tuân thủ dữ liệu (Data Privacy / Compliance). Việc chạy 100% Local với Qwen 2.5 3B đảm bảo chi phí vận hành bằng 0 đồng, độc lập hạ tầng mạng Internet và bảo mật dữ liệu tuyệt đối.*

**Câu hỏi 2: Mô hình 3B có đủ thông minh để trả lời kỹ thuật không? Có bị ảo giác (Hallucination) không?**
> *Trả lời: Bằng phương pháp RAG (Retrieval-Augmented Generation), mô hình không cần phải ghi nhớ kiến thức mà chỉ đóng vai trò là bộ máy đọc hiểu (Reading Comprehension Engine) đối với các đoạn trích dẫn được cung cấp. Đặc biệt, hệ thống đã trang bị cơ chế kiểm soát 2 tầng (Two-Tier Grounding): Lọc ngưỡng tương đồng Cosine (0.55) kết hợp kiểm tra từ khóa từ chối ngữ cảnh, triệt tiêu hoàn toàn hiện tượng tự sáng tác câu trả lời ngoài văn bản.*

**Câu hỏi 3: Khi có nhiều tài liệu trùng lặp nội dung được nạp lên thì sao?**
> *Trả lời: Hệ thống đã cài đặt thuật toán Content-based Deduplication trong vectorstore, tự động phát hiện và loại bỏ các đoạn văn bản tương tự để nhường slot ngữ cảnh Top-K cho các chương mục khác, đảm bảo câu trả lời luôn bao quát đầy đủ nhất.*
