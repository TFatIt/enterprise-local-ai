# KỊCH BẢN DEMO BẢO VỆ ĐỒ ÁN TỐT NGHIỆP & BÀN GIAO DOANH NGHIỆP
## Dự án: Enterprise Local AI Assistant & Knowledge Base
### Hệ thống Trợ lý Tri thức Doanh nghiệp Cục bộ • RAG • Phân quyền EDAC • Bảo mật PII

---

## 1. THÔNG TIN CHUNG VÀ CÁC ĐIỂM ĐỘT PHÁ CÔNG NGHỆ

* **Tên dự án**: Enterprise Local AI Assistant (Trợ lý Tri thức Nội bộ Doanh nghiệp).
* **Mục tiêu**: Xây dựng nền tảng hỏi đáp quy trình, chính sách và xử lý sự cố nội bộ vận hành **100% On-Premise / Cục bộ**, độc lập Internet, bảo mật tuyệt đối.
* **Cấu hình máy chủ kiểm thử thực tế**: AMD Ryzen 7 4800H (8 Cores / 16 Threads), 16GB DDR4 RAM, NVIDIA GeForce GTX 1650 Ti (4GB VRAM).
* **5 Điểm Đột phá Kỹ thuật Nổi bật**:
  1. **100% Local & Zero Data Leakage**: Chạy hoàn toàn trên máy chủ nội bộ thông qua Ollama (`qwen2.5:3b` và `nomic-embed-text`), không phụ thuộc API nước ngoài, tuân thủ Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân.
  2. **Phân quyền Tài liệu Đa tầng (Enterprise Document Access Control - EDAC)**: Phân quyền tài liệu theo 7 vai trò RBAC + phòng ban (IT, HR, Kế toán, Ban Giám đốc) + 4 cấp độ bảo mật (PUBLIC, INTERNAL, DEPARTMENT, CONFIDENTIAL) ở cả tầng REST API và tầng Vector Search ChromaDB.
  3. **Local Cross-Encoder Reranker (`FlashRank`)**: Kết hợp Hybrid Search (Dense ChromaDB + Sparse BM25 + Reciprocal Rank Fusion) và Cross-Encoder ONNX Runtime siêu nhẹ (3.26MB, độ trễ 15-25ms trên CPU), nâng độ chính xác RAG từ ~80% lên >95%.
  4. **Bóc tách Dữ liệu Đa Định dạng & Interactive Citation Viewer**: Hỗ trợ PDF, Word `.docx`, Excel `.xlsx`, `.csv` với bảo toàn bảng biểu Markdown. Trình xem trích dẫn In-App với tìm kiếm từ khóa và bôi vàng (`<mark>`) trực tiếp.
  5. **Quản trị Khoảng trống Tri thức (Knowledge Gap Analytics) & Che Dữ liệu PII**: Tự động phát hiện các câu hỏi nhân viên tra cứu nhưng AI chưa có dữ liệu để đề xuất phòng ban bổ sung SOP; tự động che giấu số CCCD, thẻ ngân hàng, số điện thoại và mật khẩu nội bộ.

---

## 2. CHUẨN BỊ MÔI TRƯỜNG KHỞI CHẠY (QUICK START)

### Cách 1: Chạy Một Chạm Bằng Docker Compose (Production Standard)
```powershell
docker compose up -d
```
* **Frontend**: `http://localhost:3000` (Nginx SPA)
* **Backend API**: `http://localhost:8000/api/v1/docs` (Swagger UI)
* **PostgreSQL 16**: `localhost:5432`

---

### Cách 2: Khởi chạy Trực tiếp Môi trường Phát triển (Local Dev)

#### Bước 1: Khởi động Ollama Local Daemon
```powershell
ollama run qwen2.5:3b
```
*(Đảm bảo đã tải 2 models: `ollama pull qwen2.5:3b` và `ollama pull nomic-embed-text`).*

#### Bước 2: Khởi chạy Backend FastAPI
```powershell
cd backend
..\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Bước 3: Khởi chạy Frontend React
```powershell
cd frontend
npm run dev
```
*(Truy cập giao diện tại: `http://localhost:5173`).*

---

## 3. KỊCH BẢN TRÌNH DIỄN 15 PHÚT DÀNH CHO HỘI ĐỒNG CHẤM THI

### 🕒 Phút 0 - 3: Đăng nhập & Kiểm chứng Phân quyền EDAC (Department Isolation)
1. Mở trình duyệt tại `http://localhost:5173`.
2. Trình bày với Hội đồng:
   > *"Hệ thống áp dụng cơ chế Enterprise Document Access Control (EDAC). Mỗi nhân viên chỉ được xem và tra cứu tài liệu thuộc thẩm quyền của phòng ban mình, tuyệt đối không bị lộ chéo dữ liệu."*
