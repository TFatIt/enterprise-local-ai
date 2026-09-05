"""Database Migration & Seeding for Enterprise Document Access Control (EDAC)."""

import os
import sys
import sqlite3
import logging

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.base import Base
from app.db.session import engine, SessionLocal
import app.models  # Registers all models with Base.metadata
from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.document import Document
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def migrate_sqlite_schema():
    """Safely apply column additions to existing SQLite database."""
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "enterprise_local_dev.db"))
    if not os.path.exists(db_path):
        logger.info(f"Database not found at {db_path}, creating via SQLAlchemy Base.")
        Base.metadata.create_all(bind=engine)
        return

    logger.info(f"Applying SQLite migrations on {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing columns in documents
    cursor.execute("PRAGMA table_info(documents);")
    existing_cols = {row[1] for row in cursor.fetchall()}

    columns_to_add = [
        ("document_type", "VARCHAR(50) DEFAULT 'POLICY' NOT NULL"),
        ("category", "VARCHAR(100) DEFAULT 'Chung' NOT NULL"),
        ("owner_id", "CHAR(36)"),
        ("security_level", "VARCHAR(50) DEFAULT 'DEPARTMENT' NOT NULL"),
        ("visibility", "BOOLEAN DEFAULT 1 NOT NULL"),
        ("version", "VARCHAR(20) DEFAULT '1.0' NOT NULL"),
        ("rag_status", "VARCHAR(30) DEFAULT 'READY' NOT NULL"),
        ("approved_at", "DATETIME"),
        ("approved_by", "CHAR(36)"),
    ]

    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            alter_query = f"ALTER TABLE documents ADD COLUMN {col_name} {col_def};"
            logger.info(f"Adding column: {col_name}")
            cursor.execute(alter_query)

    conn.commit()
    conn.close()

    # Create any missing new tables (document_permissions, department_permissions, document_versions)
    Base.metadata.create_all(bind=engine)
    logger.info("Schema migrations applied successfully.")


def seed_enterprise_entities():
    """Seed 20 departments, 6 roles, and standard test accounts."""
    db = SessionLocal()
    try:
        # 1. Seed Roles
        roles_data = [
            {"code": "SUPER_ADMIN", "name": "Quản trị viên Hệ thống (Super Admin)", "description": "Toàn quyền quản trị hệ thống, người dùng, tài liệu và audit logs."},
            {"code": "ADMIN", "name": "Quản trị viên Doanh nghiệp (Admin)", "description": "Toàn quyền quản lý tài liệu, phê duyệt và quản lý phân quyền."},
            {"code": "MANAGER", "name": "Cấp Quản lý (Manager)", "description": "Xem và tìm kiếm toàn bộ tài liệu của tất cả phòng ban trong công ty."},
            {"code": "DEPARTMENT_MANAGER", "name": "Trưởng phòng ban (Dept Manager)", "description": "Quản lý và phân quyền tài liệu trong phạm vi phòng ban phụ trách."},
            {"code": "EMPLOYEE", "name": "Nhân viên (Employee)", "description": "Xem và tìm kiếm tài liệu thuộc phòng ban mình và tài liệu nội bộ chung."},
            {"code": "VIEWER", "name": "Người xem hạn chế (Viewer)", "description": "Chỉ xem các tài liệu công khai hoặc được chỉ định riêng biệt."},
            {"code": "IT_ADMIN", "name": "Quản trị viên IT (IT Admin)", "description": "Quản trị kỹ thuật, hỗ trợ hạ tầng và vận hành RAG."},
        ]

        roles_map = {}
        for r in roles_data:
            role_obj = db.query(Role).filter(Role.code == r["code"]).first()
            if not role_obj:
                role_obj = Role(**r)
                db.add(role_obj)
                db.flush()
                logger.info(f"Created role: {role_obj.code}")
            roles_map[role_obj.code] = role_obj

        # 2. Seed 20 Departments
        departments_data = [
            {"code": "IT", "name": "Phòng Công nghệ Thông tin", "description": "Hạ tầng mạng, phần mềm và kỹ thuật CNTT"},
            {"code": "ACCOUNTING", "name": "Phòng Kế toán", "description": "Hạch toán, sổ sách kế toán, hóa đơn và thuế"},
            {"code": "FINANCE", "name": "Phòng Tài chính", "description": "Quản lý dòng tiền, ngân sách và đầu tư"},
            {"code": "HR", "name": "Phòng Nhân sự", "description": "Tuyển dụng, đào tạo, chế độ phúc lợi và nhân lực"},
            {"code": "SALES", "name": "Phòng Kinh doanh & Bán hàng", "description": "Thương mại, hợp đồng bán hàng và chính sách giá"},
            {"code": "MARKETING", "name": "Phòng Tiếp thị & Truyền thông", "description": "Chiến lược tiếp thị, quảng bá thương hiệu"},
            {"code": "CUSTOMER_SERVICE", "name": "Phòng Chăm sóc Khách hàng", "description": "Hỗ trợ khách hàng, giải quyết khiếu nại"},
            {"code": "PLANNING", "name": "Phòng Kế hoạch & Quản trị Dự án", "description": "Quy hoạch chiến lược và quản trị dự án"},
            {"code": "PROCUREMENT", "name": "Phòng Thu mua & Chuỗi Cung ứng", "description": "Mua sắm hàng hóa, đánh giá nhà cung cấp"},
            {"code": "LEGAL", "name": "Phòng Pháp chế & Tuân thủ", "description": "Tư vấn pháp lý, rà soát hợp đồng và tuân thủ"},
            {"code": "QA", "name": "Phòng Đảm bảo Chất lượng (QA)", "description": "Quy trình chất lượng và tiêu chuẩn ISO"},
            {"code": "QC", "name": "Phòng Kiểm soát Chất lượng (QC)", "description": "Kiểm tra chất lượng sản phẩm và vật tư"},
            {"code": "PRODUCTION", "name": "Phòng Quản lý Sản xuất", "description": "Vận hành dây chuyền và lịch trình sản xuất"},
            {"code": "WAREHOUSE", "name": "Phòng Quản lý Kho vận", "description": "Lưu kho, xuất nhập tồn và kiểm kê hàng hóa"},
            {"code": "LOGISTICS", "name": "Phòng Hậu cần & Vận tải", "description": "Điều phối phương tiện và giao nhận hàng hóa"},
            {"code": "MAINTENANCE", "name": "Phòng Bảo trì Thiết bị", "description": "Bảo dưỡng máy móc và sửa chữa kỹ thuật cơ điện"},
            {"code": "ENGINEERING", "name": "Phòng Kỹ thuật Công nghệ", "description": "Nghiên cứu công nghệ, cải tiến kỹ thuật"},
            {"code": "INFRASTRUCTURE", "name": "Phòng Quản trị Hạ tầng", "description": "Cơ sở vật chất, tòa nhà và hệ thống điện nước"},
            {"code": "SECURITY", "name": "Phòng An ninh Doanh nghiệp", "description": "Bảo vệ an ninh trật tự và phòng cháy chữa cháy"},
            {"code": "MANAGEMENT", "name": "Ban Lãnh đạo & Điều hành", "description": "Ban Giám đốc và quản lý cấp cao doanh nghiệp"},
        ]

        depts_map = {}
        for d in departments_data:
            dept_obj = db.query(Department).filter(Department.code == d["code"]).first()
            if not dept_obj:
                dept_obj = Department(**d)
                db.add(dept_obj)
                db.flush()
                logger.info(f"Created department: {dept_obj.code}")
            depts_map[dept_obj.code] = dept_obj

        # 3. Seed Standard Test Accounts
        test_users = [
            {
                "username": "superadmin",
                "email": "admin@enterprise.local",
                "full_name": "System Administrator",
                "password": "Admin@123456",
                "role_code": "SUPER_ADMIN",
                "dept_code": "IT",
            },
            {
                "username": "itadmin",
                "email": "it.admin@enterprise.local",
                "full_name": "IT Helpdesk Specialist",
                "password": "Admin@123456",
                "role_code": "IT_ADMIN",
                "dept_code": "IT",
            },
            {
                "username": "admin_corp",
                "email": "admin.corp@enterprise.local",
                "full_name": "Corporate Administrator",
                "password": "Admin@123456",
                "role_code": "ADMIN",
                "dept_code": "MANAGEMENT",
            },
            {
                "username": "manager_corp",
                "email": "manager@enterprise.local",
                "full_name": "General Manager",
                "password": "Admin@123456",
                "role_code": "MANAGER",
                "dept_code": "MANAGEMENT",
            },
            {
                "username": "it_manager",
                "email": "it.manager@enterprise.local",
                "full_name": "IT Department Manager",
                "password": "Admin@123456",
                "role_code": "DEPARTMENT_MANAGER",
                "dept_code": "IT",
            },
            {
                "username": "it_employee",
                "email": "it.employee@enterprise.local",
                "full_name": "IT Support Engineer",
                "password": "Employee@123456",
                "role_code": "EMPLOYEE",
                "dept_code": "IT",
            },
            {
                "username": "acc_employee",
                "email": "acc.employee@enterprise.local",
                "full_name": "Accounting Specialist",
                "password": "Employee@123456",
                "role_code": "EMPLOYEE",
                "dept_code": "ACCOUNTING",
            },
            {
                "username": "hr_employee",
                "email": "hr.employee@enterprise.local",
                "full_name": "HR Generalist",
                "password": "Employee@123456",
                "role_code": "EMPLOYEE",
                "dept_code": "HR",
            },
            {
                "username": "viewer",
                "email": "viewer@enterprise.local",
                "full_name": "Guest Document Viewer",
                "password": "Employee@123456",
                "role_code": "VIEWER",
                "dept_code": "IT",
            },
        ]

        users_map = {}
        for u in test_users:
            user_obj = db.query(User).filter(User.username == u["username"]).first()
            if not user_obj:
                role = roles_map.get(u["role_code"])
                dept = depts_map.get(u["dept_code"])
                user_obj = User(
                    username=u["username"],
                    email=u["email"],
                    full_name=u["full_name"],
                    hashed_password=get_password_hash(u["password"]),
                    role_id=role.id,
                    department_id=dept.id if dept else None,
                    is_active=True,
                )
                db.add(user_obj)
                db.flush()
                logger.info(f"Created user: {user_obj.username}")
            users_map[u["username"]] = user_obj

        # 4. Backfill and map existing documents
        super_admin_user = users_map.get("superadmin")
        docs = db.query(Document).all()
        for doc in docs:
            if not doc.owner_id:
                doc.owner_id = doc.uploaded_by or (super_admin_user.id if super_admin_user else None)
            if not doc.security_level:
                doc.security_level = "DEPARTMENT"
            if not doc.version:
                doc.version = "1.0"
            if not doc.rag_status:
                doc.rag_status = "READY" if doc.total_chunks > 0 else "NOT_INDEXED"

            # Assign appropriate department and category based on filename
            fn = doc.file_name.lower()
            if "finance" in fn or "accounting" in fn or "thanh toán" in doc.title.lower():
                doc.department_id = depts_map["ACCOUNTING"].id
                doc.document_type = "POLICY"
                doc.category = "Kế toán & Tài chính"
                doc.security_level = "DEPARTMENT"
            elif "procurement" in fn or "mua sắm" in doc.title.lower():
                doc.department_id = depts_map["PROCUREMENT"].id
                doc.document_type = "POLICY"
                doc.category = "Mua sắm & Chuỗi cung ứng"
                doc.security_level = "DEPARTMENT"
            elif "sales" in fn or "bán hàng" in doc.title.lower():
                doc.department_id = depts_map["SALES"].id
                doc.document_type = "POLICY"
                doc.category = "Kinh doanh & Thương mại"
                doc.security_level = "DEPARTMENT"
            elif "hr" in fn or "lao động" in doc.title.lower():
                doc.department_id = depts_map["HR"].id
                doc.document_type = "POLICY"
                doc.category = "Nhân sự & Tiền lương"
                doc.security_level = "DEPARTMENT"
            elif "bhyt" in fn:
                doc.department_id = depts_map["HR"].id
                doc.document_type = "GUIDE"
                doc.category = "Bảo hiểm & Phúc lợi"
                doc.security_level = "INTERNAL"
            elif "kham pha" in fn or "quy hoạch" in doc.title.lower():
                doc.department_id = depts_map["PLANNING"].id
                doc.document_type = "REPORT"
                doc.category = "Quy hoạch Trí thức"
                doc.security_level = "INTERNAL"
            elif "troubleshooting" in fn or "sự cố" in doc.title.lower():
                doc.department_id = depts_map["IT"].id
                doc.document_type = "SOP"
                doc.category = "Hỗ trợ Kỹ thuật HelpDesk"
                doc.security_level = "DEPARTMENT"
            elif "security" in fn or "bảo mật" in doc.title.lower() or "vpn" in fn:
                doc.department_id = depts_map["IT"].id
                doc.document_type = "POLICY"
                doc.category = "An ninh Mạng & CNTT"
                doc.security_level = "DEPARTMENT"

        db.commit()
        logger.info(f"Successfully migrated and seeded {len(departments_data)} departments, {len(roles_data)} roles, and {len(docs)} documents.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    migrate_sqlite_schema()
    seed_enterprise_entities()
