"""Script to upload and index all enterprise sample documents via FastAPI API."""

import os
import sys
import requests

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 1. Login as Admin
login_resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username_or_email": "admin@enterprise.local", "password": "Admin@123456"}
)

if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.text}")
    sys.exit(1)

token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Successfully logged in as Super Admin.")

# Get departments map
depts_resp = requests.get(f"{BASE_URL}/departments", headers=headers)
depts = {d["code"]: d["id"] for d in depts_resp.json()}
print(f"Loaded {len(depts)} departments.")

# List of documents to upload
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documents"))

documents_to_upload = [
    {
        "file_name": "sample_it_policy.txt",
        "title": "Chính sách và Hướng dẫn CNTT Nội bộ Doanh nghiệp 2026",
        "department_code": "IT",
        "document_type": "POLICY",
        "category": "Công nghệ thông tin",
        "security_level": "DEPARTMENT",
        "version": "1.0"
    },
    {
        "file_name": "sample_troubleshooting_handbook.txt",
        "title": "Sổ tay Xử lý Sự cố Kỹ thuật IT HelpDesk, Mạng LAN & Outlook",
        "department_code": "IT",
        "document_type": "GUIDE",
        "category": "IT Support",
        "security_level": "INTERNAL",
        "version": "1.0"
    },
    {
        "file_name": "sample_cyber_security_pdpd.txt",
        "title": "Quy định An toàn Thông tin & Bảo vệ Dữ liệu Cá nhân (PDPD)",
        "department_code": "SECURITY",
        "document_type": "POLICY",
        "category": "An ninh Doanh nghiệp",
        "security_level": "INTERNAL",
        "version": "1.0"
    },
    {
        "file_name": "sample_finance_accounting_policy.txt",
        "title": "Quy chế Quản lý Tài chính, Kế toán & Duyệt chi Nội bộ",
        "department_code": "ACCOUNTING",
        "document_type": "POLICY",
        "category": "Tài chính Kế toán",
        "security_level": "DEPARTMENT",
        "version": "1.0"
    },
    {
        "file_name": "sample_hr_policy.txt",
        "title": "Sổ tay Nhân sự, Nội quy Lao động & Chế độ Phúc lợi",
        "department_code": "HR",
        "document_type": "POLICY",
        "category": "Nhân sự & Lao động",
        "security_level": "INTERNAL",
        "version": "1.0"
    },
    {
        "file_name": "sample_procurement_sourcing_policy.txt",
        "title": "Quy trình Thu mua, Đấu thầu & Quản lý Nhà cung cấp",
        "department_code": "PROCUREMENT",
        "document_type": "PROCEDURE",
        "category": "Thu mua & Cung ứng",
        "security_level": "DEPARTMENT",
        "version": "1.0"
    },
    {
        "file_name": "sample_b2b_sales_commercial_policy.txt",
        "title": "Quy trình Bán hàng Doanh nghiệp B2B & Chính sách Thương mại",
        "department_code": "SALES",
        "document_type": "PROCEDURE",
        "category": "Kinh doanh & Bán hàng",
        "security_level": "DEPARTMENT",
        "version": "1.0"
    },
    {
        "file_name": "Ban_Do_Tai_Lieu_Tri_Thuc_Doanh_Nghiep.docx",
        "title": "Bản đồ Tài liệu Tri thức Doanh nghiệp Toàn diện",
        "department_code": None,
        "document_type": "MANUAL",
        "category": "Tri thức Chung",
        "security_level": "PUBLIC",
        "version": "1.0"
    }
]

print(f"\nBắt đầu nạp {len(documents_to_upload)} tài liệu tri thức vào hệ thống...")

for doc_info in documents_to_upload:
    file_path = os.path.join(DOCS_DIR, doc_info["file_name"])
    if not os.path.exists(file_path):
        print(f"[BỎ QUA] Không tìm thấy tệp: {file_path}")
        continue

    dept_id = depts.get(doc_info["department_code"]) if doc_info["department_code"] else None
    
    data = {
        "title": doc_info["title"],
        "document_type": doc_info["document_type"],
        "category": doc_info["category"],
        "security_level": doc_info["security_level"],
        "version": doc_info["version"],
    }
    if dept_id:
        data["department_id"] = str(dept_id)

    print(f"\n--> Đang nạp: '{doc_info['title']}' ({doc_info['file_name']})")
    print(f"    Phòng ban: {doc_info['department_code'] or 'Toàn doanh nghiệp'}, Bảo mật: {doc_info['security_level']}")

    with open(file_path, "rb") as f:
        files = {"file": (doc_info["file_name"], f)}
        upload_resp = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers,
            data=data,
            files=files
        )

    if upload_resp.status_code == 201:
        doc_res = upload_resp.json()
        print(f"    [THÀNH CÔNG] ID: {doc_res['id']} | Chunks: {doc_res.get('total_chunks')} | Status: {doc_res.get('rag_status')}")
    else:
        print(f"    [THẤT BẠI] Mã lỗi {upload_resp.status_code}: {upload_resp.text}")

print("\n--- HOÀN TẤT NẠP TÀI LIỆU ---")
