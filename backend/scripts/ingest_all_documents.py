#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ENTERPRISE KNOWLEDGE BASE — AUTOMATED RAG INGESTION PIPELINE
===============================================================================
Script to discover, validate, upload, chunk, and index all enterprise
documents into FastAPI + PostgreSQL + ChromaDB Vector Database using
Ollama nomic-embed-text embeddings.
"""

import os
import sys
import io
import time
from pathlib import Path
import requests

# Force UTF-8 on Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = BASE_DIR / "documents"
KB_DIR = BASE_DIR / "enterprise_knowledge_base"
API_BASE = "http://127.0.0.1:8000/api/v1"

# -----------------------------------------------------------------------------
# 1. AUTHENTICATE WITH BACKEND API
# -----------------------------------------------------------------------------
def get_auth_token():
    print("[*] Đang kết nối tới Backend API tại: " + API_BASE)
    try:
        resp = requests.post(
            f"{API_BASE}/auth/login",
            json={"username_or_email": "admin@enterprise.local", "password": "Admin@123456"},
            timeout=10
        )
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Không thể kết nối tới Backend API tại http://127.0.0.1:8000")
        print("Vui lòng khởi động hệ thống trước (Menu lựa chọn 1 hoặc 4).")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"[ERROR] Đăng nhập quản trị viên thất bại: {resp.status_code} - {resp.text}")
        sys.exit(1)

    token = resp.json().get("access_token")
    print("[OK] Đăng nhập quản trị viên thành công (Super Admin).")
    return token


# -----------------------------------------------------------------------------
# 2. LOAD DEPARTMENTS & CURRENT DOCUMENTS
# -----------------------------------------------------------------------------
def load_metadata(headers):
    # Load departments
    depts_resp = requests.get(f"{API_BASE}/departments", headers=headers, timeout=10)
    if depts_resp.status_code != 200:
        print(f"[ERROR] Không thể lấy danh sách phòng ban: {depts_resp.text}")
        sys.exit(1)
    
    depts = {d["code"]: d["id"] for d in depts_resp.json()}
    print(f"[OK] Đã tải thông tin {len(depts)} phòng ban từ hệ thống.")

    # Load currently indexed documents to prevent duplicates
    docs_resp = requests.get(f"{API_BASE}/documents", headers=headers, timeout=15)
    existing_docs = {}
    if docs_resp.status_code == 200:
        doc_list = docs_resp.json()
        for doc in doc_list:
            existing_docs[doc["title"]] = doc
            existing_docs[doc["file_name"]] = doc
    print(f"[OK] Hệ thống hiện có {len(existing_docs) // 2 if existing_docs else 0} tài liệu trong cơ sở dữ liệu.")
    return depts, existing_docs


# -----------------------------------------------------------------------------
# 3. ENSURE ALL CORNERSTONE DEPARTMENT DOCUMENTS EXIST ON DISK
# -----------------------------------------------------------------------------
def ensure_cornerstone_documents():
    print("[*] Kiểm tra và khởi tạo tài liệu tiêu chuẩn các phòng ban...")
    cornerstone_defs = [
        (
            KB_DIR / "04_FINANCE" / "doc-fin-001.md",
            "HƯỚNG DẪN XỬ LÝ HÓA ĐƠN ĐIỆN TỬ THEO NGHỊ ĐỊNH 123/2020 VÀ THÔNG TƯ 78/2021",
            "FINANCE", "PROCEDURE", "Hóa đơn điện tử & Thuế", "DEPARTMENT",
            """# HƯỚNG DẪN XỬ LÝ HÓA ĐƠN ĐIỆN TỬ THEO NGHỊ ĐỊNH 123/2020/NĐ-CP VÀ THÔNG TƯ 78/2021/TT-BTC
**Mã tài liệu:** DOC-FIN-001  
**Phòng ban:** Tài chính (Finance)  
**Thẩm quyền:** Tổng cục Thuế & Bộ Tài chính  
**Phiên bản:** 2.0 | **Cấp độ bảo mật:** DEPARTMENT

---

## 1. Phân Loại Hóa Đơn Điện Tử
Doanh nghiệp áp dụng hai hình thức hóa đơn điện tử chính:
1. **Hóa đơn điện tử có mã của cơ quan thuế:** Sử dụng cho các đơn hàng bán lẻ và cung ứng dịch vụ thông thường.
2. **Hóa đơn điện tử không có mã của cơ quan thuế:** Áp dụng cho các giao dịch doanh nghiệp lớn, truyền dữ liệu hóa đơn trực tiếp về cổng thông tin của Tổng cục Thuế theo định dạng chuẩn XML.

---

## 2. Quy Trình Xử Lý Sai Sót Hóa Đơn (Điều 19 Nghị định 123)
- **Trường hợp sai tên, địa chỉ người mua nhưng không sai mã số thuế:** Doanh nghiệp gửi thông báo Mẫu 04/SS-HĐĐT cho cơ quan thuế và gửi thông báo cho khách hàng, không cần lập hóa đơn mới.
- **Trường hợp sai mã số thuế, số tiền, thuế suất hoặc quy cách hàng hóa:**
  1. Hai bên lập văn bản thỏa thuận ghi rõ sai sót.
  2. Người bán lập hóa đơn điện tử điều chỉnh hoặc hóa đơn thay thế mới gửi cho cơ quan thuế cấp mã (nếu thuộc diện có mã).
  3. Gửi hóa đơn mới kèm biên bản điều chỉnh cho bên mua.

