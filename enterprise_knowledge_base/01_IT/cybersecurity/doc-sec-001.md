# TIÊU CHUẨN AN TOÀN THÔNG TIN THEO KHUNG NIST CSF 2.0 VÀ CIS CONTROLS V8
**Mã tài liệu:** DOC-SEC-001  
**Phòng ban:** An toàn Thông tin (IT Security)  
**Thẩm quyền:** NIST Computer Security Resource Center & CIS  
**Phiên bản:** 2.0 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Sáu Chức Năng Cốt Lõi Khung NIST CSF 2.0
1. **GOVERN (Quản trị):** Thiết lập chính sách an ninh mạng, xác định trách nhiệm giải trình và quản trị rủi ro chuỗi cung ứng.
2. **IDENTIFY (Nhận diện):** Quản lý toàn bộ tài sản phần cứng, phần mềm, luồng dữ liệu và các lỗ hổng bảo mật tiềm ẩn.
3. **PROTECT (Bảo vệ):** Triển khai xác thực đa yếu tố (MFA), phân quyền truy cập tối thiểu (Least Privilege), mã hóa dữ liệu nhạy cảm ở trạng thái lưu trữ (Data at Rest) và truyền tải (Data in Transit).
4. **DETECT (Phát hiện):** Giám sát nhật ký bảo mật (SIEM), phát hiện các hành vi bất thường, tấn công brute-force hoặc mã độc lây lan.
5. **RESPOND (Ứng phó):** Kích hoạt quy trình phản ứng sự cố theo NIST SP 800-61 Rev 2, cô lập máy trạm nhiễm mã độc trong vòng 15 phút.
6. **RECOVER (Phục hồi):** Khôi phục dữ liệu từ bản sao lưu sạch (Clean Backup) và rút kinh nghiệm sau sự cố.

---

## 2. Các Kiểm Soát An Ninh Bắt Buộc (CIS Controls v8)
- Bắt buộc kích hoạt tường lửa cá nhân (Host-based Firewall) trên 100% máy trạm.
- Khóa cổng USB lưu trữ ngoài đối với các máy trạm xử lý dữ liệu tài chính và khách hàng.
- Quét và vá lỗ hổng hệ điều hành định kỳ vào tuần thứ hai hàng tháng (Patch Tuesday).
