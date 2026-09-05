# QUY TRÌNH SAO LƯU DỰ PHÒNG WAL, REPLICATION VÀ TỐI ƯU HÓA POSTGRESQL 16
**Mã tài liệu:** DOC-DB-001  
**Phòng ban:** Quản trị Cơ sở Dữ liệu (IT Database)  
**Thẩm quyền:** PostgreSQL Global Development Group  
**Phiên bản:** 16.2 | **Cấp độ bảo mật:** DEPARTMENT

---

## 1. Chiến Lược Sao Lưu Dữ Liệu Điểm Thời Gian (Point-In-Time Recovery - PITR)
- **Bản sao lưu vật lý đầy đủ (Base Backup):** Thực hiện tự động hàng đêm vào lúc 01:00 AM bằng công cụ `pg_basebackup`.
- **Lưu trữ nhật ký ghi trước (WAL Archiving):** Kích hoạt `archive_mode = on` và truyền liên tục các tệp WAL 16MB sang cụm lưu trữ dự phòng độc lập.
- Khi cần phục hồi: Khôi phục bản Base Backup gần nhất và phát lại các tệp WAL đến đúng thời điểm trước khi xảy ra sự cố người dùng xóa nhầm dữ liệu.

---

## 2. Quy Chuẩn Tối Ưu Hóa Truy Vấn & Chỉ Mục (Indexing)
- Mọi câu truy vấn chạy trên bảng có trên 100.000 dòng bắt buộc phải có chỉ mục (B-Tree hoặc GIN Index) tương ứng với các cột trong mệnh đề `WHERE` hoặc `JOIN`.
- Sử dụng lệnh `EXPLAIN (ANALYZE, BUFFERS)` để kiểm tra chi phí thực thi, nghiêm cấm các câu lệnh gây ra quét toàn bộ bảng (Sequential Scan) trên bảng lớn.
- Bật công cụ mở rộng `pg_stat_statements` để giám sát top 10 câu truy vấn chiếm nhiều CPU và I/O nhất hệ thống.
