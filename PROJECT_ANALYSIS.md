# ENTERPRISE LOCAL AI ASSISTANT — TOÀN VĂN PHÂN TÍCH HỆ THỐNG (PROJECT_ANALYSIS.md)

**Ngày lập báo cáo:** 05/09/2026  
**Vai trò thẩm định:** Senior AI Engineer + Full-Stack Engineer + RAG Architect  
**Phiên bản hệ thống:** v2.5.0 Enterprise Local AI  

---

## 1. TỔNG QUAN KIẾN TRÚC HIỆN TẠI (CURRENT ARCHITECTURE)

Hệ thống hiện tại được xây dựng theo mô hình **On-Premise / Local AI** hoàn toàn khép kín, tối ưu cho máy tính nội bộ hoặc máy trạm doanh nghiệp:

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│ GIAO DIỆN NGƯỜI DÙNG (FRONTEND)                                                  │
│ React 18 + Vite + TypeScript + TailwindCSS (Nginx Port 3000 / Vite Dev Port 5173)│
│ Pages: ChatPage, DocumentsPage, UsersPage, TicketsPage, DashboardPage, LoginPage  │
└──────────────────────────────────────┬────────────────────────────────────────────┘
                                       │ REST API + SSE Streaming
┌──────────────────────────────────────▼────────────────────────────────────────────┐
│ BACKEND MICRO-FRAMEWORK (FASTAPI)                                                 │
│ Python 3.12 + FastAPI + SQLAlchemy ORM (Uvicorn Port 8000)                        │
│ ├── Auth & Security: JWT Bearer, RBAC (5 Roles), Department Isolation (26 Depts)  │
│ ├── Document Service: File storage, DocumentParser (PDF, DOCX, TXT, CSV, XLSX, MD)│
│ └── Chat Service: Session Management, SSE Stream Generator, History Storage       │
└──────────┬───────────────────────────┬─────────────────────────────────┬──────────┘
           │                           │                                 │