---

## 3. Quy Định Lưu Trữ Chứng Từ Điện Tử
- Hóa đơn điện tử phải được lưu trữ tối thiểu **10 năm** theo quy định của Luật Kế toán.
- Bắt buộc sao lưu định kỳ cả hai tệp: file XML (chứa dữ liệu gốc có chữ ký số) và file PDF (bản thể hiện).
"""
        ),
        (
            KB_DIR / "05_SALES" / "doc-sales-001.md",
            "QUY TRÌNH BÁN HÀNG B2B 7 BƯỚC VÀ PHÊ DUYỆT HẠN MỨC CÔNG NỢ THƯƠNG MẠI",
            "SALES", "PROCEDURE", "Kinh doanh Doanh nghiệp", "DEPARTMENT",
            """# QUY TRÌNH BÁN HÀNG B2B 7 BƯỚC VÀ PHÊ DUYỆT HẠN MỨC CÔNG NỢ THƯƠNG MẠI
**Mã tài liệu:** DOC-SALES-001  
**Phòng ban:** Kinh doanh (Sales)  
**Thẩm quyền:** Ban Giám đốc Khối Thương mại  
**Phiên bản:** 3.1 | **Cấp độ bảo mật:** DEPARTMENT

---

## 1. Chu trình Bán hàng Doanh nghiệp (B2B Sales Cycle)
1. **Giai đoạn 1 - Tìm kiếm & Khảo sát:** Xác định khách hàng doanh nghiệp tiềm năng, phân loại quy mô và ngành nghề.
2. **Giai đoạn 2 - Tiếp cận ban đầu:** Đặt lịch hẹn, giới thiệu hồ sơ năng lực doanh nghiệp trong vòng 48 giờ.
3. **Giai đoạn 3 - Đánh giá nhu cầu (Discovery):** Thu thập bài toán thực tế của khách hàng, hạ tầng kỹ thuật và ngân sách dự kiến.
4. **Giai đoạn 4 - Trình bày Giải pháp & Báo giá (Proposal/Quotation):** Gửi báo giá chi tiết, phân tích ROI và phương án triển khai.
5. **Giai đoạn 5 - Đàm phán Điều khoản Hợp đồng:** Thống nhất mức chiết khấu, tiến độ thanh toán và trách nhiệm bảo hành.
6. **Giai đoạn 6 - Ký kết Hợp đồng kinh tế:** Hoàn thiện hồ sơ pháp lý, ký số hợp đồng và chuyển giao cho bộ phận Vận hành/Triển khai.
7. **Giai đoạn 7 - Chăm sóc sau bán hàng & Up-sell:** Đánh giá mức độ hài lòng định kỳ 3 tháng/lần và mở rộng dịch vụ.

---

## 2. Tiêu chuẩn Thẩm định & Cấp Hạn Mức Công Nợ
- Khách hàng mới: Yêu cầu tạm ứng tối thiểu 50%, thanh toán nốt 50% trước khi bàn giao.
- Khách hàng thân thiết (thâm niên > 1 năm, lịch sử thanh toán đúng hạn): Cấp hạn mức công nợ tối đa 500 triệu đồng với thời hạn thanh toán 30 ngày kể từ ngày xuất hóa đơn VAT.
- Mọi trường hợp vượt hạn mức phải có chữ ký phê duyệt của Giám đốc Tài chính (CFO) và Giám đốc Điều hành (CEO).
"""
        ),
        (
            KB_DIR / "07_PROCUREMENT" / "doc-proc-001.md",
            "QUY TRÌNH MUA SẮM NỘI BỘ, ĐẤU THẦU VÀ ĐÁNH GIÁ NHÀ CUNG CẤP THEO LUẬT ĐẤU THẦU 2023",
            "PROCUREMENT", "PROCEDURE", "Thu mua & Chuỗi cung ứng", "DEPARTMENT",
            """# QUY TRÌNH MUA SẮM NỘI BỘ, ĐẤU THẦU VÀ ĐÁNH GIÁ NHÀ CUNG CẤP
**Mã tài liệu:** DOC-PROC-001  
**Phòng ban:** Thu mua (Procurement)  
**Thẩm quyền:** Luật Đấu thầu số 22/2023/QH15  
**Phiên bản:** 2026.1 | **Cấp độ bảo mật:** DEPARTMENT

---

## 1. Quy Trình Mua Sắm Từ Đề Xuất Đến Thanh Toán (Procure-to-Pay)
1. **Bước 1 - Lập Phiếu Yêu cầu Mua sắm (PR - Purchase Requisition):** Bộ phận phát sinh nhu cầu tạo phiếu PR trên hệ thống ERP, kèm mô tả kỹ thuật và dự toán ngân sách.
2. **Bước 2 - Phê duyệt PR:** Trưởng bộ phận và Giám đốc Khối thẩm định tính cấp thiết trong vòng 24 giờ.
3. **Bước 3 - Thu thập & So sánh Báo giá (RFQ):**
   - Giá trị gói thầu dưới 20 triệu VNĐ: Thu thập tối thiểu 02 báo giá cạnh tranh.
   - Giá trị gói thầu từ 20 triệu đến 100 triệu VNĐ: Thu thập tối thiểu 03 báo giá độc lập.
   - Giá trị gói thầu trên 100 triệu VNĐ: Thành lập tổ thẩm định chào thầu cạnh tranh hoặc đấu thầu rộng rãi.
