# -*- coding: utf-8 -*-
"""Direct SQLite script with timeout to fix Vietnamese encoding in departments and documents."""

import os
import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

db_path = os.path.abspath("enterprise_local_dev.db")
print(f"Connecting to {db_path}...")

conn = sqlite3.connect(db_path, timeout=60.0)
cursor = conn.cursor()

# 1. Fix department names
dept_fixes = [
    ("Phòng Công nghệ Thông tin", "IT"),
    ("Phòng Nhân sự", "HR"),
    ("Phòng Kế toán - Tài chính", "FINANCE"),
    ("Phòng Thu mua & Chuỗi Cung ứng", "PROCUREMENT"),
    ("Phòng Pháp chế & Tuân thủ", "LEGAL"),
    ("Phòng Quản lý Chất lượng", "QA"),
    ("Phòng Kinh doanh & Phát triển Thị trường", "SALES"),
    ("Phòng Kế hoạch & Quản trị Dự án", "PLANNING"),
]

print("=== UPDATING DEPARTMENTS ===")
for name, code in dept_fixes:
    cursor.execute("UPDATE departments SET name = ? WHERE code = ?", (name, code))
    print(f"Updated department {code} -> {name}")
conn.commit()

# 2. Delete corrupt/broken duplicate document
cursor.execute("DELETE FROM documents WHERE title LIKE '%B?n ??%'")
print(f"Deleted corrupted duplicate docs: {cursor.rowcount}")
conn.commit()

# 3. Fix document titles
title_fixes = [
    ("Chính sách An toàn Mật khẩu, Gia nhập Miền AD & Cấu hình VPN", "sample_it_policy.txt"),
    ("Sổ tay Xử lý Sự cố Kỹ thuật IT HelpDesk, Mạng LAN & Outlook", "sample_troubleshooting_handbook.txt"),
    ("Chính sách An toàn Thông tin & Tuân thủ Bảo vệ Dữ liệu Cá nhân (Nghị định 13)", "sample_cyber_security_pdpd.txt"),
    ("Nội quy Lao động, Chế độ Nghỉ phép & Phúc lợi Nhân sự", "sample_hr_policy.txt"),
    ("Quy định Thanh toán, Hoàn ứng, Duyệt chi & Hóa đơn Điện tử", "sample_finance_accounting_policy.txt"),
    ("Quy trình Mua sắm Hàng hóa & Đánh giá Nhà Cung cấp (Procure-to-Pay)", "sample_procurement_sourcing_policy.txt"),
    ("Quy trình Bán hàng B2B 7 Bước & Khung Chính sách Giá Chiết khấu", "sample_b2b_sales_commercial_policy.txt"),
    ("Bản đồ Khám phá & Quy hoạch Tri thức Toàn Doanh nghiệp", "Ban_Do_Tai_Lieu_Tri_Thuc_Doanh_Nghiep.docx"),
]

print("=== UPDATING DOCUMENT TITLES ===")
for title, filename in title_fixes:
    cursor.execute("UPDATE documents SET title = ? WHERE file_name = ?", (title, filename))
    print(f"Updated doc {filename} -> {title}")
conn.commit()

# 4. Print current state
print("=== VERIFYING DATABASE RECORDS ===")
cursor.execute("SELECT d.id, d.title, d.file_name, dept.name, d.file_size, d.total_chunks FROM documents d LEFT JOIN departments dept ON d.department_id = dept.id")
rows = cursor.fetchall()
for r in rows:
    print(f"- Title: {r[1]} | File: {r[2]} | Dept: {r[3]} | Size: {r[4]} bytes | Chunks: {r[5]}")

conn.close()
print("=== SUCCESS: All records updated cleanly with full Vietnamese UTF-8! ===")
