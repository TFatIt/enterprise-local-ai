# QUY TRÌNH QUẢN LÝ KHO BÃI, NGUYÊN TẮC FIFO/FEFO VÀ KIỂM KÊ TỒN KHO BẰNG MÃ VẠCH
**Mã tài liệu:** DOC-WH-001  
**Phòng ban:** Kho bãi (Warehouse)  
**Thẩm quyền:** Ban Quản trị Kho Vận  
**Phiên bản:** 2.0 | **Cấp độ bảo mật:** DEPARTMENT

---

## 1. Nguyên Tắc Luân Chuyển Hàng Hóa
- **FIFO (First In, First Out - Nhập trước, Xuất trước):** Áp dụng cho các vật tư công nghiệp, linh kiện điện tử và bao bì.
- **FEFO (First Expired, First Out - Hết hạn trước, Xuất trước):** Bắt buộc áp dụng cho các vật tư có hạn sử dụng, hóa chất và dung dịch công nghiệp.
- Vị trí lưu kho được định vị theo sơ đồ mã hóa: `Khu vực (Zone) - Dãy (Aisle) - Kệ (Rack) - Tầng (Shelf) - Ô (Bin)`.

---

## 2. Quy Trình Nhập - Xuất - Kiểm Kê Hàng Hóa
1. **Nhập kho:** Quét mã vạch (Barcode/QR code) kiện hàng, đối chiếu PO, dán nhãn pallet và cập nhật vị trí lưu kho trên WMS/ERP trong vòng 2 giờ.
2. **Xuất kho:** Nhân viên soạn hàng (Picker) theo phiếu xuất kho điện tử, quét mã xác nhận trước khi giao hàng cho bộ phận Vận chuyển.
3. **Kiểm kê định kỳ:** Thực hiện kiểm kê luân phiên (Cycle Counting) hàng tuần đối với nhóm hàng giá trị cao (Nhóm A) và tổng kiểm kê toàn kho vào cuối mỗi quý.