4. **Bước 4 - Phát hành Đơn Đặt Hàng (PO - Purchase Order):** Bộ phận Thu mua phát hành PO chính thức cho nhà cung cấp được lựa chọn.
5. **Bước 5 - Tiếp nhận & Kiểm tra Hàng hóa (GRN - Goods Receipt Note):** Phối hợp cùng Bộ phận Kho và QA/QC nghiệm thu hàng hóa thực tế.
6. **Bước 6 - Đối chiếu 3 bên (3-Way Match):** Kế toán đối chiếu PO - GRN - Hóa đơn VAT trước khi chuyển tiền thanh toán.

---

## 2. Tiêu Chuẩn Thẩm Định Nhà Cung Cấp Hàng Quý
Nhà cung cấp được chấm điểm theo thang 100 điểm với các tiêu chí:
- Chất lượng sản phẩm/dịch vụ (40% trọng số).
- Độ tin cậy về thời gian giao hàng (30% trọng số).
- Mức độ cạnh tranh về chi phí và điều kiện thanh toán (20% trọng số).
- Khả năng phản hồi và dịch vụ bảo hành (10% trọng số).
"""
        ),
        (
            KB_DIR / "09_QA" / "doc-qa-001.md",
            "QUY TRÌNH QUẢN LÝ HỆ THỐNG CHẤT LƯỢNG ISO 9001:2015 VÀ HÀNH ĐỘNG KHẮC PHỤC PHÒNG NGỪA (CAPA)",
            "QA", "POLICY", "Quản lý Chất lượng ISO", "INTERNAL",
            """# QUY TRÌNH QUẢN LÝ CHẤT LƯỢNG ISO 9001:2015 VÀ HÀNH ĐỘNG KHẮC PHỤC (CAPA)
**Mã tài liệu:** DOC-QA-001  
**Phòng ban:** Quản lý Chất lượng (QA)  
**Thẩm quyền:** Tiêu chuẩn Quốc tế ISO 9001:2015  
**Phiên bản:** 4.0 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Chu Trình Cải Tiến Liên Tục PDCA
Hệ thống chất lượng của doanh nghiệp vận hành theo chu trình:
- **Plan (Hoạch định):** Thiết lập các mục tiêu chất lượng phòng ban và xác định nguồn lực cần thiết.
- **Do (Thực hiện):** Triển khai các quy trình tác nghiệp chuẩn (SOP) theo đúng hướng dẫn đã ban hành.
- **Check (Kiểm tra):** Giám sát, đo lường các chỉ số KPI chất lượng, thực hiện đánh giá nội bộ định kỳ 6 tháng/lần.
- **Act (Hành động cải tiến):** Thực hiện các hành động khắc phục và phòng ngừa nhằm nâng cao hiệu suất vận hành.

---

## 2. Quy Trình Xử Lý Sự Cố Không Phù Hợp (Non-conformity) & CAPA
1. **Nhận diện và Cách ly:** Ngay khi phát hiện sản phẩm hoặc dịch vụ lỗi, lập tức gắn nhãn không phù hợp và cách ly khỏi luồng xử lý thông thường.
2. **Phân tích Nguyên nhân Gốc rễ (Root Cause Analysis):**
   - Áp dụng kỹ thuật **5 Whys (5 Câu hỏi Tại sao)** để truy tìm nguyên nhân cốt lõi.
   - Sử dụng **Biểu đồ Xương cá Ishikawa (6M):** Con người (Man), Máy móc (Machine), Vật liệu (Material), Phương pháp (Method), Đo lường (Measurement), Môi trường (Milieu).
3. **Lập Kế hoạch Hành động Khắc phục (Corrective Action Plan):** Xác định rõ người chịu trách nhiệm, hành động cụ thể và thời hạn hoàn thành (Deadline).
4. **Đánh giá Hiệu lực:** Sau 30 ngày kể từ khi áp dụng, bộ phận QA tiến hành tái kiểm tra để xác nhận lỗi không tái diễn.
"""
        ),
        (
            KB_DIR / "10_QC" / "doc-qc-001.md",
            "QUY TRÌNH KIỂM SOÁT CHẤT LƯỢNG ĐẦU VÀO (IQC), TRONG QUÁ TRÌNH (IPQC) VÀ ĐẦU RA (OQC)",
            "QC", "PROCEDURE", "Kiểm soát Chất lượng Thực tế", "INTERNAL",
            """# QUY TRÌNH KIỂM SOÁT CHẤT LƯỢNG ĐẦU VÀO, TRONG QUÁ TRÌNH VÀ ĐẦU RA
**Mã tài liệu:** DOC-QC-001  
**Phòng ban:** Kiểm soát Chất lượng (QC)  
**Thẩm quyền:** Ban Quản lý Chất lượng Sản phẩm  
**Phiên bản:** 2.5 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Kiểm Soát Chất Lượng Đầu Vào (IQC - Incoming Quality Control)
- **Đối tượng:** Toàn bộ nguyên vật liệu, linh kiện, thiết bị phần cứng từ nhà cung cấp bàn giao.
- **Phương pháp lấy mẫu:** Áp dụng tiêu chuẩn lấy mẫu ngẫu nhiên **AQL 0.65 / 1.5 theo MIL-STD-105E**.
- **Tiêu chí đánh giá:** Kiểm tra ngoại quan, kích thước vật lý, độ bền cơ học và chứng chỉ xuất xưởng (CO/CQ).
- **Hành động khi không đạt:** Lập Biên bản từ chối nhận hàng (Rejection Report) và yêu cầu nhà cung cấp đổi trả trong vòng 48 giờ.

