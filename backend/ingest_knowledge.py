"""Ingestion script to populate Enterprise Knowledge Base across all departments."""

import os
import sys
import io
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_knowledge")

from app.db.session import SessionLocal
from app.models.department import Department
from app.models.user import User
from app.models.document import Document
from app.services.document_service import document_service
from fastapi import UploadFile


def main():
    db = SessionLocal()
    try:
        # 1. Department definitions
        dept_defs = [
            {"code": "IT", "name": "Phòng Công nghệ Thông tin", "desc": "Quản trị hạ tầng mạng, máy chủ và an toàn thông tin."},
            {"code": "HR", "name": "Phòng Nhân sự", "desc": "Chính sách nhân sự, nội quy lao động, tuyển dụng và đào tạo."},
            {"code": "FINANCE", "name": "Phòng Kế toán - Tài chính", "desc": "Quản lý kế toán, duyệt chi, hóa đơn và công nợ."},
            {"code": "PROCUREMENT", "name": "Phòng Thu mua & Chuỗi Cung ứng", "desc": "Mua sắm thiết bị, tài sản và quản trị nhà cung cấp."},
            {"code": "LEGAL", "name": "Phòng Pháp chế & Tuân thủ", "desc": "Rà soát hợp đồng kinh tế, sở hữu trí tuệ và tuân thủ PDPD."},
            {"code": "QA", "name": "Phòng Quản lý Chất lượng", "desc": "Hệ thống quản lý chất lượng ISO, kiểm thử và quy trình CAPA."},
            {"code": "SALES", "name": "Phòng Kinh doanh & Phát triển Thị trường", "desc": "Bán hàng B2B, quản trị quan hệ khách hàng và báo giá."},
            {"code": "PLANNING", "name": "Phòng Kế hoạch & Quản trị Dự án", "desc": "Lập kế hoạch tổng thể, điều phối dự án và nguồn lực."},
        ]

        dept_map = {}
        for d in dept_defs:
            dept = db.query(Department).filter(Department.code == d["code"]).first()
            if not dept:
                dept = Department(code=d["code"], name=d["name"], description=d["desc"])
                db.add(dept)
                db.flush()
                logger.info(f"Created Department: {dept.code} (ID={dept.id})")
            dept_map[d["code"]] = dept
        db.commit()

        # 2. Get superadmin user
        admin_user = db.query(User).filter(User.username == "superadmin").first()
        if not admin_user:
            admin_user = db.query(User).first()
        logger.info(f"Uploader user: {admin_user.username} (ID={admin_user.id})")

        # 3. Document catalog to ingest
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documents"))
        docs_to_ingest = [
            {
                "file_name": "sample_it_policy.txt",
                "title": "Chính sách An toàn Mật khẩu, Gia nhập Miền AD & Cấu hình VPN",
                "dept_code": "IT",
            },
            {
                "file_name": "sample_troubleshooting_handbook.txt",
                "title": "Sổ tay Xử lý Sự cố Kỹ thuật IT HelpDesk, Mạng LAN & Outlook",
                "dept_code": "IT",
            },
            {
                "file_name": "sample_cyber_security_pdpd.txt",
                "title": "Chính sách An toàn Thông tin & Tuân thủ Bảo vệ Dữ liệu Cá nhân (Nghị định 13)",
                "dept_code": "IT",
            },
            {
                "file_name": "sample_hr_policy.txt",
                "title": "Nội quy Lao động, Chế độ Nghỉ phép & Phúc lợi Nhân sự",
                "dept_code": "HR",
            },
            {
                "file_name": "sample_finance_accounting_policy.txt",
                "title": "Quy định Thanh toán, Hoàn ứng, Duyệt chi & Hóa đơn Điện tử",
                "dept_code": "FINANCE",
            },
            {
                "file_name": "sample_procurement_sourcing_policy.txt",
                "title": "Quy trình Mua sắm Hàng hóa & Đánh giá Nhà Cung cấp (Procure-to-Pay)",
                "dept_code": "PROCUREMENT",
            },
            {
                "file_name": "sample_b2b_sales_commercial_policy.txt",
                "title": "Quy trình Bán hàng B2B 7 Bước & Khung Chính sách Giá Chiết khấu",
                "dept_code": "SALES",
            },
            {
                "file_name": "Ban_Do_Tai_Lieu_Tri_Thuc_Doanh_Nghiep.docx",
                "title": "Bản đồ Khám phá & Quy hoạch Tri thức Toàn Doanh nghiệp",
                "dept_code": "PLANNING",
            },
        ]

        logger.info("=== BẮT ĐẦU NẠP TÀI LIỆU VÀO KHO TRI THỨC DOANH NGHIỆP ===")
        ingested_count = 0
        for item in docs_to_ingest:
            file_path = os.path.join(base_dir, item["file_name"])
            if not os.path.exists(file_path):
                logger.warning(f"Không tìm thấy file: {file_path}")
                continue

            # Check if document with same filename already in DB
            existing_doc = db.query(Document).filter(Document.file_name == item["file_name"]).first()
            if existing_doc and existing_doc.status == "INDEXED" and existing_doc.total_chunks > 0:
                logger.info(f"Tài liệu đã tồn tại: '{existing_doc.title}' (ID={existing_doc.id}, Chunks={existing_doc.total_chunks})")
                continue

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            dept = dept_map.get(item["dept_code"])
            upload_file = UploadFile(filename=item["file_name"], file=io.BytesIO(file_bytes))

            created_doc = document_service.upload_document(
                db=db,
                file=upload_file,
                title=item["title"],
                department_id=dept.id if dept else None,
                current_user=admin_user,
            )
            ingested_count += 1
            logger.info(f" ĐÃ NẠP THÀNH CÔNG: '{created_doc.title}' | Phòng ban: {dept.name if dept else 'Chung'} | Status: {created_doc.status} | Chunks: {created_doc.total_chunks}")

        logger.info(f"=== HOÀN TẤT: Đã nạp thành công {ingested_count} tài liệu mới vào hệ thống! ===")

        # Summary check
        total_docs = db.query(Document).count()
        logger.info(f"Tổng số tài liệu hiện hữu trong Database: {total_docs}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
