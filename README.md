# Enterprise Local AI Assistant

> **Hệ thống Trợ lý AI Nội bộ Doanh nghiệp sử dụng Local Large Language Model và Retrieval-Augmented Generation (RAG)**  
> *Đồ án tốt nghiệp Đại học ngành Kỹ thuật Phần mềm / Khoa học Máy tính*

---

## 1. Giới thiệu tổng quan

Trong môi trường doanh nghiệp hiện đại, việc quản trị tri thức nội bộ và hỗ trợ kỹ thuật (IT Support) là bài toán trọng tâm. **Enterprise Local AI Assistant** là giải pháp phần mềm toàn diện giúp nhân viên tra cứu quy trình, hỏi đáp chính sách và nhận hướng dẫn xử lý sự cố kỹ thuật dựa trên kho tài liệu nội bộ của tổ chức.

Hệ thống được thiết kế theo kiến trúc **Local AI-First**, cam kết bảo mật 100% dữ liệu doanh nghiệp: toàn bộ mô hình ngôn ngữ lớn (LLM), vector database và quy trình trích xuất văn bản đều hoạt động nội bộ trên hạ tầng máy chủ của doanh nghiệp hoặc laptop cá nhân, không phụ thuộc và không gửi dữ liệu ra các dịch vụ AI đám mây bên thứ ba.

---

## 2. Tính năng cốt lõi

### 2.1. Phân hệ Nhân viên (Employee)
* **Hỏi đáp Tri thức Doanh nghiệp (AI RAG Chat)**: Đặt câu hỏi tự nhiên về quy trình, hướng dẫn IT, chính sách nhân sự và nhận câu trả lời chính xác trích xuất từ tài liệu.
* **Trích dẫn nguồn minh bạch (Source Citation)**: Mỗi câu trả lời đều kèm liên kết đến tài liệu gốc (Tên file, số trang/đoạn trích dẫn) giúp người dùng kiểm chứng.
* **Cơ chế Fallback & Tạo IT Ticket**: Khi kho tri thức không có câu trả lời hoặc sự cố vượt ngoài khả năng tự xử lý, hệ thống tự động hướng dẫn người dùng tạo Ticket gửi cho đội ngũ IT Admin.
* **Quản lý lịch sử hội thoại**: Lưu vết và xem lại các phiên hỏi đáp trước đó.

### 2.2. Phân hệ Quản trị IT (IT Admin)
* **Quản lý IT Knowledge Base**: Tải lên và phân loại tài liệu hướng dẫn kỹ thuật mạng, phần mềm, phần cứng.
* **Xử lý Ticket hỗ trợ**: Tiếp nhận, phân loại mức độ ưu tiên (Priority), cập nhật trạng thái (Open, In Progress, Resolved, Closed) và trao đổi giải pháp qua Ticket Comments.

### 2.3. Phân hệ Quản trị Hệ thống (Super Admin)
* **Quản trị người dùng & Phân quyền (RBAC)**: Quản lý tài khoản, phòng ban, gán vai trò (`SUPER_ADMIN`, `IT_ADMIN`, `EMPLOYEE`).
* **Quản lý toàn diện Tài liệu (Document Management)**: Upload (PDF, DOCX, TXT), phân bổ theo phòng ban, theo dõi trạng thái Indexing (Uploaded, Processing, Indexed, Failed).
* **Bảng điều khiển Giám sát (Admin Dashboard)**: Thống kê số lượng người dùng, tài liệu, câu hỏi, ticket, tỷ lệ AI giải quyết thành công (AI Resolution Rate) và các chủ đề được quan tâm nhiều nhất.
* **Nhật ký hệ thống (Audit Logs)**: Ghi vết hoạt động người dùng phục vụ an toàn thông tin.

---

## 3. Kiến trúc kỹ thuật (Architecture)

Hệ thống được thiết kế theo mô hình **Modular Monolith**, tối ưu hóa để vận hành mượt mà trên laptop cá nhân hoặc máy chủ cục bộ:

```text
                    NGƯỜI DÙNG (Trình duyệt)
                              │
                              ▼
              ┌───────────────────────────────┐
              │     Frontend (React + TS)     │  Vite, Tailwind CSS, Axios
              │         Port: 5173 / 80       │
              └───────────────┬───────────────┘
                              │ REST API / SSE
                              ▼
              ┌───────────────────────────────┐
              │      Backend (FastAPI)        │  Python, SQLAlchemy, Pydantic
              │         Port: 8000            │
              └───────────────┬───────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │  PostgreSQL  │    │   ChromaDB   │    │    Ollama    │
   │  Port: 5432  │    │  VectorStore │    │  Port: 11434 │
   │              │    │              │    │  (Qwen3 4B)  │
   └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 4. Công nghệ sử dụng (Tech Stack)

| Thành phần | Công nghệ chính | Lý do lựa chọn |
| :--- | :--- | :--- |
| **Frontend** | React, TypeScript, Vite, Tailwind CSS | Giao diện hiện đại, gõ an toàn (type-safe), tốc độ tải trang cao, dễ tùy biến |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, Pydantic | Xử lý bất đồng bộ (async), tài liệu API Swagger tự động, hiệu năng cao |
| **Database** | PostgreSQL | Cơ sở dữ liệu quan hệ mạnh mẽ, đảm bảo tính toàn vẹn (ACID) |
| **Vector DB** | ChromaDB | Vector store nhẹ, lưu trữ dạng tệp tin cục bộ hoặc service, không cần GPU |
| **Local LLM** | Ollama, Qwen3 4B (hoặc Qwen2.5) | Mô hình ngôn ngữ xuất sắc về tiếng Việt và tiếng Anh, vận hành mượt trên CPU/RAM laptop |
| **Embedding** | nomic-embed-text | Mô hình embedding mã nguồn mở hiệu năng cao, context 8192 tokens |
| **Đóng gói** | Docker, Docker Compose | Đóng gói toàn bộ ứng dụng chỉ với 1 câu lệnh `docker compose up` |

---

## 5. Cấu trúc thư mục dự án

```text
enterprise-local-ai/
├── backend/                  # Mã nguồn Backend FastAPI
│   ├── app/
│   │   ├── api/              # API Endpoints (Auth, Users, Documents, Chat, Tickets, Dashboard)
│   │   ├── core/             # Cấu hình hệ thống, Database Session, JWT Security
│   │   ├── models/           # SQLAlchemy ORM Models
│   │   ├── schemas/          # Pydantic Request/Response DTOs
│   │   ├── services/         # Nghiệp vụ xử lý (Business Logic)
│   │   ├── rag/              # Module RAG (Parser, Chunker, Embedding, ChromaDB, Generator)
│   │   └── main.py           # FastAPI Application Entrypoint
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Biến môi trường mẫu
├── frontend/                 # Mã nguồn Frontend React TypeScript
│   ├── src/
│   │   ├── assets/           # Tài nguyên tĩnh (Hình ảnh, icons)
│   │   ├── components/       # Các UI Component tái sử dụng
│   │   ├── pages/            # Các màn hình chính (Chat, Admin, Tickets, Documents)
│   │   ├── services/         # API Client (Axios)
│   │   ├── types/            # TypeScript interfaces
│   │   └── App.tsx           # Route configuration & Layout
│   ├── package.json
│   └── vite.config.ts
├── documents/                # Thư mục lưu tài liệu mẫu demo (PDF, DOCX, TXT)
├── tests/                    # Bộ kiểm thử tự động (Unit & Integration tests)
├── docker/                   # Dockerfiles cho Frontend & Backend
├── docker-compose.yml        # File khởi chạy toàn bộ hệ thống
├── README.md                 # Tài liệu tổng quan
├── ARCHITECTURE.md           # Thiết kế kiến trúc chi tiết
├── DATABASE.md               # Thiết kế cơ sở dữ liệu (ERD, DDL)
├── API.md                    # Đặc tả RESTful API
├── RAG.md                    # Thiết kế chi tiết Pipeline RAG
├── AI_RULES.md               # Quy định kỹ thuật & chống ảo giác cho mô hình
└── TODO.md                   # Bảng theo dõi tiến độ đồ án (15 Phases)
```

---

## 6. Yêu cầu phần cứng đề xuất (Laptop)

* **Hệ điều hành**: Windows 10/11, macOS, hoặc Linux.
* **CPU**: 4 nhân / 8 luồng trở lên (Intel Core i5 Gen 11+, AMD Ryzen 5000 series trở lên).
* **RAM**:
  * Tối thiểu: 8GB RAM (sử dụng model Qwen 1.7B).
  * Khuyến nghị: 16GB RAM (sử dụng model Qwen3 4B / Qwen2.5 3B).
* **Dung lượng ổ cứng**: Tối thiểu 15GB SSD trống (cho Docker images, database, và LLM weights).
* **GPU**: Tùy chọn (Hệ thống có thể chạy hoàn toàn bằng CPU nhờ cấu hình Ollama).

---

## 7. Hướng dẫn cài đặt nhanh (Quickstart)

### Bước 1: Khởi động Ollama và tải mô hình AI
Cài đặt Ollama từ [ollama.com](https://ollama.com) và chạy các lệnh:
```bash
# Tải mô hình Embedding cục bộ
ollama pull nomic-embed-text