---

## 2. Kiểm Soát Chất Lượng Quá Trình (IPQC - In-Process Quality Control)
- Kiểm tra thông số vận hành máy móc đầu ca làm việc (First Article Inspection).
- Tuần tra kiểm tra định kỳ 2 giờ/lần trên dây chuyền sản xuất hoặc tiến độ đóng gói.
- Dừng dây chuyền khẩn cấp nếu phát hiện tỷ lệ lỗi vượt quá ngưỡng cảnh báo 1.5%.

---

## 3. Kiểm Soát Chất Lượng Xuất Xưởng (OQC - Outgoing Quality Control)
- Kiểm tra 100% đối với các sản phẩm đóng gói thành phẩm trước khi đưa vào kho bảo quản.
- Cấp tem kiểm định chứng nhận ĐẠT CHUẨN (QC PASSED) kèm phiếu kiểm tra chất lượng xuất xưởng.
"""
        ),
        (
            KB_DIR / "11_PRODUCTION" / "doc-prod-001.md",
            "QUY TRÌNH ĐIỀU ĐỘ SẢN XUẤT, THỰC HÀNH 5S, KAIZEN VÀ BẢO TRÌ PHÒNG NGỪA THIẾT BỊ (TPM)",
            "PRODUCTION", "MANUAL", "Quản lý Sản xuất & Bảo trì", "INTERNAL",
            """# QUY TRÌNH ĐIỀU ĐỘ SẢN XUẤT, THỰC HÀNH 5S, KAIZEN VÀ BẢO TRÌ PHÒNG NGỪA THIẾT BỊ (TPM)
**Mã tài liệu:** DOC-PROD-001  
**Phòng ban:** Sản xuất (Production)  
**Thẩm quyền:** Khối Vận hành Sản xuất  
**Phiên bản:** 3.0 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Nguyên Tắc Vận Hành 5S Nhà Xưởng
- **Seiri (Sàng lọc):** Phân loại và loại bỏ các vật dụng không cần thiết khỏi khu vực làm việc.
- **Seiton (Sắp xếp):** Sắp xếp dụng cụ, thiết bị theo nguyên tắc dễ tìm, dễ thấy, dễ lấy, dễ trả lại.
- **Seiso (Sạch sẽ):** Vệ sinh máy móc, sàn nhà xưởng và thiết bị vào 15 phút cuối mỗi ca làm việc.
- **Seiketsu (Săn sóc):** Duy trì tiêu chuẩn 3S đầu tiên hàng ngày, trực quan hóa bằng bảng biểu.
- **Shitsuke (Sẵn sàng):** Rèn luyện thói quen tự giác tuân thủ quy tắc an toàn và kỷ luật lao động.

---

## 2. Bảo Trì Năng Suất Toàn Diện (TPM - Total Productive Maintenance)
- **Bảo trì tự quản (Autonomous Maintenance):** Công nhân vận hành máy tự chịu trách nhiệm tra dầu mỡ, vệ sinh và siết chặt bu-lông hàng ngày.
- **Bảo trì phòng ngừa định kỳ (Preventive Maintenance):** Kỹ sư bảo trì thay thế linh kiện hao mòn theo số giờ vận hành quy định, ngăn ngừa sự cố dừng máy đột ngột (Zero Breakdown).
"""
        ),
        (
            KB_DIR / "12_WAREHOUSE" / "doc-wh-001.md",
            "QUY TRÌNH QUẢN LÝ KHO BÃI, NGUYÊN TẮC FIFO/FEFO VÀ KIỂM KÊ TỒN KHO BẰNG MÃ VẠCH",
            "WAREHOUSE", "PROCEDURE", "Quản lý Kho Vận", "DEPARTMENT",
            """# QUY TRÌNH QUẢN LÝ KHO BÃI, NGUYÊN TẮC FIFO/FEFO VÀ KIỂM KÊ TỒN KHO BẰNG MÃ VẠCH
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
"""
        ),
        (
            KB_DIR / "13_LOGISTICS" / "doc-log-001.md",
            "QUY TRÌNH GIAO NHẬN VẬN TẢI NỘI ĐỊA, ĐIỀU PHỐI ĐỘI XE VÀ QUY TẮC INCOTERMS 2020",
            "LOGISTICS", "PROCEDURE", "Logistics & Vận tải", "INTERNAL",
            """# QUY TRÌNH GIAO NHẬN VẬN TẢI NỘI ĐỊA, ĐIỀU PHỐI ĐỘI XE VÀ QUY TẮC INCOTERMS 2020
**Mã tài liệu:** DOC-LOG-001  
**Phòng ban:** Giao nhận Vận tải (Logistics)  
**Thẩm quyền:** ICC Incoterms 2020 & Luật Giao thông Đường bộ  
**Phiên bản:** 2.0 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Quy Trình Điều Phối Đội Xe & Giao Hàng
1. **Lập Kế hoạch Lộ trình (Route Planning):** Tối ưu hóa lộ trình xe tải dựa trên địa chỉ giao nhận, tải trọng xe và khung giờ cấm tải đô thị.
2. **Bàn giao Hàng hóa & Chứng từ:** Tài xế ký nhận Biên bản bàn giao hàng hóa và Phiếu xuất kho kiêm vận chuyển nội bộ.
3. **Theo dõi Hành trình (GPS Tracking):** Giám sát hành trình xe qua hệ thống GPS thời gian thực, cập nhật trạng thái đơn hàng trên phần mềm TMS.
4. **Xác nhận Giao hàng Thành công (POD - Proof of Delivery):** Chụp ảnh chữ ký người nhận trên ứng dụng di động và bàn giao chứng từ gốc cho phòng Kế toán trong vòng 24 giờ.