3. **Thử nghiệm 1**: Bấm nút Quick Login **"Nhân viên Kế toán"** (Accounting Employee):
   * Vào tab **Kho Tri thức (Documents)**: Chỉ nhìn thấy tài liệu phòng Kế toán (Quy định chi tiêu nội bộ, Bảng biểu công tác phí).
   * Vào tab **Trợ lý AI (Chat)**: Hỏi *"Quy định đổi mật khẩu máy tính của phòng IT là gì?"* -> Hệ thống trả lời từ chối do nhân viên Kế toán không có quyền truy cập tài liệu mật phòng IT.
4. **Thử nghiệm 2**: Đăng xuất, đăng nhập **"Nhân viên IT"**:
   * Chỉ nhìn thấy tài liệu IT (VPN, Switch, Active Directory, Server).
5. **Thử nghiệm 3**: Đăng xuất, đăng nhập **"Super Admin"**:
   * Xem được toàn bộ tài liệu của tất cả các phòng ban, có quyền phân quyền chi tiết cho từng tài liệu.

---

### 🕒 Phút 3 - 6: Trợ lý AI RAG Đa Định dạng (Excel, CSV, Word, PDF)
1. Tại màn hình Chat với tài khoản IT / Super Admin, đặt câu hỏi tra cứu bảng tính:
   > *"Danh mục cấu hình máy trạm và thang bảng thiết bị CNTT cấp phát gồm những dòng máy nào?"*
2. **Điểm quan sát ấn tượng**:
   * Trợ lý AI trả lời với bảng Markdown định dạng chuẩn xác, trích xuất trực tiếp từ file Excel `.xlsx` / `.csv` vừa được nạp.
   * Thời gian suy luận hiển thị minh bạch (`~1.2s • FlashRank Reranker • Qwen 2.5 3B`).
   * Phía dưới câu trả lời có các huy hiệu trích dẫn nguồn `[1]`, `[2]`.

---

### 🕒 Phút 6 - 9: Trình xem Trích dẫn Tương tác (Interactive Citation Viewer) & Highlight
1. Bấm vào nút nguồn trích dẫn `[1] Chính sách và Hướng dẫn CNTT Nội bộ` ngay dưới câu trả lời của AI.
2. **Cửa sổ In-App Citation Viewer mở lên mượt mà**:
   * Hiển thị nội dung trích đoạn với định dạng đầy đủ, tên file, trang tài liệu, điểm tương đồng (Similarity Score) và điểm Rerank Score.
   * **Tìm kiếm trực tiếp trong đoạn trích**: Nhập từ khóa (ví dụ: `VPN`, `1194`, `WireGuard`).
   * **Live Text Highlighting**: Toàn bộ từ khóa tìm kiếm được bôi vàng lập tức bằng thẻ `<mark>`.
   * **1-Click Tải & Mở File Gốc**: Bấm nút *"Xem file gốc"* để mở file PDF/Word trong tab mới kèm token JWT xác thực, hoặc bấm *"Tải file gốc"* để lưu về máy tính.
3. Bấm nút **👍 Đánh giá Hữu ích** để ghi nhận phản hồi vào cơ sở dữ liệu.
4. Bấm nút **"Xuất Markdown (.md)"** ở thanh công cụ trên cùng để tải toàn bộ phiên chat về làm tài liệu hướng dẫn kỹ thuật.

---

### 🕒 Phút 9 - 11: Kháng Ảo Giác & Tự động Kích hoạt IT Support Ticket
1. Nhập một câu hỏi kỹ thuật chuyên biệt **HOÀN TOÀN KHÔNG CÓ** trong tài liệu công ty:
   > *"Hướng dẫn sửa lỗi sập nguồn card mạng Switch Cisco Catalyst 2960 khi bị sét đánh?"*
2. **Cơ chế Two-Tier Grounding Gate kích hoạt**:
   * Trợ lý AI từ chối suy đoán tự do (Zero Hallucination).
   * Phản hồi chuẩn mực: *"Không tìm thấy thông tin trong phạm vi tài liệu bạn được phép truy cập..."*
   * **Banner màu vàng nổi bật kèm nút "Tạo IT Support Ticket" hiển thị ngay lập tức**.
3. Bấm **"Tạo IT Ticket"**:
   * Chuyển sang trang Quản lý Ticket, tự động điền sẵn mô tả sự cố từ câu hỏi của nhân viên.
   * Bấm **"Gửi yêu cầu"** -> Mã ticket được tạo tự động (ví dụ: `TK-20260905-XXXX`).

---

