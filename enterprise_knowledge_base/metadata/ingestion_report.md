# CHIẾN LƯỢC VÀ QUY TRÌNH NẠP DỮ LIỆU (INGESTION REPORT)
**Hệ thống:** Enterprise Knowledge Base Ingestion Pipeline  
**Model Embedding:** `nomic-embed-text` (Chiều vector: 768)  
**Vector Database:** `ChromaDB` (Chế độ lưu trữ: Persistent Client)  
**Reranker Model:** `FlashRank` (`ms-marco-TinyBERT-L-2-v2`)  
**LLM Engine:** `Ollama` với mô hình `qwen2.5:3b`

---

## 1. Kiến Trúc Luồng Dữ Liệu Ingestion (End-to-End Pipeline)

```text
[1.000+ Tài liệu Nguồn] (PDF / DOCX / MD)
           │
           ▼
[DocumentParser] ──► Làm sạch ký tự lạ, chuẩn hóa khoảng trắng, che chắn PII
           │
           ▼
[Context-Aware Chunker] ──► Cắt đoạn theo Section & Heading (Kích thước 800 ký tự, overlap 120 ký tự)
           │
           ▼
[Metadata Enricher] ──► Gắn 21 trường metadata vào từng chunk (document_id, department, security_level)
           │
           ▼
[Ollama nomic-embed-text] ──► Tạo vector đặc trưng 768 chiều
           │
           ▼
[ChromaDB Persistent Store] ──► Lưu trữ Vector Index kèm Metadata Filtering
```

---

## 2. Tiêu Chuẩn Cắt Đoạn (Chunking Policy)

- **Không chia đoạn thô thiển theo độ dài ký tự:** Ưu tiên giữ nguyên khối ngữ cảnh theo tiêu đề (`#`, `##`, `###`), các bước thực hiện (`Bước 1`, `Bước 2`), các điều khoản luật (`Điều 1`, `Khoản 2`), hoặc hàng trong bảng biểu.
- **Kích thước Chunk mục tiêu:**
  - `Chunk Size`: 800 - 1.200 ký tự.
  - `Chunk Overlap`: 100 - 150 ký tự (bảo đảm không bị đứt gãy mạch ý tứ giữa hai đoạn nối tiếp).
- **Metadata gắn kèm trên từng Chunk:**
  - `document_id`: Mã định danh tài liệu.
  - `department`: Mã phòng ban để lọc phân quyền (`$eq: user.department`).
  - `security_level`: Cấp độ bảo mật (`PUBLIC`, `INTERNAL`, `DEPARTMENT`, `CONFIDENTIAL`).
  - `title`: Tên tài liệu.
  - `source`: Cơ quan xuất bản.
  - `version`: Phiên bản tài liệu.

---

## 3. Cơ Chế Cô Lập Dữ Liệu & Phân Quyền Phòng Ban (Department Isolation)

Khi người dùng gửi câu hỏi trong khung Chat AI:
1. Backend trích xuất danh tính người dùng: `user_role = user.role.code` và `user_dept = user.department.code`.
2. Nếu `user_role` là `EMPLOYEE`:
   - Bộ lọc ChromaDB tự động chèn mệnh đề:
     `{ "$or": [ {"security_level": "PUBLIC"}, {"department": user_dept} ] }`
   - Nhân viên IT tuyệt đối không truy xuất được tài liệu Kế toán hay Hợp đồng nhạy cảm của Ban Giám đốc.
3. Nếu `user_role` là `SUPER_ADMIN` hoặc `ADMIN`:
   - Truy xuất toàn bộ kho tri thức không giới hạn.

---

## 4. Kế Hoạch Chạy Thử Nghiệm Với Bộ 300 Câu Hỏi (`rag_test_questions.json`)

- Chạy kiểm thử tự động toàn bộ 300 câu hỏi đánh giá.
- Đo lường 3 chỉ số cốt lõi:
  1. **Top-3 Retrieval Accuracy:** Tài liệu chứa câu trả lời có nằm trong top 3 kết quả trả về của ChromaDB hay không (Kỳ vọng: $\ge 92\%$).
  2. **Context Precision sau FlashRank Rerank:** Tỉ lệ đoạn văn bản thực sự chứa câu trả lời nằm ở vị trí số 1 sau khi rerank (Kỳ vọng: $\ge 88\%$).
  3. **Zero-Hallucination Rate:** Tỉ lệ AI từ chối trả lời hoặc nói rõ tài liệu không đề cập khi câu hỏi nằm ngoài phạm vi tri thức (Kỳ vọng: $100\%$).
