"""Database Seeder script to initialize default roles, departments, and seed accounts."""

import logging
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


def seed_database(db: Session) -> None:
    """Populate database with default roles, departments, and administrative accounts."""
    logger.info("Checking and seeding default database entities...")

    # 1. Seed Roles
    roles_data = [
        {
            "code": "SUPER_ADMIN",
            "name": "Quản trị viên Hệ thống (Super Admin)",
            "description": "Toàn quyền quản trị hệ thống, người dùng, tài liệu và audit logs."
        },
        {
            "code": "IT_ADMIN",
            "name": "Quản trị viên IT (IT Admin)",
            "description": "Quản lý hỗ trợ kỹ thuật, xử lý ticket và nạp tài liệu IT knowledge base."
        },
        {
            "code": "EMPLOYEE",
            "name": "Nhân viên (Employee)",
            "description": "Hỏi đáp trợ lý AI, tra cứu tri thức nội bộ và tạo ticket yêu cầu hỗ trợ."
        },
    ]

    roles_map = {}
    for r_data in roles_data:
        role = db.query(Role).filter(Role.code == r_data["code"]).first()
        if not role:
            role = Role(**r_data)
            db.add(role)
            db.flush()
            logger.info(f"Created role: {role.code}")
        roles_map[role.code] = role

    # 2. Seed Departments
    dept_data = [
        {
            "code": "IT",
            "name": "Phòng Công nghệ Thông tin",
            "description": "Quản trị hạ tầng mạng, máy chủ, bảo mật và hỗ trợ kỹ thuật."
        },
        {
            "code": "HR",
            "name": "Phòng Nhân sự",
            "description": "Quản trị nhân lực, tuyển dụng, đào tạo và chính sách lao động."
        },
        {
            "code": "FINANCE",
            "name": "Phòng Kế toán - Tài chính",
            "description": "Quản lý kế toán, ngân sách, quyết toán và thủ tục tài chính."
        },
    ]

    dept_map = {}
    for d_data in dept_data:
        dept = db.query(Department).filter(Department.code == d_data["code"]).first()
        if not dept:
            dept = Department(**d_data)
            db.add(dept)
            db.flush()
            logger.info(f"Created department: {dept.code}")
        dept_map[dept.code] = dept

    # 3. Seed Default Accounts
    users_data = [
        {
            "email": "admin@enterprise.local",
            "username": "superadmin",
            "full_name": "System Administrator",
            "password": "Admin@123456",
            "role_code": "SUPER_ADMIN",
            "dept_code": "IT",
        },
        {
            "email": "it.admin@enterprise.local",
            "username": "itadmin",
            "full_name": "IT Helpdesk Specialist",
            "password": "Admin@123456",
            "role_code": "IT_ADMIN",
            "dept_code": "IT",
        },
        {
            "email": "employee@enterprise.local",
            "username": "employee",
            "full_name": "Standard Employee",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "HR",
        },
    ]

    for u_data in users_data:
        user = db.query(User).filter(User.email == u_data["email"]).first()
        if not user:
            user = User(
                email=u_data["email"],
                username=u_data["username"],
                full_name=u_data["full_name"],
                hashed_password=get_password_hash(u_data["password"]),
                role_id=roles_map[u_data["role_code"]].id,
                department_id=dept_map[u_data["dept_code"]].id,
                is_active=True,
            )
            db.add(user)
            logger.info(f"Created user: {user.username} ({user.email})")

    db.commit()
    logger.info("Database seeding completed successfully.")
