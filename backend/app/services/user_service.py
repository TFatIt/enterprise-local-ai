"""User, Department, and Enterprise Account Management business logic with strict RBAC & Department Isolation."""

import csv
import io
import secrets
import string
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.models.permission import Permission
from app.models.audit_log import AuditLog
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    UserProfileUpdateRequest,
    UserChangePasswordRequest,
    UserBulkActionRequest,
)
from app.core.security import get_password_hash, verify_password


class UserService:
    """Enterprise User Management Service."""

    # -------------------------------------------------------------
    # Helper: Department & Role Access Verification
    # -------------------------------------------------------------
    @staticmethod
    def _is_it_department(dept: Optional[Department]) -> bool:
        if not dept:
            return False
        code = dept.code.upper()
        return code == "IT" or code.startswith("IT_")

    @classmethod
    def apply_department_isolation(cls, query, actor: User, db: Session):
        """Filter user query based on actor's role and departmental boundary."""
        actor_role = actor.role.code if actor.role else "EMPLOYEE"

        if actor_role in ("SUPER_ADMIN", "ADMIN"):
            # Full visibility across enterprise
            return query

        if actor_role == "IT_ADMIN":
            # IT Admin sees all users except SUPER_ADMIN
            return query.join(User.role).filter(Role.code != "SUPER_ADMIN")

        if actor_role == "IT_MANAGER":
            # IT Manager sees users in IT and all IT sub-departments (IT_HELPDESK, IT_NETWORK, etc.)
            it_dept_ids = [
                d.id for d in db.query(Department).all()
                if cls._is_it_department(d)
            ]
            return query.filter(User.department_id.in_(it_dept_ids))

        if actor_role == "DEPARTMENT_MANAGER":
            # Department Manager ONLY sees users in their own department
            if not actor.department_id:
                return query.filter(False)
            return query.filter(User.department_id == actor.department_id)

        # Other roles cannot manage or view other users
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem hoặc quản lý người dùng."
        )

    @classmethod
    def verify_can_manage_target(cls, actor: User, target: User, db: Session, action_name: str = "quản lý"):
        """Enforce strict hierarchy rules so lower-privileged users cannot modify superiors."""
        actor_role = actor.role.code if actor.role else "EMPLOYEE"
        target_role = target.role.code if target.role else "EMPLOYEE"

        # 1. Self modification limits
        if actor.id == target.id and action_name in ("khóa", "vô hiệu hóa", "xóa", "hạ quyền"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể tự {action_name} tài khoản của chính mình."
            )

        # 2. Super Admin protection
        if target_role == "SUPER_ADMIN" and actor_role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Chỉ Super Admin mới có quyền {action_name} tài khoản Super Admin khác."
            )

        # 3. IT Admin limitations
        if actor_role == "IT_ADMIN":
            if target_role in ("SUPER_ADMIN", "ADMIN"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"IT Admin không thể {action_name} tài khoản Admin hoặc Super Admin."
                )

        # 4. IT Manager limitations
        if actor_role == "IT_MANAGER":
            if target_role in ("SUPER_ADMIN", "ADMIN", "IT_ADMIN", "IT_MANAGER") and actor.id != target.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"IT Manager không thể {action_name} tài khoản cấp quản trị."
                )
            if not cls._is_it_department(target.department):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IT Manager chỉ được quản lý nhân viên thuộc khối Công nghệ Thông tin."
                )

        # 5. Department Manager limitations
        if actor_role == "DEPARTMENT_MANAGER":
            if target_role in ("SUPER_ADMIN", "ADMIN", "IT_ADMIN", "IT_MANAGER", "DEPARTMENT_MANAGER") and actor.id != target.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Trưởng phòng không thể {action_name} tài khoản cấp quản lý khác."
                )
            if target.department_id != actor.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Trưởng phòng chỉ được quản lý nhân viên thuộc phòng ban mình phụ trách."
                )

    # -------------------------------------------------------------
    # Query & Retrieval
    # -------------------------------------------------------------
    @classmethod
    def get_users_paginated(
        cls,
        db: Session,
        actor: User,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        role_code: Optional[str] = None,
        user_status: Optional[str] = None,
        position: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[User], int]:
        """Fetch users with search, multi-field filters, department isolation, and total count."""
        query = db.query(User)

        # Department isolation
        query = cls.apply_department_isolation(query, actor, db)

        # Search term (username, full_name, email, employee_code, phone)
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(User.username).like(term),
                    func.lower(User.full_name).like(term),
                    func.lower(User.email).like(term),
                    func.lower(User.employee_code).like(term),
                    func.lower(User.phone).like(term),
                )
            )

        if department_id:
            query = query.filter(User.department_id == department_id)

        if role_code:
            query = query.join(User.role).filter(Role.code == role_code)

        if user_status:
            query = query.filter(User.status == user_status.upper())

        if position:
            query = query.filter(func.lower(User.position).like(f"%{position.strip().lower()}%"))

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        return users, total

    @classmethod
    def get_user_by_id(cls, db: Session, user_id: UUID, actor: Optional[User] = None) -> User:
        """Fetch user by primary key and verify boundary access."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng."
            )
        if actor:
            cls.verify_can_manage_target(actor, user, db, action_name="xem thông tin")
        return user

    @staticmethod
    def get_user_permissions(user: User) -> List[str]:
        """Resolve all permission codes granted to this user via their assigned role."""
        if not user.role or not user.role.permissions:
            return []
        return [p.code for p in user.role.permissions]

    # -------------------------------------------------------------
    # Create / Update / Delete
    # -------------------------------------------------------------
    @classmethod
    def create_user(cls, db: Session, actor: User, user_in: UserCreate, ip_address: Optional[str] = None) -> User:
        """Create new user with uniqueness validations, hierarchy enforcement, and audit trail."""
        actor_role = actor.role.code if actor.role else "EMPLOYEE"

        # Hierarchy check on assigning roles
        if user_in.role_code == "SUPER_ADMIN" and actor_role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Super Admin mới có quyền tạo thêm tài khoản Super Admin."
            )
        if user_in.role_code in ("ADMIN", "SUPER_ADMIN") and actor_role in ("IT_ADMIN", "IT_MANAGER", "DEPARTMENT_MANAGER"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền tạo tài khoản cấp Quản trị viên."
            )

        # Department boundary check
        if actor_role == "DEPARTMENT_MANAGER":
            if user_in.department_id != actor.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Trưởng phòng chỉ được tạo nhân viên trong phòng ban mình phụ trách."
                )
        if actor_role == "IT_MANAGER":
            target_dept = db.query(Department).filter(Department.id == user_in.department_id).first()
            if not cls._is_it_department(target_dept):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IT Manager chỉ được tạo nhân viên thuộc khối CNTT."
                )

        # Uniqueness checks
        norm_email = user_in.email.strip().lower()
        if db.query(User).filter(User.email == norm_email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email '{norm_email}' đã tồn tại.")

        norm_username = user_in.username.strip()
        if db.query(User).filter(User.username == norm_username).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tên đăng nhập '{norm_username}' đã được sử dụng.")

        if user_in.employee_code and user_in.employee_code.strip():
            emp_code = user_in.employee_code.strip()
            if db.query(User).filter(User.employee_code == emp_code).first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Mã nhân viên '{emp_code}' đã tồn tại.")
        else:
            emp_code = None

        role = db.query(Role).filter(Role.code == user_in.role_code).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vai trò '{user_in.role_code}' không hợp lệ.")

        if user_in.department_id:
            dept = db.query(Department).filter(Department.id == user_in.department_id).first()
            if not dept:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Phòng ban ID {user_in.department_id} không tồn tại.")

        # Hash password securely
        new_user = User(
            email=norm_email,
            username=norm_username,
            full_name=user_in.full_name.strip(),
            employee_code=emp_code,
            phone=user_in.phone.strip() if user_in.phone else None,
            position=user_in.position.strip() if user_in.position else None,
            hashed_password=get_password_hash(user_in.password),
            role_id=role.id,
            department_id=user_in.department_id,
            status=user_in.status.upper() if user_in.status else "ACTIVE",
            is_active=(user_in.status.upper() != "INACTIVE" and user_in.status.upper() != "LOCKED"),
            created_by=actor.id,
        )
        db.add(new_user)
        db.flush()

        # Audit Log
        audit = AuditLog(
            user_id=actor.id,
            target_user_id=new_user.id,
            action="USER_CREATE",
            resource="USERS",
            result="SUCCESS",
            details={
                "username": new_user.username,
                "email": new_user.email,
                "role": role.code,
                "department_id": new_user.department_id,
                "status": new_user.status,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        db.commit()
        db.refresh(new_user)
        return new_user

    @classmethod
    def update_user(cls, db: Session, actor: User, user_id: UUID, user_in: UserUpdate, ip_address: Optional[str] = None) -> User:
        """Update user profile, status, role, or department with guardrails."""
        user = cls.get_user_by_id(db, user_id)
        cls.verify_can_manage_target(actor, user, db, action_name="sửa")

        actor_role = actor.role.code if actor.role else "EMPLOYEE"

        # Unique email check
        if user_in.email and user_in.email.strip().lower() != user.email:
            norm_email = user_in.email.strip().lower()
            if db.query(User).filter(User.email == norm_email).first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã tồn tại.")
            user.email = norm_email

        # Unique username check
        if user_in.username and user_in.username.strip() != user.username:
            norm_username = user_in.username.strip()
            if db.query(User).filter(User.username == norm_username).first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên đăng nhập đã tồn tại.")
            user.username = norm_username

        # Unique employee code check
        if user_in.employee_code is not None and user_in.employee_code != user.employee_code:
            norm_code = user_in.employee_code.strip() if user_in.employee_code else None
            if norm_code:
                if db.query(User).filter(User.employee_code == norm_code).first():
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã nhân viên đã tồn tại.")
            user.employee_code = norm_code

        if user_in.full_name:
            user.full_name = user_in.full_name.strip()
        if user_in.phone is not None:
            user.phone = user_in.phone.strip() if user_in.phone else None
        if user_in.position is not None:
            user.position = user_in.position.strip() if user_in.position else None
        if user_in.avatar is not None:
            user.avatar = user_in.avatar

        # Role change
        if user_in.role_code and user.role and user_in.role_code != user.role.code:
            if user_in.role_code == "SUPER_ADMIN" and actor_role != "SUPER_ADMIN":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Super Admin mới có thể nâng quyền Super Admin.")
            new_role = db.query(Role).filter(Role.code == user_in.role_code).first()
            if not new_role:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vai trò không hợp lệ.")
            user.role_id = new_role.id

        # Department change
        if user_in.department_id is not None and user_in.department_id != user.department_id:
            dept = db.query(Department).filter(Department.id == user_in.department_id).first()
            if not dept:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phòng ban không tồn tại.")
            user.department_id = dept.id

        # Status change
        if user_in.status:
            user.status = user_in.status.upper()
            user.is_active = (user.status == "ACTIVE")

        if user_in.is_active is not None:
            user.is_active = user_in.is_active
            if not user.is_active and user.status == "ACTIVE":
                user.status = "INACTIVE"
            elif user.is_active and user.status != "ACTIVE":
                user.status = "ACTIVE"

        user.updated_at = datetime.now(timezone.utc)
        user.updated_by = actor.id

        # Audit Log
        audit = AuditLog(
            user_id=actor.id,
            target_user_id=user.id,
            action="USER_UPDATE",
            resource="USERS",
            result="SUCCESS",
            details={
                "username": user.username,
                "role": user.role.code if user.role else None,
                "department_id": user.department_id,
                "status": user.status,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def lock_user(cls, db: Session, actor: User, user_id: UUID, ip_address: Optional[str] = None) -> User:
        """Lock user account."""
        user = cls.get_user_by_id(db, user_id)
        cls.verify_can_manage_target(actor, user, db, action_name="khóa")

        user.status = "LOCKED"
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        user.updated_by = actor.id

        audit = AuditLog(
            user_id=actor.id,
            target_user_id=user.id,
            action="USER_LOCK",
            resource="USERS",
            result="SUCCESS",
            details={"username": user.username, "status": "LOCKED"},
            ip_address=ip_address,
        )
        db.add(audit)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def unlock_user(cls, db: Session, actor: User, user_id: UUID, ip_address: Optional[str] = None) -> User:
        """Unlock user account."""
        user = cls.get_user_by_id(db, user_id)
        cls.verify_can_manage_target(actor, user, db, action_name="mở khóa")

        user.status = "ACTIVE"
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        user.updated_by = actor.id

        audit = AuditLog(
            user_id=actor.id,
            target_user_id=user.id,
            action="USER_UNLOCK",
            resource="USERS",
            result="SUCCESS",
            details={"username": user.username, "status": "ACTIVE"},
            ip_address=ip_address,
        )
        db.add(audit)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def delete_user(cls, db: Session, actor: User, user_id: UUID, ip_address: Optional[str] = None) -> None:
        """Soft delete user account."""
        user = cls.get_user_by_id(db, user_id)
        cls.verify_can_manage_target(actor, user, db, action_name="xóa")

        user.status = "INACTIVE"
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)
        user.deleted_by = actor.id

        audit = AuditLog(
            user_id=actor.id,
            target_user_id=user.id,
            action="USER_DELETE",
            resource="USERS",
            result="SUCCESS",
            details={"username": user.username, "action": "SOFT_DELETE"},
            ip_address=ip_address,
        )
        db.add(audit)
        db.commit()

    @classmethod
    def reset_password(cls, db: Session, actor: User, user_id: UUID, ip_address: Optional[str] = None) -> str:
        """Generate secure temporary password, hash it, force change, and audit without logging password."""
        user = cls.get_user_by_id(db, user_id)
        cls.verify_can_manage_target(actor, user, db, action_name="đặt lại mật khẩu")

        # Generate readable secure temporary password e.g. "Pass@8xK9mQ"
        alphabet = string.ascii_letters + string.digits
        random_str = "".join(secrets.choice(alphabet) for _ in range(8))
        temp_password = f"Reset@{random_str}"

        user.hashed_password = get_password_hash(temp_password)
        user.force_password_change = True
        user.password_changed_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        user.updated_by = actor.id

        audit = AuditLog(
            user_id=actor.id,
            target_user_id=user.id,
            action="USER_RESET_PASSWORD",
            resource="USERS",
            result="SUCCESS",
            details={"username": user.username, "note": "Temporary password issued, forced change required"},
            ip_address=ip_address,
        )
        db.add(audit)
        db.commit()
        return temp_password

    # -------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------
    @classmethod
    def bulk_action(cls, db: Session, actor: User, bulk_in: UserBulkActionRequest, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Execute bulk actions safely excluding SUPER_ADMIN and self."""
        affected = 0
        skipped = 0

        for uid in bulk_in.user_ids:
            user = db.query(User).filter(User.id == uid).first()
            if not user:
                skipped += 1
                continue

            # Protect Super Admin and self from destructive actions
            if (user.role and user.role.code == "SUPER_ADMIN") or user.id == actor.id:
                skipped += 1
                continue

            try:
                cls.verify_can_manage_target(actor, user, db, action_name="thao tác hàng loạt")
            except HTTPException:
                skipped += 1
                continue

            if bulk_in.action == "ACTIVATE":
                user.status = "ACTIVE"
                user.is_active = True
            elif bulk_in.action == "DEACTIVATE":
                user.status = "INACTIVE"
                user.is_active = False
            elif bulk_in.action == "LOCK":
                user.status = "LOCKED"
                user.is_active = False
            elif bulk_in.action == "UNLOCK":
                user.status = "ACTIVE"
                user.is_active = True
            elif bulk_in.action == "ASSIGN_DEPARTMENT":
                if bulk_in.target_department_id:
                    user.department_id = bulk_in.target_department_id

            user.updated_at = datetime.now(timezone.utc)
            user.updated_by = actor.id
            affected += 1

        audit = AuditLog(
            user_id=actor.id,
            action=f"USER_BULK_{bulk_in.action}",
            resource="USERS",
            result="SUCCESS",
            details={"action": bulk_in.action, "affected_count": affected, "skipped_count": skipped},
            ip_address=ip_address,
        )
        db.add(audit)
        db.commit()
        return {"success": True, "affected": affected, "skipped": skipped}

    # -------------------------------------------------------------
    # Stats & Metrics
    # -------------------------------------------------------------
    @classmethod
    def get_user_stats(cls, db: Session, actor: User) -> Dict[str, int]:
        """Calculate system user statistics adhering to department isolation."""
        query = db.query(User)
        query = cls.apply_department_isolation(query, actor, db)

        all_users = query.all()
        total_users = len(all_users)
        active_users = sum(1 for u in all_users if u.status == "ACTIVE")
        inactive_users = sum(1 for u in all_users if u.status == "INACTIVE")
        locked_users = sum(1 for u in all_users if u.status == "LOCKED")
        pending_users = sum(1 for u in all_users if u.status == "PENDING")

        it_users = sum(1 for u in all_users if cls._is_it_department(u.department))
        admin_users = sum(1 for u in all_users if u.role and u.role.code in ("SUPER_ADMIN", "ADMIN", "IT_ADMIN"))
        total_departments = db.query(Department).count()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "locked_users": locked_users,
            "pending_users": pending_users,
            "total_departments": total_departments,
            "it_users": it_users,
            "admin_users": admin_users,
        }

    # -------------------------------------------------------------
    # CSV Export & Import
    # -------------------------------------------------------------
    @classmethod
    def export_users_csv(cls, db: Session, actor: User) -> str:
        """Export users list to CSV format omitting any passwords or security secrets."""
        users, _ = cls.get_users_paginated(db, actor, limit=10000)

        output = io.StringIO()
        # UTF-8 BOM for Microsoft Excel compatibility
        output.write("\ufeff")
        writer = csv.writer(output)

        writer.writerow([
            "Mã nhân viên",
            "Tên đăng nhập",
            "Họ và tên",
            "Email",
            "Số điện thoại",
            "Chức danh",
            "Phòng ban",
            "Vai trò",
            "Trạng thái",
            "Đăng nhập cuối",
            "Ngày tạo",
        ])

        for u in users:
            writer.writerow([
                u.employee_code or "",
                u.username,
                u.full_name,
                u.email,
                u.phone or "",
                u.position or "",
                u.department.name if u.department else "",
                u.role.name if u.role else "Nhân viên",
                u.status,
                u.last_login_at.strftime("%Y-%m-%d %H:%M") if u.last_login_at else "",
                u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "",
            ])

        return output.getvalue()

    @classmethod
    def import_users_csv(cls, db: Session, actor: User, csv_content: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Validate and bulk import users from CSV."""
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        imported = 0
        errors = []

        # Cache roles and depts
        roles = {r.code: r for r in db.query(Role).all()}
        depts_by_name = {d.name.lower(): d for d in db.query(Department).all()}
        depts_by_code = {d.code.lower(): d for d in db.query(Department).all()}

        default_role = roles.get("EMPLOYEE")
        default_dept = depts_by_code.get("it")

        for idx, row in enumerate(reader, start=2):
            username = (row.get("username") or row.get("Tên đăng nhập") or "").strip()
            email = (row.get("email") or row.get("Email") or "").strip().lower()
            full_name = (row.get("full_name") or row.get("Họ và tên") or "").strip()
            employee_code = (row.get("employee_code") or row.get("Mã nhân viên") or "").strip() or None
            phone = (row.get("phone") or row.get("Số điện thoại") or "").strip() or None
            position = (row.get("position") or row.get("Chức danh") or "").strip() or None
            dept_raw = (row.get("department") or row.get("Phòng ban") or "").strip().lower()
            role_raw = (row.get("role") or row.get("Vai trò") or "EMPLOYEE").strip().upper()

            if not username or not email or not full_name:
                errors.append(f"Dòng {idx}: Thiếu tên đăng nhập, email hoặc họ tên.")
                continue

            if db.query(User).filter(User.username == username).first():
                errors.append(f"Dòng {idx}: Tên đăng nhập '{username}' đã tồn tại.")
                continue

            if db.query(User).filter(User.email == email).first():
                errors.append(f"Dòng {idx}: Email '{email}' đã tồn tại.")
                continue

            target_dept = depts_by_code.get(dept_raw) or depts_by_name.get(dept_raw) or default_dept
            target_role = roles.get(role_raw, default_role)

            new_u = User(
                username=username,
                email=email,
                full_name=full_name,
                employee_code=employee_code,
                phone=phone,
                position=position,
                hashed_password=get_password_hash("Employee@123456"),
                role_id=target_role.id,
                department_id=target_dept.id if target_dept else None,
                status="ACTIVE",
                force_password_change=True,
                created_by=actor.id,
            )
            db.add(new_u)
            imported += 1

        db.commit()
        return {"imported": imported, "errors": errors}

    # -------------------------------------------------------------
    # Self-Service Profile
    # -------------------------------------------------------------
    @classmethod
    def update_profile(cls, db: Session, user: User, profile_in: UserProfileUpdateRequest) -> User:
        """Allow user to edit their own profile (name, phone, avatar)."""
        if profile_in.full_name:
            user.full_name = profile_in.full_name.strip()
        if profile_in.phone is not None:
            user.phone = profile_in.phone.strip() if profile_in.phone else None
        if profile_in.avatar is not None:
            user.avatar = profile_in.avatar

        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def change_password(cls, db: Session, user: User, pw_in: UserChangePasswordRequest) -> None:
        """Allow user to change their own password."""
        if not verify_password(pw_in.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không chính xác."
            )
        user.hashed_password = get_password_hash(pw_in.new_password)
        user.force_password_change = False
        user.password_changed_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

    # -------------------------------------------------------------
    # Departments & Roles
    # -------------------------------------------------------------
    @staticmethod
    def get_departments(db: Session) -> List[Department]:
        """Fetch all departments with user counts."""
        return db.query(Department).order_by(Department.name.asc()).all()

    @staticmethod
    def create_department(db: Session, dept_in: DepartmentCreate) -> Department:
        """Create new department."""
        code = dept_in.code.strip().upper()
        if db.query(Department).filter(Department.code == code).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Mã phòng ban '{code}' đã tồn tại.")
        new_dept = Department(code=code, name=dept_in.name.strip(), description=dept_in.description)
        db.add(new_dept)
        db.commit()
        db.refresh(new_dept)
        return new_dept

    @staticmethod
    def update_department(db: Session, dept_id: int, dept_in: DepartmentUpdate) -> Department:
        """Update department information."""
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phòng ban không tồn tại.")
        if dept_in.name is not None and dept_in.name.strip():
            dept.name = dept_in.name.strip()
        if dept_in.description is not None:
            dept.description = dept_in.description
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def delete_department(db: Session, dept_id: int) -> None:
        """Delete a department if it contains no users."""
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phòng ban không tồn tại.")
        user_count = db.query(User).filter(User.department_id == dept_id, User.status != "INACTIVE").count()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể xóa phòng ban '{dept.name}' vì đang có {user_count} nhân viên trực thuộc. Vui lòng điều chuyển nhân sự trước."
            )
        db.delete(dept)
        db.commit()

    @staticmethod
    def get_roles(db: Session) -> List[Role]:
        """Fetch all roles."""
        return db.query(Role).all()

    @staticmethod
    def get_permissions(db: Session) -> List[Permission]:
        """Fetch all permissions."""
        return db.query(Permission).order_by(Permission.category.asc(), Permission.code.asc()).all()


user_service = UserService()