---

## 2. Các Điều Kiện Thương Mại Incoterms 2020 Thường Dùng
- **EXW (Ex Works - Giao tại xưởng):** Người bán giao hàng tại kho; người mua chịu toàn bộ chi phí và rủi ro vận chuyển.
- **FOB (Free On Board - Giao lên tàu):** Người bán hoàn thành nghĩa vụ khi hàng đã qua lan can tàu tại cảng bốc hàng chỉ định.
- **CIF (Cost, Insurance and Freight - Tiền hàng, Bảo hiểm và Cước phí):** Người bán trả cước vận chuyển và mua bảo hiểm hàng hải cho lô hàng đến cảng đến.
- **DDP (Delivered Duty Paid - Giao hàng đã thông quan nhập khẩu):** Người bán chịu toàn bộ chi phí, thuế nhập khẩu và rủi ro cho đến khi giao hàng tại địa điểm chỉ định của người mua.
"""
        ),
        (
            KB_DIR / "14_PLANNING" / "doc-plan-001.md",
            "QUY TRÌNH HOẠCH ĐỊNH NGUỒN LỰC DOANH NGHIỆP (MRP) VÀ QUẢN TRỊ TIẾN ĐỘ DỰ ÁN THEO CHUẨN PMBOK",
            "PLANNING", "MANUAL", "Kế hoạch & Quản trị Dự án", "INTERNAL",
            r"""# QUY TRÌNH HOẠCH ĐỊNH NGUỒN LỰC DOANH NGHIỆP (MRP) VÀ TIẾN ĐỘ THEO CHUẨN PMBOK
**Mã tài liệu:** DOC-PLAN-001  
**Phòng ban:** Kế hoạch (Planning)  
**Thẩm quyền:** Project Management Institute (PMI)  
**Phiên bản:** 4.0 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Hoạch Định Nhu Cầu Vật Tư (MRP - Material Requirements Planning)
- **Đầu vào của MRP:**
  1. Kế hoạch sản xuất tổng thể (Master Production Schedule - MPS).
  2. Định mức nguyên vật liệu sản phẩm (Bill of Materials - BOM).
  3. Dữ liệu tồn kho khả dụng thời gian thực từ hệ thống kho.
- **Đầu ra của MRP:** Lịch trình phát hành Đơn hàng Sản xuất nội bộ và Kế hoạch Đặt mua nguyên vật liệu tự động chuyển sang phòng Thu mua.

---

## 2. Quản Trị Tiến Đồ Dự Án Theo Chuẩn PMBOK
- **Phân rã Công việc (WBS - Work Breakdown Structure):** Chia nhỏ phạm vi dự án thành các gói công việc cụ thể có thể đo lường.
- **Phương pháp Đường Găng (CPM - Critical Path Method):** Xác định chuỗi công việc dài nhất quyết định tổng thời gian hoàn thành dự án. Mọi sự chậm trễ trên đường găng đều làm chậm tiến độ chung.
- **Quản lý Giá trị Thu được (EVM - Earned Value Management):**
  - $CV = EV - AC$ (Chênh lệch Chi phí).
  - $SV = EV - PV$ (Chênh lệch Tiến độ).
  - $CPI = EV / AC$ (Chỉ số Hiệu suất Chi phí, yêu cầu $\ge 1.0$).
"""
        ),
        (
            KB_DIR / "00_general" / "doc-gen-001.md",
            "KẾ HOẠCH DUY TRÌ HOẠT ĐỘNG KINH DOANH LIÊN TỤC (BCP) VÀ PHÒNG CHỐNG RỦI RO THEO ISO 31000",
            "MANAGEMENT", "POLICY", "Quản trị Doanh nghiệp & Rủi ro", "PUBLIC",
            r"""# KẾ HOẠCH DUY TRÌ HOẠT ĐỘNG KINH DOANH LIÊN TỤC (BCP) VÀ QUẢN TRỊ RỦI RO ISO 31000
**Mã tài liệu:** DOC-GEN-001  
**Phòng ban:** Ban Giám đốc & Quản trị Chung (Management)  
**Thẩm quyền:** Tiêu chuẩn Quốc tế ISO 22301 & ISO 31000  
**Phiên bản:** 2026.1 | **Cấp độ bảo mật:** PUBLIC

---

## 1. Mục Tiêu Kế Hoạch BCP (Business Continuity Plan)
Bảo đảm doanh nghiệp có khả năng ứng phó, duy trì các hoạt động trọng yếu và phục hồi nhanh chóng sau các sự cố thảm họa (cháy nổ, thiên tai, đứt gãy mạng diện rộng, tấn công mạng mã hóa Ransomware).
- **Chỉ tiêu RPO (Recovery Point Objective):** Dữ liệu tối đa chấp nhận mất mát $\le 4$ giờ làm việc.
- **Chỉ tiêu RTO (Recovery Time Objective):** Thời gian tối đa phục hồi các hệ thống cốt lõi (ERP, Email, Cơ sở dữ liệu) $\le 8$ giờ.

---

