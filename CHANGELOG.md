# CHANGELOG — Enterprise Local AI Assistant

Tất cả các thay đổi kiến trúc và tính năng quan trọng của dự án được ghi nhận tại đây theo nguyên tắc bảo toàn tính ổn định và bảo mật.

---

## [1.1.0] - 2026-09-05: Nâng Cấp Kiến Trúc AI Trò Chuyện Tự Nhiên & Dual-Path RAG

### Added
- **Hybrid Intent Classifier (`backend/app/rag/intent_classifier.py`)**:
  - Tầng 1: Regex Fast-Path siêu tốc (<1ms) nhận diện các mẫu chào hỏi (`GREETING`), trò chuyện thân mật / cảm ơn / hỏi thăm sức khỏe (`SMALL_TALK`), trợ lý viết lách (`WRITING_ASSISTANT`), dịch thuật đa ngữ (`TRANSLATION`), giải thích khái niệm CNTT tổng quát (`GENERAL_CHAT`).
  - Tầng 2: Domain Matching trên 12 khối nghiệp vụ doanh nghiệp (`IT_HELPDESK`, `IT_NETWORK`, `IT_SYSTEM`, `IT_SECURITY`, `HR`, `ACCOUNTING`, `FINANCE`, `SALES`, `PROCUREMENT`, `LEGAL`, `QA_QC`, `PRODUCTION_LOGISTICS`).
  - Định tuyến thông minh: Bỏ qua vector search khi chỉ trò chuyện thông thường để ngăn chặn việc lấy tài liệu không liên quan.
- **Conversation Memory & Context Reformulation (`backend/app/rag/conversation_memory.py`)**:
  - Duy trì cửa sổ ngữ cảnh trượt (Sliding Window) 4-6 lượt tin nhắn gần nhất.
  - Tự động chuẩn hóa câu hỏi phụ thuộc ngữ cảnh (ví dụ: "còn trên macos thì sao?") thành câu truy vấn độc lập tối ưu cho vector retrieval.
- **Dual-Path Generation Pipeline (`backend/app/rag/pipeline.py`)**:
  - `GENERAL_CHAT_SYSTEM_PROMPT`: Giọng văn thân thiện, ấm áp, thông minh và lịch thiệp chuẩn phong cách ChatGPT; không ép vào quy trình và không trích dẫn nguồn khi small talk.
  - `ENTERPRISE_RAG_SYSTEM_PROMPT`: Chuẩn xác, tuân thủ nguyên tắc Zero-Hallucination, phân chia các bước (Bước 1, Bước 2...) rõ ràng và trích dẫn minh chứng nguồn [1], [2].
  - Bổ sung phương thức `chat_general()` và `chat_general_stream()`.
  - Cơ chế phòng chống Prompt Injection: Đóng gói tài liệu trích xuất trong thẻ an toàn `<company_context>...</company_context>`.
  - Bộ làm sạch ký tự UTF-8 cho nguồn trích dẫn (`sanitize_utf8_text`), loại bỏ triệt để lỗi biến dạng ký tự tiếng Việt (`Ch?nh s?ch...`).
- **Feedback API Endpoint (`backend/app/api/v1/chat.py`)**:
  - `POST /api/v1/chat/sessions/{session_id}/messages/{message_id}/feedback`: Cho phép nhân viên đánh giá (rating 1-5 sao hoặc thumbs up/down) và để lại ý kiến đóng góp nhằm cải thiện chất lượng AI.
- **Bộ Kiểm Thử Tự Động Toàn Diện (`backend/tests/test_enterprise_assistant_suite.py`)**:
  - 50+ ca kiểm thử phủ khắp các kịch bản: Intent Classification, Live General Chat, Live Enterprise RAG, Multi-turn Context, ACL RBAC Isolation, Anti-Injection & Anti-Hallucination.

### Changed
- **`backend/app/services/chat_service.py`**:
  - Tích hợp Intent Routing vào cả hai chế độ xử lý đồng bộ (`send_message`) và Server-Sent Events streaming (`send_message_stream`).
  - Truyền đầy đủ lịch sử hội thoại gần nhất vào prompt sinh lời thoại.
  - Ghi nhận Audit Log chi tiết về Intent và số lượng nguồn tài liệu được tham khảo.
- **`backend/app/schemas/chat.py`**:
  - Bổ sung schema `MessageFeedbackCreate`.
- **Tài liệu Kiến trúc**:
  - Cập nhật `ARCHITECTURE.md` và `RAG.md` với sơ đồ luồng Dual-Path và Intent Classifier.
  - Cập nhật `API.md` với các endpoint Streaming SSE và Feedback.

### Fixed
- **Lỗi Phản Hồi Khi Chào Hỏi ("hi", "xin chào")**:
  - Khắc phục triệt để hiện tượng AI tự động vector search và trích xuất các tài liệu ngẫu nhiên (BHYT, Incoterms...) khi người dùng chỉ chào hỏi hoặc hỏi thăm thông thường.
- **Lỗi Ký Tự Tiêu Đề Nguồn**:
  - Khắc phục lỗi encoding làm xuất hiện dấu hỏi chấm `?` trong tên tài liệu tiếng Việt có dấu.
