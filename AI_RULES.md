# AI_RULES.md

# Quy chuẩn và Chính sách Vận hành Local AI

Tài liệu này quy định các tiêu chuẩn kỹ thuật bắt buộc khi tích hợp và vận hành mô hình trí tuệ nhân tạo cục bộ (Local AI) trong dự án **Enterprise Local AI Assistant**.

---

## 1. Chính sách Mô hình Ngôn ngữ (Model Policy)

### 1.1. Mô hình Mặc định (Default LLM)
* **Tên mô hình**: `Qwen3 4B` (hoặc `Qwen2.5 3B` theo tags chuẩn của Ollama).
* **Lý do lựa chọn**:
  - Khả năng xử lý ngôn ngữ tiếng Việt và thuật ngữ kỹ thuật CNTT xuất sắc.
  - Cấu hình 4-bit quantization (GGUF) chỉ tiêu thụ khoảng 2.0GB - 2.8GB RAM/VRAM.
  - Tốc độ sinh chữ (generation speed) đạt từ 20-35 tokens/giây trên CPU máy tính xách tay thế hệ mới.

### 1.2. Quy tắc Điều chỉnh Mô hình theo Cấu hình Máy tính
* **Laptop cấu hình thấp (RAM 8GB, CPU thế hệ cũ)**:
  - Cho phép hạ cấp xuống `Qwen2.5 1.5B` hoặc `Qwen 1.7B`.
  - Giảm `Top-K` từ 5 xuống 3 chunks để tiết kiệm bộ nhớ ngữ cảnh.
* **Laptop/Máy trạm cấu hình cao (RAM 16GB - 32GB, có card đồ họa rời RTX)**:
  - Có thể nâng cấp lên `Qwen2.5 7B` hoặc `Qwen3 8B` để câu trả lời trau chuốt và thông minh hơn.
* **Quy tắc vàng**:
  - Không tự ý thay đổi mô hình nếu chưa chứng minh được sự cần thiết qua kết quả kiểm thử.
  - Khi muốn nâng cấp hoặc đổi model, phải đánh giá lại tài nguyên RAM và thời gian phản hồi.

---

## 2. Chính sách Mô hình Embedding (Embedding Policy)

* **Mô hình bắt buộc**: `nomic-embed-text`.
* **Kích thước vector**: 768 chiều.
* **Quy tắc**:
  - Tuyệt đối dùng đồng nhất một mô hình embedding duy nhất cho cả hai quá trình: nạp tài liệu (document indexing) và tìm kiếm câu hỏi (query search).
  - Không trộn lẫn các mô hình embedding khác nhau trong cùng một ChromaDB collection.

---

## 3. Tham số Sinh từ (Inference Hyperparameters)

Để bảo đảm câu trả lời mang tính kỹ thuật chính xác, nhất quán và không sáng tạo lung tung:

```python
INFERENCE_PARAMS = {
    "temperature": 0.1,         # Nhiệt độ thấp giúp phản hồi mang tính xác định (deterministic) và bám sát tài liệu
    "top_p": 0.9,               # Giới hạn phân phối xác suất từ ngữ
    "num_ctx": 4096,            # Giới hạn cửa sổ ngữ cảnh (Context Window) phù hợp với Top-5 chunks
    "repeat_penalty": 1.1,      # Tránh lặp từ
    "stop": ["<|im_end|>", "<|endoftext|>"]
}
```

---

## 4. Chính sách Chống Ảo giác (Anti-Hallucination Rules)

1. **Nguyên tắc "Tài liệu là Chân lý duy nhất"**:
   - Nếu trong ngữ cảnh trích xuất (Context) không chứa giải pháp cho câu hỏi, mô hình không được phép sử dụng tri thức tiền huấn luyện (pre-trained knowledge) để tự trả lời.
2. **Quy tắc Phản hồi Khi Không Tìm Thấy (Out-of-Context Fallback)**:
   - Khi độ tương đồng của các chunks dưới ngưỡng tin cậy ($< 0.55$), hệ thống bắt buộc phải đưa ra thông báo:
     > *"Không tìm thấy thông tin đầy đủ trong tài liệu nội bộ của doanh nghiệp. Bạn vui lòng liên hệ bộ phận IT hoặc bấm nút Tạo IT Support Ticket bên dưới để được hỗ trợ trực tiếp."*
   - Cờ `suggest_ticket` trong response API phải được đặt thành `true`.
3. **Quy tắc Trung thực về Nguồn (Citation Integrity)**:
   - Nghiêm cấm hoàn toàn hành vi tự bịa ra tên file hoặc số trang tài liệu không có thực trong cơ sở dữ liệu.
   - Nguồn hiển thị trên giao diện phải khớp 100% với `document_id` và `chunk_id` được ChromaDB trả về.

---

## 5. Tiêu chuẩn An toàn Dữ liệu (Data Privacy & Isolation)

* **Không gửi dữ liệu ra ngoài (No Cloud Egress)**: Mọi yêu cầu truy vấn, nội dung tài liệu và câu hỏi nhân viên phải được xử lý bên trong mạng cục bộ (`localhost` hoặc Docker network nội bộ).
* **Cách ly theo Phòng ban (Departmental Isolation)**: Tài liệu được gắn thẻ phòng ban (`department_id`). Khi nhân viên phòng ban tra cứu, hệ thống có thể kích hoạt bộ lọc metadata để bảo đảm nhân viên không tiếp cận tài liệu nhạy cảm của phòng ban khác nếu chưa được cấp quyền.