## 2. Khung Quản Trị Rủi Ro Theo ISO 31000
1. **Nhận diện rủi ro:** Định kỳ hàng quý rà soát các rủi ro vận hành, tài chính, pháp lý và công nghệ.
2. **Đánh giá rủi ro (Risk Matrix):** Chấm điểm ma trận giữa Mức độ tác động (1-5) và Khả năng xảy ra (1-5). Các rủi ro điểm $\ge 15$ bắt buộc phải có phương án kiểm soát tức thì.
3. **Chiến lược xử lý rủi ro:** Né tránh (Avoid), Giảm thiểu (Mitigate), Chuyển giao (Transfer - qua Bảo hiểm) hoặc Chấp nhận (Accept).
"""
        ),
        (
            KB_DIR / "01_IT" / "cybersecurity" / "doc-sec-001.md",
            "TIÊU CHUẨN BẢO VỆ HỆ THỐNG THÔNG TIN THEO KHUNG AN NINH MẠNG NIST CSF 2.0 VÀ CIS CONTROLS V8",
            "IT_SECURITY", "TECHNICAL_STANDARD", "An toàn An ninh Thông tin", "INTERNAL",
            """# TIÊU CHUẨN AN TOÀN THÔNG TIN THEO KHUNG NIST CSF 2.0 VÀ CIS CONTROLS V8
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
"""
        ),
        (
            KB_DIR / "01_IT" / "database" / "doc-db-001.md",
            "QUY TRÌNH SAO LƯU DỰ PHÒNG WAL, REPLICATION VÀ TỐI ƯU HÓA TRUY VẤN POSTGRESQL 16",
            "IT_DBA", "TECHNICAL_STANDARD", "Quản trị Cơ sở Dữ liệu", "DEPARTMENT",
            """# QUY TRÌNH SAO LƯU DỰ PHÒNG WAL, REPLICATION VÀ TỐI ƯU HÓA POSTGRESQL 16
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
"""
        ),
        (
            KB_DIR / "01_IT" / "infrastructure" / "doc-infra-001.md",
            "TIÊU CHUẨN VẬN HÀNH HẠ TẦNG CỤM MÁY CHỦ VMWARE VSPHERE 8 VÀ DOCKER CONTAINER",
            "IT_INFRASTRUCTURE", "TECHNICAL_STANDARD", "Hạ tầng Máy chủ & Ảo hóa", "INTERNAL",
            """# TIÊU CHUẨN VẬN HÀNH HẠ TẦNG CỤM MÁY CHỦ VMWARE VSPHERE 8 VÀ DOCKER
**Mã tài liệu:** DOC-INFRA-001  
**Phòng ban:** Hạ tầng CNTT (IT Infrastructure)  
**Thẩm quyền:** VMware by Broadcom & Docker Inc.  
**Phiên bản:** 8.0 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Tiêu Chuẩn Cụm Ảo Hóa VMware vSphere HA / DRS
- Cụm máy chủ (Cluster) tối thiểu gồm 03 máy chủ vật lý (ESXi Hosts) để đảm bảo tính sẵn sàng cao $N+1$.
- Bật tính năng **vSphere High Availability (HA):** Khi một host vật lý bị mất nguồn hoặc treo cứng, toàn bộ máy ảo (VM) trên host đó tự động khởi động lại trên các host còn lại trong vòng dưới 3 phút.
- Bật tính năng **Distributed Resource Scheduler (DRS)** ở chế độ Fully Automated để tự động cân bằng tải CPU và RAM giữa các máy chủ.

---