# Tải mô hình LLM chính
ollama pull qwen2.5:3b
# (hoặc ollama pull qwen2.5:1.5b nếu máy cấu hình RAM thấp)
```

### Bước 2: Chạy Backend (Môi trường Development)
```bash
cd backend
python -m venv venv
# Kích hoạt venv (Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Truy cập Swagger API Documentation tại: `http://localhost:8000/docs`

### Bước 4: Triển khai toàn diện bằng Docker Compose (Khuyến nghị Production/Defense)
Hệ thống hỗ trợ khởi chạy toàn bộ các dịch vụ bằng 1 lệnh duy nhất:
```bash
docker-compose up --build -d
```
* **Frontend SPA**: `http://localhost:3000` (hoặc `http://localhost:80`)
* **FastAPI Backend & Swagger**: `http://localhost:8000/docs`
* **PostgreSQL Database**: Port 5432
* **Local Ollama Daemon**: Tự động kết nối qua `host.docker.internal:11434`

---

## 8. Tài liệu Kịch bản Demo Bảo vệ Tốt nghiệp
Xem kịch bản thuyết trình và demo thực tế từng bước dành cho Hội đồng tại: [DEMO_GUIDE.md](file:///d:/Maytinh-data/Downloads/AI/DEMO_GUIDE.md).

---

## 9. Bộ kiểm thử tự động (Test Suite)
Dự án được bảo chứng với **52/52 bài kiểm thử tự động (Unit & Integration Tests)**:
```bash
$env:PYTHONPATH="backend"; pytest -v tests/
```
* `test_auth.py`: Xác thực JWT, Refresh token, Bcrypt password hashing.
* `test_database.py`: Quan hệ ORM, cascading delete, SQLite/PostgreSQL fallback.
* `test_rbac_and_users.py`: Phân quyền RBAC, quản lý phòng ban và người dùng.
* `test_documents.py`: Tải lên, bóc tách văn bản, cắt chunks và lập chỉ mục.
* `test_rag_pipeline.py`: Luồng RAG, embedding, vector similarity search.
* `test_chat.py`: Quản lý phiên hội thoại và tự động sinh tiêu đề.
* `test_tickets.py`: Vòng đời IT Ticket, phân công và ghi chú nội bộ IT.
* `test_dashboard.py`: Thống kê tổng hợp số liệu và bảo vệ phân quyền.
* `test_rag_benchmark.py`: Benchmark thực nghiệm 5 kịch bản tri thức IT với độ chính xác và kháng ảo giác 100%.
* **Tên đề tài**: Hệ thống trợ lý AI nội bộ doanh nghiệp sử dụng Local Large Language Model và Retrieval-Augmented Generation (Enterprise Local AI Assistant).
* **Quy chuẩn phát triển**: Tuân thủ tiêu chuẩn kỹ thuật phần mềm (Clean Code, SOLID, DRY, KISS, RBAC, Data Privacy).