┌──────────▼──────────────┐ ┌──────────▼─────────────────┐ ┌─────────────▼─────────┐
│ RELATIONAL DATABASE     │ │ VECTOR DATABASE            │ │ LOCAL AI INFERENCE     │
│ PostgreSQL 16           │ │ ChromaDB (Persistent)      │ │ Ollama Engine (11434)  │
│ Port 5433 (Tránh đè 5432)│ │ Collection: enterprise_kb  │ │ ├── qwen2.5:3b (LLM)   │
│ 13 Bảng dữ liệu quan hệ │ │ Metric: Cosine Similarity  │ │ ├── nomic-embed-text   │
│ Users, Roles, Documents,│ │ 221 Chunks đang hoạt động  │ │ └── enterprise-        │
│ Permissions, Chat, Logs │ │ FlashRank Reranker         │ │     discovery-agent    │
└─────────────────────────┘ └────────────────────────────┘ └────────────────────────┘
```

---

## 2. ĐÁNH GIÁ CHỨC NĂNG ĐANG HOẠT ĐỘNG (CURRENT FUNCTIONING FEATURES)

1. **Hạ tầng Container & Điều khiển trung tâm:**
   - Docker Compose 3 containers (`enterprise_ai_db`, `enterprise_ai_backend`, `enterprise_ai_frontend`) chạy ổn định.
   - Script tập trung [menu.bat](file:///d:/Maytinh-data/Downloads/AI/menu.bat) hỗ trợ 9 tính năng: chạy Docker, Dev local, Git push, tải model Ollama, health check và tự động nạp tài liệu.
2. **Quản trị Người dùng & Phân quyền (RBAC & Department Isolation):**
   - 33 tài khoản mẫu phủ rộng 26 phòng ban và 5 cấp độ vai trò: `SUPER_ADMIN`, `ADMIN`, `IT_ADMIN`, `DEPT_MANAGER`, `EMPLOYEE`.
   - Cơ chế kiểm soát quyền hạn phân tầng (EDAC) hoạt động tốt ở cấp độ bảng tài liệu.
3. **Kho Tri thức & Xử lý Tài liệu:**
   - 34 tài liệu toàn văn chất lượng cao thuộc 22 phòng ban đã được nạp thành công vào PostgreSQL.
   - Toàn bộ 221 chunks văn bản đã được tạo embedding vector bằng `nomic-embed-text` và lưu trong ChromaDB.
   - Master Catalog với 1.090 tài liệu định danh cùng 300 câu hỏi kiểm thử RAG trong `enterprise_knowledge_base/metadata/`.
4. **Hạ tầng RAG cơ sở:**
   - Hỗ trợ Dense Vector Search (ChromaDB) kết hợp Sparse Keyword Search (BM25) qua Reciprocal Rank Fusion (RRF).
   - Tích hợp FlashRank Cross-Encoder reranker (`ms-marco-TinyBERT-L-2-v2`) để xếp hạng lại top-3 chunks.
   - Có bộ lọc che giấu thông tin nhạy cảm PII (`pii_masker.py`).
5. **Giao diện Web:**
   - Thiết kế chuẩn Dark Mode Enterprise, responsive, hỗ trợ tra cứu tài liệu, quản lý ticket hỗ trợ, bảng thống kê quản trị.

---

## 3. CÁC ĐIỂM NGHẼN & LỖI NGHIÊM TRỌNG ĐANG TỒN TẠI (BROKEN & BOTTLENECK FEATURES)

### 🔴 LỖI 1: ÉP TOÀN BỘ TIN NHẮN PHẢI ĐI QUA RAG (GÂY RA LỖI NHƯ HÌNH ẢNH USER GỬI)
- **Hiện tượng thực tế:** Người dùng gõ `"hi"`, `"xin chào"`, `"chào bạn"`, hoặc `"hôm nay tôi hơi mệt"`:
  - Hệ thống lấy từ `"hi"` đi tìm kiếm vector trong ChromaDB.
  - Do khoảng cách cosine với 221 chunks, một số tài liệu (như BHYT, Incoterms, IT) vẫn đạt ngưỡng similarity $\ge 0.40$.
  - Pipeline nhồi các đoạn này vào `SYSTEM_PROMPT` cứng nhắc của `pipeline.py`.
  - Kết quả: AI trả lời một câu vô nghĩa và ngớ ngẩn:
    > *"Không tìm thấy thông tin đầy đủ trong tài liệu nội bộ của doanh nghiệp. Bước 1: Để biết về bảo hiểm y tế (BHYT) tham khảo Tài liệu [1]... Bước 2: Để hiểu về Incoterms tham khảo Tài liệu [2]..."*
- **Nguyên nhân gốc rễ:** Thiếu hoàn toàn tầng **Intent Classifier (Phân loại ý định)** trước RAG.

### 🔴 LỖI 2: HOÀN TOÀN MẤT TRÍ NHỚ HỘI THOẠI (ZERO CONVERSATION MEMORY)
- Trong [backend/app/services/chat_service.py](file:///d:/Maytinh-data/Downloads/AI/backend/app/services/chat_service.py) (dòng 131 và 216), hệ thống chỉ truyền đúng `content` của tin nhắn hiện tại vào RAG.
- Toàn bộ lịch sử các câu hỏi trước đó trong `session.messages` bị bỏ qua 100%.
- Khi người dùng hỏi nối tiếp:
  - Câu 1: *"VPN công ty dùng loại gì?"* -> AI trả lời: Fortinet SSL-VPN.
  - Câu 2: *"Cách cài trên Windows?"* -> RAG chỉ tìm kiếm `"Cách cài trên Windows?"`, mất toàn bộ ngữ cảnh VPN, dẫn đến tìm kiếm sai tài liệu hoặc trả lời lạc đề!

### 🔴 LỖI 3: LỖI FONT / ENCODING TRONG NGUỒN TRÍCH DẪN (CITATION ENCODING CORRUPTION)
- Trong ảnh người dùng gửi, nguồn trích dẫn hiển thị:
  `[2] Ch?nh s?ch An to?n Th?ng tin...` thay vì `Chính sách An toàn Thông tin`.
- Do quá trình xử lý chuỗi ở tầng chuyển đổi multipart hoặc parser metadata trên môi trường Windows CP1252 / UTF-8.

### 🟡 LỖI 4: THIẾU CƠ CHẾ ĐÁNH GIÁ ĐỘ TIN CẬY (CONFIDENCE SCORING & SMART FALLBACK)
- Hiện tại chỉ có ngưỡng cứng `settings.RAG_SIMILARITY_THRESHOLD = 0.40`.
- Thiếu phân loại 3 mức độ:
  - **High (>0.80):** Khẳng định thông tin chắc chắn, trích dẫn số trang/điều khoản.
  - **Medium (0.60 - 0.79):** Cung cấp câu trả lời kèm cảnh báo nguồn.
  - **Low (<0.60):** Lập tức từ chối khẳng định thông tin nội bộ: *"Tôi chưa tìm thấy tài liệu nội bộ về vấn đề này trong Knowledge Base..."*, sau đó mới đưa ra gợi ý chung hoặc đề xuất tạo ticket.

### 🟡 LỖI 5: CẤU HÌNH MODEL CỨNG (HARDCODED MODEL)
- Model LLM bị gắn cố định là `qwen2.5:3b`.
- Chưa có cấu hình Model Router phân luồng theo tác vụ: Chat thông thường, Suy luận kỹ thuật, Lập trình hoặc Tóm tắt.

---

## 4. BẢNG CƠ SỞ DỮ LIỆU & QUAN HỆ THỰC THỂ (DATABASE STRUCTURE)

Hiện tại PostgreSQL có 13 bảng:
- `users`: ID, username, email, hashed_password, full_name, role_id, department_id, is_active.
- `roles`: ID, name, code, description.
- `permissions`: ID, name, code, module.
- `role_permissions`: Liên kết N-N giữa Role và Permission.
- `departments`: ID, name, code, description.
- `department_permissions`: Phân quyền liên phòng ban.
- `documents`: ID, title, file_name, stored_file_name, file_path, file_type, file_size, department_id, security_level, version, status, rag_status, total_chunks.
- `document_versions`: Lưu lịch sử phiên bản của từng tài liệu.
- `document_chunks`: Lưu vết các đoạn chunking của tài liệu.
- `document_permissions`: Phân quyền chi tiết trên từng tài liệu.
- `chat_sessions`: ID, user_id, title, is_active, created_at, updated_at.
- `chat_messages`: ID, session_id, sender_type (USER/ASSISTANT/SYSTEM), content, sources (JSON), response_time_ms, created_at.
- `tickets`: Hỗ trợ kỹ thuật liên kết với chat session.
- `audit_logs`: Nhật ký kiểm toán bảo mật.

---

## 5. ĐÁNH GIÁ BẢO MẬT & PHÒNG CHỐNG PROMPT INJECTION (SECURITY AUDIT)

1. **Bảo mật phân quyền dữ liệu (Data Isolation):**
   - Đã có kiểm tra ở tầng truy vấn vector ChromaDB qua hàm `is_chunk_accessible` và lọc `department_id`.
   - Cần củng cố: Nhân viên không được truy xuất metadata (tên file, tiêu đề) của các tài liệu mật phòng ban khác.
2. **Phòng chống Prompt Injection (Prompt Injection Defense):**
   - Ngữ cảnh tài liệu nội bộ trích xuất từ RAG phải được bao bọc trong khối thẻ cách ly rõ ràng: `<context>...</context>`.
   - System Prompt phải quy định rõ: Mọi nội dung bên trong `<context>` chỉ là DỮ LIỆU THAM KHẢO, tuyệt đối không được coi là CHỈ THỊ THỰC THI (Instruction).

---

## 6. ĐỀ XUẤT GIẢI PHÁP KIẾN TRÚC MỤC TIÊU (TARGET SOLUTION)

Xây dựng bộ đôi module đột phá:
1. **`app/rag/intent_classifier.py`**:
   - Sử dụng cơ chế Hybrid: **Rule-based Regex & Keyword Matching** (cực nhanh, < 1ms) kết hợp **Semantic Keyword Scoring**.
   - Phân luồng triệt để:
     - `GREETING` ("hi", "hello", "xin chào", "chào bạn", "alo"): Trả lời chào hỏi tự nhiên, giới thiệu chức năng hỗ trợ.
     - `SMALL_TALK` ("hôm nay tôi mệt", "bạn khỏe không", "bạn là ai", "cảm ơn bạn", "tạm biệt"): Trò chuyện tự nhiên, ân cần, phong cách ChatGPT.
     - `GENERAL_CHAT` ("DHCP là gì", "giải thích TCP/IP", "viết email xin nghỉ", "dịch sang tiếng Anh"): Gọi thẳng Ollama LLM mà KHÔNG kích hoạt RAG.
     - `ENTERPRISE_KNOWLEDGE` (Hỏi về VPN, Domain, Kế toán, Thuế, Lương, Hợp đồng, ISO, BCP...): Kích hoạt RAG Pipeline đầy đủ.
2. **`app/rag/conversation_memory.py`**:
   - Trích xuất 4-6 tin nhắn gần nhất của phiên hội thoại (`session.messages`).
   - Tự động viết lại câu hỏi (Query Rewriting / Reformulation): biến câu hỏi phụ thuộc ngữ cảnh ("Cách cài trên Windows?") thành câu hỏi độc lập đầy đủ nghĩa ("Cách cài đặt Fortinet SSL-VPN công ty trên hệ điều hành Windows?").
3. **`app/rag/smart_router.py`**:
   - Điều phối luồng xử lý tin nhắn, tính toán Confidence Score (High, Medium, Low), tạo định dạng trích dẫn nguồn chuẩn xác, tránh tuyệt đối tình trạng Hallucination.