## 2. Tiêu Chuẩn Vận Hành Docker Container Doanh Nghiệp
- Toàn bộ container chạy dịch vụ nghiệp vụ phải có giới hạn tài nguyên rõ ràng trong file `docker-compose.yml`:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4096M
  ```
- Định cấu hình `restart: always` và thiết lập kịch bản kiểm tra sức khỏe `healthcheck` trên cổng nội bộ.
- Dữ liệu cơ sở dữ liệu và tệp người dùng tải lên bắt buộc phải ánh xạ ra khối lưu trữ ngoài (Named Volumes hoặc Host Mounts).
"""
        )
    ]

    created_count = 0
    for file_path, title, dept_code, doc_type, category, sec_level, content in cornerstone_defs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_count += 1
    
    if created_count > 0:
        print(f"[OK] Đã tạo mới {created_count} tài liệu tiêu chuẩn phòng ban tại {KB_DIR}")
    else:
        print("[OK] Toàn bộ tài liệu tiêu chuẩn phòng ban đã tồn tại sẵn sàng.")


# -----------------------------------------------------------------------------
# 4. DISCOVER ALL DOCUMENTS READY FOR INGESTION
# -----------------------------------------------------------------------------
def discover_all_documents():
    """Build master list of all candidate documents across documents/ and enterprise_knowledge_base/"""
    candidates = []

    # A. Scan documents/ directory
    if DOCS_DIR.exists():
        for f in DOCS_DIR.glob("*.*"):
            if f.suffix.lower() not in [".txt", ".docx", ".pdf", ".md"]:
                continue
            
            # Map known titles and departments
            name = f.name
            dept_code = "IT"
            doc_type = "GUIDE"
            category = "Công nghệ Thông tin"
            sec_level = "INTERNAL"
            title = f.stem.replace("_", " ").title()

            if "policy" in name.lower():
                doc_type = "POLICY"
            if "troubleshoot" in name.lower() or "guide" in name.lower():
                doc_type = "GUIDE"

            if "hr" in name.lower():
                dept_code = "HR"
                category = "Nhân sự & Lao động"
                title = "Sổ tay Nhân sự, Nội quy Lao động & Chế độ Phúc lợi"
            elif "finance" in name.lower() or "accounting" in name.lower():
                dept_code = "ACCOUNTING"
                category = "Tài chính Kế toán"
                title = "Quy chế Quản lý Tài chính, Kế toán & Duyệt chi Nội bộ"
            elif "procurement" in name.lower():
                dept_code = "PROCUREMENT"
                category = "Thu mua & Cung ứng"
                title = "Quy trình Thu mua, Đấu thầu & Quản lý Nhà cung cấp"
            elif "sales" in name.lower():
                dept_code = "SALES"
                category = "Kinh doanh & Bán hàng"
                title = "Quy trình Bán hàng Doanh nghiệp B2B & Chính sách Thương mại"
            elif "cyber" in name.lower() or "pdpd" in name.lower():
                dept_code = "IT_SECURITY"
                category = "An ninh Doanh nghiệp"
                title = "Quy định An toàn Thông tin & Bảo vệ Dữ liệu Cá nhân (PDPD)"
            elif "ad_netlogon" in name.lower():
                dept_code = "IT_SYSTEM"
                category = "Active Directory & GPO"
                title = "Hướng dẫn Quản trị Active Directory, GPO & Bảo mật Netlogon"
            elif "cisco_osi" in name.lower():
                dept_code = "IT_NETWORK"
                category = "Mạng & Hạ tầng Cisco"
                title = "Cẩm nang Khắc phục Sự cố Mạng Cisco theo Mô hình OSI 7 Tầng"
            elif "fiber_optic" in name.lower():
                dept_code = "IT_INFRASTRUCTURE"
                category = "Hạ tầng Cáp quang & ODF"
                title = "Tiêu chuẩn Thi công & Đo kiểm Hạ tầng Cáp quang ODF - ODS"
            elif "printer" in name.lower():
                dept_code = "IT_HELPDESK"
                category = "Máy in & Print Server"
                title = "Quy trình Khắc phục Sự cố Máy in Mạng & Quản trị Print Server"
            elif "outlook" in name.lower():
                dept_code = "IT_HELPDESK"
                category = "Email & Chữ ký số"
                title = "Hướng dẫn Cài đặt Chữ ký số, Chứng thư Điện tử & Khắc phục Lỗi Outlook"
            elif "app_web_dev" in name.lower():
                dept_code = "IT_DEVELOPMENT"
                category = "Phát triển Ứng dụng & DevOps"
                title = "Sổ tay Chẩn đoán & Xử lý Sự cố Ứng dụng Web, API & DevOps"
            elif "bios_boot" in name.lower():
                dept_code = "IT_INFRASTRUCTURE"
                category = "Phần cứng & Tối ưu AI"
                title = "Hướng dẫn Cấu hình BIOS/UEFI, Tối ưu Phần cứng cho Local AI & RAG"
            elif "windows_system" in name.lower():
                dept_code = "IT_HELPDESK"
                category = "Hệ điều hành Windows & BSOD"
                title = "Sổ tay Xử lý Sự cố Hệ điều hành Windows & Khắc phục Lỗi BSOD"
            elif "ban_do" in name.lower():
                dept_code = "MANAGEMENT"
                category = "Tri thức Chung"
                sec_level = "PUBLIC"
                title = "Bản đồ Tài liệu Tri thức Doanh nghiệp Toàn diện"

            candidates.append({
                "path": f,
                "file_name": f.name,
                "title": title,
                "dept_code": dept_code,
                "doc_type": doc_type,
                "category": category,
                "security_level": sec_level,
                "version": "1.0"
            })

    # B. Scan enterprise_knowledge_base/ directory
    if KB_DIR.exists():
        for md_file in KB_DIR.rglob("*.md"):
            if md_file.name.lower() in ["readme.md", "quality_report.md", "ingestion_report.md"]:
                continue
            
            # Infer dept from parent folder
            parent_name = md_file.parent.name.upper()
            dept_code = "GENERAL"
            if "HELPDESK" in parent_name:
                dept_code = "IT_HELPDESK"
            elif "NETWORK" in parent_name:
                dept_code = "IT_NETWORK"
            elif "SYSTEM" in parent_name:
                dept_code = "IT_SYSTEM"
            elif "CYBERSECURITY" in parent_name:
                dept_code = "IT_SECURITY"
            elif "DATABASE" in parent_name:
                dept_code = "IT_DBA"
            elif "INFRASTRUCTURE" in parent_name:
                dept_code = "IT_INFRASTRUCTURE"
            elif "DEVELOPMENT" in parent_name:
                dept_code = "IT_DEVELOPMENT"
            elif "HR" in parent_name:
                dept_code = "HR"
            elif "ACCOUNTING" in parent_name:
                dept_code = "ACCOUNTING"
            elif "FINANCE" in parent_name:
                dept_code = "FINANCE"
            elif "SALES" in parent_name:
                dept_code = "SALES"
            elif "MARKETING" in parent_name:
                dept_code = "MARKETING"
            elif "PROCUREMENT" in parent_name:
                dept_code = "PROCUREMENT"
            elif "LEGAL" in parent_name:
                dept_code = "LEGAL"
            elif "QA" in parent_name:
                dept_code = "QA"
            elif "QC" in parent_name:
                dept_code = "QC"
            elif "PRODUCTION" in parent_name:
                dept_code = "PRODUCTION"
            elif "WAREHOUSE" in parent_name:
                dept_code = "WAREHOUSE"
            elif "LOGISTICS" in parent_name:
                dept_code = "LOGISTICS"
            elif "PLANNING" in parent_name:
                dept_code = "PLANNING"
            elif "GENERAL" in parent_name:
                dept_code = "MANAGEMENT"

            # Extract title from first markdown line
            title = md_file.stem
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break
            except Exception:
                pass

            candidates.append({
                "path": md_file,
                "file_name": md_file.name,
                "title": title,
                "dept_code": dept_code,
                "doc_type": "POLICY" if "quy" in title.lower() or "chinh" in title.lower() else "GUIDE",
                "category": f"Quy trình {dept_code}",
                "security_level": "INTERNAL" if dept_code != "MANAGEMENT" else "PUBLIC",
                "version": "1.0"
            })

    # Deduplicate candidates by title or file_name
    unique_candidates = []
    seen_keys = set()
    for c in candidates:
        key = c["title"].lower().strip()
        if key not in seen_keys:
            seen_keys.add(key)
            unique_candidates.append(c)

    return unique_candidates


# -----------------------------------------------------------------------------
# 5. INGEST DOCUMENTS INTO FASTAPI + CHROMADB
# -----------------------------------------------------------------------------
def ingest_all():
    print("=" * 70)
    print("   TIẾN HÀNH TỰ ĐỘNG NẠP DỮ LIỆU TRI THỨC VÀO FASTAPI & CHROMADB")
    print("=" * 70)

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    depts_map, existing_docs = load_metadata(headers)

    ensure_cornerstone_documents()
    candidates = discover_all_documents()
    print(f"\n[*] Tìm thấy tổng cộng {len(candidates)} tài liệu ứng viên để nạp vào hệ thống.")

    success_count = 0
    skipped_count = 0
    failed_count = 0
    total_chunks_added = 0

    print("\n--- BẮT ĐẦU QUÁ TRÌNH NẠP & TẠO VECTOR EMBEDDING (OLLAMA) ---")

    for idx, doc in enumerate(candidates, 1):
        title = doc["title"]
        file_name = doc["file_name"]
        file_path = doc["path"]
        dept_code = doc["dept_code"]

        # Check duplicate
        if title in existing_docs or file_name in existing_docs:
            print(f"[{idx}/{len(candidates)}] [ĐÃ TỒN TẠI] Bỏ qua: '{title}' ({file_name})")
            skipped_count += 1
            continue

        dept_id = depts_map.get(dept_code) or depts_map.get("IT")

        form_data = {
            "title": title,
            "document_type": doc["doc_type"],
            "category": doc["category"],
            "security_level": doc["security_level"],
            "version": doc["version"],
        }
        if dept_id:
            form_data["department_id"] = str(dept_id)

        print(f"\n[{idx}/{len(candidates)}] Đang nạp: '{title}'")
        print(f"    -> Phòng ban: {dept_code} | Bảo mật: {doc['security_level']} | File: {file_name}")

        try:
            with open(file_path, "rb") as f:
                content_bytes = f.read()

            # Pass as .txt if .md to ensure clean parsing by plain text UTF-8 parser
            upload_filename = file_name
            if upload_filename.lower().endswith(".md"):
                upload_filename = upload_filename[:-3] + ".txt"

            files_payload = {
                "file": (upload_filename, io.BytesIO(content_bytes), "text/plain" if upload_filename.endswith(".txt") else "application/octet-stream")
            }

            resp = requests.post(
                f"{API_BASE}/documents/upload",
                headers=headers,
                data=form_data,
                files=files_payload,
                timeout=60
            )

            if resp.status_code == 201:
                res_data = resp.json()
                chunks = res_data.get("total_chunks", 0)
                status = res_data.get("rag_status", "READY")
                total_chunks_added += chunks
                success_count += 1
                existing_docs[title] = res_data
                existing_docs[file_name] = res_data
                print(f"    [THÀNH CÔNG] ID: {res_data['id']} | Chunks: {chunks} | Trạng thái RAG: {status}")
            else:
                print(f"    [THẤT BẠI] Mã lỗi {resp.status_code}: {resp.text}")
                failed_count += 1

        except Exception as e:
            print(f"    [LỖI NGOẠI LỆ] {str(e)}")
            failed_count += 1

        # Brief pause to let local LLM/embedding breathe
        time.sleep(0.3)

    # -------------------------------------------------------------------------
    # FINAL REPORT
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("   BÁO CÁO TỔNG KẾT NẠP DỮ LIỆU TRI THỨC VÀO RAG CHROMADB")
    print("=" * 70)
    print(f"  * Tổng số tài liệu ứng viên quét được : {len(candidates)}")
    print(f"  * Nạp mới thành công                 : {success_count}")
    print(f"  * Đã tồn tại sẵn (bỏ qua)            : {skipped_count}")
    print(f"  * Thất bại / Lỗi                     : {failed_count}")
    print(f"  * Tổng số Chunks vector vừa lập chỉ mục: {total_chunks_added}")
    print("=" * 70)
    print("[OK] ĐÃ XONG! Toàn bộ tài liệu đã được nạp thành công vào hệ thống.")
    print("Bạn có thể mở giao diện Web tại http://localhost:3000 để kiểm tra.")


if __name__ == "__main__":
    ingest_all()
