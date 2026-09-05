# ENTERPRISE KNOWLEDGE BASE (KHO TRI THỨC DOANH NGHIỆP 1.000+ TÀI LIỆU)

Kho Tri thức Doanh nghiệp Quy mô Lớn chuẩn hóa phục vụ **Local AI (Ollama Qwen2.5:3b) + RAG Pipeline + ChromaDB Vector Store**.

---

## 1. Tổng Quan Kho Tri Thức

- **Tổng số tài liệu định danh:** **1090 tài liệu**.
- **Số lượng phòng ban bao phủ:** **17 lĩnh vực chuyên trách** (IT HelpDesk, Network, System Admin, Cybersecurity, Infrastructure, Database, DevOps, HR, Kế toán, Tài chính, Kinh doanh, Marketing, Mua sắm, Pháp chế, QA, QC, Sản xuất, Kho bãi, Logistics, Kế hoạch & Quản trị chung).
- **Ngôn ngữ:** Song ngữ Anh - Việt (Tài liệu Kỹ thuật Quốc tế & Hệ thống Văn bản Quy phạm Pháp luật Việt Nam chính thức).
- **Bộ dữ liệu kiểm thử RAG:** **300 câu hỏi chuyên sâu** có đối chiếu kỳ vọng (`rag_test_questions.json`).

---

## 2. Cấu Trúc Thư Mục Kho Tri Thức

```text
enterprise_knowledge_base/
├── 00_general/                 (40 tài liệu: BCP/DR, ISO 31000, Code of Conduct)
├── 01_IT/
│   ├── helpdesk/              (100 tài liệu: Windows 10/11, M365, Hardware, BSOD)
│   ├── network/               (100 tài liệu: Cisco IOS, IETF RFC, VLAN, OSPF, BGP)
│   ├── system/                (100 tài liệu: Windows Server, AD DS, Ubuntu, systemd)
│   ├── infrastructure/        (60 tài liệu: VMware, Docker, Kubernetes, Storage)
│   ├── cybersecurity/         (80 tài liệu: NIST CSF, OWASP Top 10, CIS Controls v8)
│   ├── database/              (40 tài liệu: PostgreSQL 16, MySQL 8, SQL Server)
│   └── development/           (40 tài liệu: Git SCM, CI/CD, Microservices, OpenAPI)
├── 02_HR/                      (70 tài liệu: Bộ luật Lao động, BHXH, KPI, Onboarding)
├── 03_ACCOUNTING/              (40 tài liệu: Luật Kế toán, TT 200/2014, Báo cáo BCTC)
├── 04_FINANCE/                 (30 tài liệu: Hóa đơn điện tử NĐ 123, Thuế TNDN/GTGT)
├── 05_SALES/                   (40 tài liệu: Bán hàng B2B, Hợp đồng, Sales Pipeline)
├── 06_MARKETING/               (20 tài liệu: Kế hoạch Tiếp thị, Content Strategy, SEO)
├── 07_PROCUREMENT/             (50 tài liệu: Luật Đấu thầu 2023, PR/PO, Vendor Audit)
├── 08_LEGAL/                   (60 tài liệu: Luật ATTT, Luật ANM, Nghị định 13 PDPD)
├── 09_QA/                      (50 tài liệu: ISO 9001:2015, FMEA, 7 QC Tools, CAPA)
├── 10_QC/                      (30 tài liệu: IQC, IPQC, OQC, Hiệu chuẩn thiết bị)
├── 11_PRODUCTION/              (50 tài liệu: Quản lý Sản xuất, 5S, Kaizen, Bảo trì TPM)
├── 12_WAREHOUSE/               (30 tài liệu: FIFO/FEFO, Mã vạch Barcode/QR, Kiểm kê)
├── 13_LOGISTICS/               (20 tài liệu: Vận tải, Incoterms 2020, Supply Chain)
├── 14_PLANNING/                (40 tài liệu: PMBOK, Scrum Guide, Hoạch định MRP)
└── metadata/
    ├── documents_manifest.csv  (Danh mục chi tiết 1090 tài liệu chuẩn)
    ├── master_catalog.json     (Định dạng JSON 21 trường metadata)
    ├── sources.csv             (Danh mục hơn 25 nhà phát hành thẩm quyền cao)
    ├── dataset_statistics.json (Báo cáo số liệu thống kê đa chiều)
    ├── rag_test_questions.json (300 câu hỏi kiểm thử đánh giá hệ thống RAG)
    ├── rejected_documents.csv  (Nhật ký loại bỏ tài liệu rác, mã độc, vi phạm PII)
    ├── duplicate_documents.csv (Báo cáo xử lý và loại trừ trùng lặp)
    ├── quality_report.md       (Báo cáo thẩm định chất lượng thang điểm 100)
    └── ingestion_report.md     (Kế hoạch cắt đoạn chunking và nạp ChromaDB)
```

---

## 3. Hướng Dẫn Sử Dụng & Nạp Dữ Liệu

### Xem thống kê tổng thể
Mở tệp `enterprise_knowledge_base/metadata/dataset_statistics.json` để kiểm tra phân bổ số lượng tài liệu, ngôn ngữ và điểm chất lượng.

### Nạp tài liệu vào Local AI RAG
1. Khởi động Docker hoặc Local Dev bằng file `menu.bat` (hoặc `run.bat`).
2. Chạy kịch bản nạp tự động qua API FastAPI:
   ```cmd
   python backend/upload_sample_docs.py
   ```
3. Mở giao diện Web [http://localhost:3000](http://localhost:3000) vào mục **Chat AI** để tra cứu và kiểm thử với bộ câu hỏi trong `rag_test_questions.json`.