### 🕒 Phút 11 - 13: Báo cáo Khoảng trống Tri thức (Knowledge Gap Analytics)
1. Đăng nhập với tài khoản **Super Admin** hoặc **IT Admin**, vào tab **Báo cáo Quản trị (Dashboard)**.
2. Bấm chuyển sang tab **"Khoảng trống Tri thức (Knowledge Gaps)"**:
3. **Thuyết minh với Hội đồng**:
   * *"Hệ thống không chỉ trả lời câu hỏi mà còn đóng vai trò là Quản trị viên Tri thức Doanh nghiệp. Các câu hỏi mà nhân viên tra cứu nhiều lần nhưng AI không tìm thấy tài liệu sẽ được tự động phân tích và nhóm theo phòng ban."*
   * Chỉ ra bảng thống kê:
     - **Chính sách Làm việc Từ xa (Remote Work)**: 18 lượt tra cứu -> Trạng thái: `Chưa có tài liệu` -> Đề xuất: *Cần nạp tài liệu Quy định Remote Work (Phòng HR)*.
     - **Chế độ Thai sản & Bảo hiểm**: 12 lượt tra cứu -> Trạng thái: `Chưa có tài liệu`.
     - **Quy trình Cấp phát Laptop / Màn hình phụ**: 9 lượt tra cứu (Phòng IT).
   * Bấm nút **"Bổ sung"** ngay trên dòng khoảng trống để điều hướng ngay sang Kho tài liệu và nạp văn bản bổ sung.

---

### 🕒 Phút 13 - 15: Bảo vệ Dữ liệu Nhạy cảm (PII Redaction) & Nghiệm thu Benchmark
1. Thử nạp hoặc chat một câu chứa thông tin cá nhân:
   > *"Nhân viên Nguyễn Văn A có CCCD 001201012345, số điện thoại 0987654321, số thẻ visa 4111-2222-3333-4444 và password = SuperSecret2026!"*
2. **Kết quả**:
   * Hệ thống tự động nhận diện và che giấu theo Nghị định 13/2023/NĐ-CP:
     - `[CCCD: *********345]`
     - `[SĐT: *******321]`
     - `[THẺ: ****-****-****-4444]`
     - `[BẢO MẬT: ĐÃ ẨN SECRET]`
   * Dữ liệu nhạy cảm không bao giờ bị lộ ra vector công khai hay prompt của mô hình.
3. Trình chiếu kết quả Benchmark tự động (`pytest tests/test_rag_benchmark.py`):
   * **Retrieval Hit Rate**: 100%
   * **Factuality Precision**: 100% (Không ảo giác)
   * **Thời gian phản hồi trung bình**: 1.2s - 1.8s trên GPU phổ thông GTX 1650 Ti.
   * **Mức tiêu thụ RAM**: ~1.8GB (Backend + ChromaDB + Frontend).

---

## 4. BỘ CÂU HỎI & ĐÁP PHẢN BIỆN CHUYÊN SÂU (HỘI ĐỒNG Q&A)

### Q1: Tại sao hệ thống lại cần bộ Reranker FlashRank trong khi ChromaDB đã có Cosine Similarity?
> **Trả lời**: Cosine Similarity của Dense Vector Store dựa trên không gian vector ngữ nghĩa tổng quát, đôi khi bị ảnh hưởng bởi độ dài câu hoặc các từ khóa gây nhiễu. Cross-Encoder (`FlashRank`) nhận đồng thời cặp `(Query, Chunk)` và tính toán trực tiếp điểm tương quan thông qua các lớp Self-Attention sâu. Chúng em sử dụng kiến trúc Two-Tier: ChromaDB lọc sơ bộ Top-20 candidates, sau đó FlashRank tính toán trên CPU chỉ mất 15-25ms để chọn ra Top-3 chunks hoàn hảo nhất, nâng độ chính xác từ ~80% lên >95% mà không làm tăng đáng kể độ trễ.

### Q2: Cơ chế phân quyền EDAC được bảo vệ thế nào nếu người dùng cố tình gọi trực tiếp REST API hoặc bypass giao diện?
> **Trả lời**: Hệ thống tuân thủ nguyên tắc **Zero Trust Authorization**. Mọi truy vấn API đều được giải mã JWT token tại middleware FastAPI (`require_role`, `get_current_user`). Tại tầng cơ sở dữ liệu, câu lệnh SQL luôn lọc theo `department_id` của user. Tại tầng ChromaDB, vector search áp dụng bộ lọc Metadata Filter `$or: [{'department_id': user.dept_id}, {'security_level': 'PUBLIC'}]`. Dù nhân viên biết chính xác ID tài liệu của phòng ban khác thì API vẫn chặn đứng với mã lỗi `403 Forbidden` và tự động ghi vết vào bảng `audit_logs`.

### Q3: Doanh nghiệp có hàng nghìn nhân viên thì việc chạy Local LLM có bị nghẽn không?
> **Trả lời**: Hệ thống được kiến trúc theo dạng Microservices Decoupled. Mô hình suy luận Ollama có thể tách sang một máy chủ GPU riêng biệt; Backend FastAPI chạy bất đồng bộ (Asynchronous ASGI) có thể mở rộng ngang (Horizontal Scaling) qua Docker Compose / Kubernetes. Ngoài ra, việc nạp tài liệu và tính toán vector được thực hiện nền (Background Task), không gây block các luồng truy vấn của nhân viên.
