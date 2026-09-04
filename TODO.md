# TODO.md

# Lộ trình Phát triển Dự án (15 Phases Tracker)

Bảng theo dõi tiến độ chi tiết từng giai đoạn của đồ án tốt nghiệp **Enterprise Local AI Assistant**.

---

## 📌 Tổng quan Trạng thái (Project Status Overview)

* **Giai đoạn Hiện tại**: **Hoàn thành toàn bộ 19/19 Phase (100% Completed & Verified)**
* **Trạng thái Hệ thống**: Enterprise-Grade & 100% Local (59/59 Tests Passed, Zero Build Errors)
* **Môi trường Triển khai**: Localhost (Dev Server) & Docker Compose (Production Ready)

---

## 🚀 Danh mục 15 Giai đoạn Phát triển (Phases)

### ✅ Phase 1: Project Setup & Architecture Documentation (HOÀN THÀNH)
- [x] Khởi tạo Master Technical Documentation (`README.md`, `ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `RAG.md`, `AI_RULES.md`, `TODO.md`).
- [x] Thiết lập cấu trúc thư mục dự án (`backend/`, `frontend/`, `documents/`, `tests/`, `docker/`).
- [x] Thiết lập file cấu hình môi trường mẫu (`backend/.env.example`, `.gitignore`).
- [x] Tạo file dependencies `backend/requirements.txt` và entrypoint `backend/app/main.py` với health check.

---

### ✅ Phase 2: Database Schema & Migration Setup (HOÀN THÀNH)
- [x] Cài đặt SQLAlchemy 2.0 và cấu hình Database Session (`app/db/session.py`, `app/db/base.py`).
- [x] Khởi tạo 10 ORM Models: `Role`, `Department`, `User`, `Document`, `DocumentChunk`, `ChatSession`, `ChatMessage`, `Ticket`, `TicketComment`, `AuditLog`.
- [x] Viết tiện ích băm mật khẩu bảo mật `app/core/security.py` (Bcrypt).
- [x] Viết script khởi tạo cơ sở dữ liệu mẫu (`app/db/seed.py`: Super Admin, IT Admin, Employee, Departments IT/HR/Finance).
- [x] Tạo script tự động sinh bảng `app/db/init_db.py` và bộ test kiểm thử quan hệ dữ liệu `tests/test_database.py`.

---

### ✅ Phase 3: Authentication & Security (HOÀN THÀNH)
- [x] Viết module mã hóa mật khẩu an toàn (`bcrypt`).
- [x] Xây dựng tiện ích tạo và giải mã JWT Token (`create_access_token`, `create_refresh_token`, `decode_token`).
- [x] Viết API `/api/v1/auth/login`, `/api/v1/auth/me`, `/api/v1/auth/refresh`, `/api/v1/auth/logout`.
- [x] Xây dựng FastAPI Dependency `get_current_user`, `get_current_active_user`, và `require_role`.
- [x] Viết 9 unit tests kiểm thử luồng đăng nhập, bảo vệ endpoint và tính hợp lệ của token (`tests/test_auth.py`).

---

### ✅ Phase 4: User Management & RBAC (HOÀN THÀNH)
- [x] Xây dựng Dependency phân quyền theo vai trò (`require_role(["SUPER_ADMIN"])`, v.v.).
- [x] Viết CRUD API quản lý người dùng `/api/v1/users` (Super Admin).
- [x] Viết CRUD API quản lý phòng ban `/api/v1/departments` và vai trò.
- [x] Viết 7 unit tests kiểm thử phân quyền RBAC (chặn Employee và IT Admin truy cập tài nguyên User Management với lỗi 403 Forbidden).

---

### ✅ Phase 5: Document Management (HOÀN THÀNH)
- [x] Cấu hình lưu trữ tệp tin tải lên (`uploads/`) với UUID hashing chống trùng lặp và chống path traversal.
- [x] Viết API upload tài liệu `/api/v1/documents/upload` hỗ trợ PDF, DOCX, TXT.
- [x] Kiểm tra dung lượng tệp (Max 25MB) và kiểm tra định dạng an toàn.
- [x] Quản lý trạng thái tài liệu (`UPLOADED`, `PROCESSING`, `INDEXED`, `FAILED`).
- [x] Viết API lấy danh sách, xem chi tiết và xóa tài liệu có cascade.

---

### ✅ Phase 6: Document Processing (HOÀN THÀNH)
- [x] Viết Parser trích xuất văn bản từ PDF (`pypdf`), DOCX (`python-docx`), TXT (`app/rag/parser.py`).
- [x] Viết module làm sạch văn bản (loại bỏ ký tự điều khiển rác, chuẩn hóa khoảng trắng).
- [x] Xây dựng bộ chia đoạn văn bản (`RecursiveCharacterChunker`) với Chunk size 700 và Overlap 120 (`app/rag/chunker.py`).
- [x] Lưu các chunks và metadata tương ứng (tên tài liệu, số trang, chunk index) vào bảng `document_chunks`.
- [x] Viết unit tests kiểm thử trọn vẹn luồng upload, bóc tách và phân đoạn (`tests/test_documents.py`).

---

### ✅ Phase 7: Embedding & Vector Database (ChromaDB) (HOÀN THÀNH)
- [x] Khởi tạo ChromaDB client cục bộ với Persistent Storage (`app/rag/vectorstore.py`).
- [x] Viết service gọi Ollama Embedding (`nomic-embed-text`) sinh vector 768 chiều (`app/rag/embeddings.py`).
- [x] Nạp vector và metadata tương ứng vào ChromaDB collection `enterprise_knowledge_base`.
- [x] Viết hàm tìm kiếm tương đồng Cosine Similarity Search với Top-K.

---

### ✅ Phase 8: Local LLM Integration (Ollama + Qwen) (HOÀN THÀNH)
- [x] Xây dựng Ollama Client gọi trực tiếp API `http://localhost:11434/api/generate` (`app/rag/llm.py`).
- [x] Cấu hình tham số sinh văn bản chuẩn mực (Temperature: 0.1, Top-P: 0.9, num_ctx: 4096).
- [x] Kiểm tra thực tế: Qwen 2.5 3B phản hồi siêu tốc (~1.2s) trên GPU GTX 1650 Ti.

---

### ✅ Phase 9: Core RAG Pipeline (HOÀN THÀNH)
- [x] Kết hợp trọn vẹn luồng: User Question -> Query Embedding -> Chroma Search -> Filter -> Prompt Builder -> Qwen LLM -> Answer Parser (`app/rag/pipeline.py`).
- [x] Triển khai cơ chế kiểm soát 2 tầng (Two-Tier Grounding): Lọc theo similarity threshold + phát hiện LLM từ chối ngữ cảnh khi ngoài phạm vi.
- [x] Triển khai định dạng trích dẫn nguồn chuẩn (`sources` array) đính kèm câu trả lời.
- [x] Viết 5 unit tests kiểm thử pipeline RAG (`tests/test_rag_pipeline.py`).

---

### ✅ Phase 10: AI Chat System (HOÀN THÀNH)
- [x] Xây dựng API quản lý phiên chat `/api/v1/chat/sessions`.
- [x] Xây dựng API gửi tin nhắn và nhận câu trả lời RAG `/api/v1/chat/sessions/{id}/messages`.
- [x] Lưu vết toàn bộ lịch sử hỏi đáp và thời gian phản hồi (response_time_ms).
- [x] Tự động đổi tên phiên chat theo câu hỏi đầu tiên.
- [x] Viết 6 unit tests kiểm thử toàn bộ API Chat (`tests/test_chat.py`).

---

### ✅ Phase 11: IT Ticket System (HOÀN THÀNH)
- [x] Xây dựng API tạo Ticket tự động từ chat hoặc nhân viên tự tạo `/api/v1/tickets`.
- [x] Tự động sinh mã Ticket chuẩn `TK-YYYYMMDD-XXXX` duy nhất.
- [x] Xây dựng API phân công IT Admin và cập nhật trạng thái vòng đời ticket (`OPEN` -> `IN_PROGRESS` -> `RESOLVED` -> `CLOSED`).
- [x] Hỗ trợ trao đổi bình luận công khai và ghi chú kỹ thuật nội bộ (`is_internal=True`).
- [x] Đổi trạng thái và ghi chú giải pháp kỹ thuật (`resolution_notes`) khi hoàn tất.
- [x] Viết 5 unit tests kiểm thử phân quyền RBAC và vòng đời Ticket (`tests/test_tickets.py`).

---

### ✅ Phase 12: Admin Dashboard & Analytics (HOÀN THÀNH)
- [x] Xây dựng API thống kê tổng quan: Users, Departments, Documents, Chunks, Questions, Tickets, AI Resolution Rate (`/api/v1/dashboard/stats`).
- [x] Xây dựng dữ liệu phân bố sự cố IT theo danh mục, trạng thái, và độ ưu tiên.
- [x] Cung cấp danh sách 10 hoạt động gần nhất của hệ thống (Recent Activities).
- [x] Phân quyền chặt chẽ: Chỉ `SUPER_ADMIN` và `IT_ADMIN` được phép truy cập dashboard.
- [x] Viết 4 unit tests kiểm thử bảo mật và độ chính xác của chỉ số thống kê (`tests/test_dashboard.py`).

---

### ✅ Phase 13: End-to-End Testing & RAG Benchmark (HOÀN THÀNH)
- [x] Tạo bộ câu hỏi mẫu kỹ thuật thực tế (Ground-truth Test Suite: VPN OpenVPN/WireGuard, Password Policy 8 ký tự/90 ngày, Active Directory DNS 192.168.1.10, Printer HP LaserJet 192.168.1.50).
- [x] Nâng cấp giải thuật Content Deduplication trong `ChromaVectorStore.similarity_search` chống tình trạng trùng lặp chunk chiếm dụng top-K context.
- [x] Kiểm chứng thành công: Độ chính xác tìm kiếm (Retrieval Hit Rate 100%), Tính xác thực của câu trả lời Qwen 2.5 3B, Tỷ lệ trích dẫn đúng nguồn, và Cơ chế từ chối ảo giác 100% đối với câu hỏi ngoài ngữ cảnh.
- [x] Viết và hoàn tất 5 bài test benchmark thực nghiệm (`tests/test_rag_benchmark.py`).

---

### ✅ Phase 14: Frontend Development (React + TypeScript + Vite + Tailwind) (HOÀN THÀNH)
- [x] Khởi tạo ứng dụng React với Vite, TypeScript và cấu hình Tailwind CSS 3.4 (`frontend/`).
- [x] Xây dựng màn hình Đăng nhập (Login) kèm tính năng Quick Demo Login 1-click cho Super Admin, IT Admin, Employee.
- [x] Xây dựng màn hình Chat AI chuyên nghiệp (Hiển thị tin nhắn, Response time ms, Source Badges, xem chi tiết trích dẫn, và Nút tự động chuyển tiếp sang IT Support Ticket khi AI từ chối ngữ cảnh).
- [x] Xây dựng màn hình Quản lý Kho tài liệu RAG (Upload kéo thả, kiểm soát phân quyền RBAC, theo dõi tiến trình số hóa & Vector Chunks).
- [x] Xây dựng màn hình IT Support Tickets (Lọc theo trạng thái, modal trao đổi bình luận công khai và ghi chú kỹ thuật nội bộ `is_internal`, điều phối phân công và giải pháp khắc phục).
- [x] Xây dựng Admin Dashboard với chỉ số KPI (AI Resolution Rate, Questions, Tickets, Chunks) và biểu đồ phân tích xu hướng.
- [x] Đóng gói thành công bản build production (`npm run build` không lỗi).

---

### ✅ Phase 15: Docker Compose, Packaging & Defense Guide (HOÀN THÀNH)
- [x] Viết `backend.Dockerfile` và `frontend.Dockerfile` tối ưu hóa kích thước image.
- [x] Cấu hình Nginx reverse proxy `frontend/nginx.conf` phục vụ SPA và định tuyến `/api/`.
- [x] Viết `docker-compose.yml` kết nối Frontend (Nginx), Backend (FastAPI), PostgreSQL 16 và Local Ollama host bridge.
- [x] Viết tài liệu Kịch bản Demo chi tiết từng bước bảo vệ đồ án trước Hội đồng (`DEMO_GUIDE.md`).
- [x] Hoàn thiện tài liệu thuyết minh báo cáo và bộ hướng dẫn chạy nhanh (`README.md`).

---

### ✅ Phase 16: Real-time Streaming Response (SSE) (HOÀN THÀNH)
- [x] Xây dựng phương thức `generate_stream` trong `backend/app/rag/llm.py` đọc stream từ Ollama.
- [x] Xây dựng phương thức `ask_stream` trong `backend/app/rag/pipeline.py` phát ra các sự kiện Server-Sent Events (SSE).
- [x] Bổ sung API endpoint `POST /api/v1/chat/sessions/{id}/messages/stream` trả về `StreamingResponse` và tự động lưu CSDL khi kết thúc.
- [x] Nâng cấp giao diện Chat React hiển thị hiệu ứng chữ chạy thời gian thực và con trỏ nhấp nháy `animate-pulse`.
- [x] Viết unit tests kiểm thử dòng sự kiện SSE và lưu vết tin nhắn (`tests/test_chat_streaming.py`).

---

### ✅ Phase 17: AI Auto-Triage & Smart IT Assistance (HOÀN THÀNH)
- [x] Khởi tạo schemas `TicketAutoTriageRequest` và `TicketAutoTriageResponse` (`backend/app/schemas/ticket.py`).
- [x] Viết service phân tích sự cố bằng Local LLM: Tự động trích xuất danh mục, mức độ ưu tiên, giải thích lý do và gợi ý các bước khắc phục sơ bộ.
- [x] Bổ sung API endpoint `POST /api/v1/tickets/auto-triage`.
- [x] Tích hợp nút **"✨ AI Tự động phân loại & Gợi ý xử lý"** trong modal tạo Ticket trên Frontend.
- [x] Viết unit tests kiểm thử phân loại chính xác sự cố mạng, phần cứng và tài khoản (`tests/test_ai_triage.py`).

---

### ✅ Phase 18: Department Document Access Control (ACL) (HOÀN THÀNH)
- [x] Chuẩn hóa metadata `department_id` cho từng Vector Chunk trong ChromaDB (`0` cho toàn công ty, hoặc mã ID phòng ban).
- [x] Tích hợp bộ lọc phân quyền trong `similarity_search`: Nhân viên phòng ban chỉ tra cứu được tài liệu của phòng ban mình và tài liệu chung; Super Admin và IT Admin tra cứu toàn bộ.
- [x] Gán nhãn phòng ban khi tải lên tài liệu mới trên giao diện `DocumentsPage.tsx`.
- [x] Viết unit test kiểm thử cách ly dữ liệu: Nhân viên HR bị chặn truy cập tài liệu bảo mật IT (`tests/test_department_rag.py`).

---

### ✅ Phase 19: Hybrid Search (ChromaDB + BM25 + RRF) (HOÀN THÀNH)
- [x] Xây dựng module `BM25Index` thuần Python hỗ trợ đối sánh từ khóa kỹ thuật (IP, Port, Mã lỗi, từ khóa tiếng Việt) (`backend/app/rag/bm25.py`).
- [x] Triển khai thuật toán xếp hạng chuẩn công nghiệp Reciprocal Rank Fusion (RRF) kết hợp kết quả Dense Vector + Sparse BM25.
- [x] Tích hợp trực tiếp vào cả 2 luồng `ask()` và `ask_stream()` của `RAGPipeline`.
- [x] Viết unit tests kiểm thử tìm kiếm từ khóa chính xác và công thức xếp hạng RRF (`tests/test_hybrid_search.py`).

