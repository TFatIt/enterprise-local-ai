"""User and organization management business logic."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.schemas.user import UserCreate, UserUpdate, DepartmentCreate
from app.core.security import get_password_hash


class UserService:
    """Service handling user accounts, roles, and departments."""

    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        department_id: Optional[int] = None,
        role_code: Optional[str] = None
    ) -> List[User]:
        """Fetch users with optional filters and pagination."""
        query = db.query(User)
        if department_id:
            query = query.filter(User.department_id == department_id)
        if role_code:
            query = query.join(Role).filter(Role.code == role_code)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Fetch user by primary key."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """Create a new corporate user."""
        # Check uniqueness
        if db.query(User).filter(User.email == user_in.email.strip().lower()).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_in.email}' đã tồn tại trong hệ thống."
            )
        if db.query(User).filter(User.username == user_in.username.strip()).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_in.username}' đã được sử dụng."
            )

        role = db.query(Role).filter(Role.code == user_in.role_code).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vai trò (Role) '{user_in.role_code}' không hợp lệ."
            )

        if user_in.department_id:
            dept = db.query(Department).filter(Department.id == user_in.department_id).first()
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Phòng ban ID {user_in.department_id} không tồn tại."
                )

        new_user = User(
            email=user_in.email.strip().lower(),
            username=user_in.username.strip(),
            full_name=user_in.full_name.strip(),
            hashed_password=get_password_hash(user_in.password),
            role_id=role.id,
            department_id=user_in.department_id,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def update_user(db: Session, user_id: UUID, user_in: UserUpdate) -> User:
        """Update existing user profile and roles."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng."
            )

        if user_in.email and user_in.email != user.email:
            if db.query(User).filter(User.email == user_in.email).first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã tồn tại.")
            user.email = user_in.email

        if user_in.username and user_in.username != user.username:
            if db.query(User).filter(User.username == user_in.username).first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username đã tồn tại.")
            user.username = user_in.username

        if user_in.full_name:
            user.full_name = user_in.full_name

        if user_in.password:
            user.hashed_password = get_password_hash(user_in.password)

        if user_in.role_code:
            role = db.query(Role).filter(Role.code == user_in.role_code).first()
            if not role:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role không hợp lệ.")
            user.role_id = role.id

        if user_in.department_id is not None:
            user.department_id = user_in.department_id

        if user_in.is_active is not None:
            user.is_active = user_in.is_active

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: UUID) -> None:
        """Deactivate a user account (Soft delete)."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng.")
        user.is_active = False
        db.commit()

    @staticmethod
    def get_departments(db: Session) -> List[Department]:
        """Fetch all departments."""
        return db.query(Department).all()

    @staticmethod
    def create_department(db: Session, dept_in: DepartmentCreate) -> Department:
        """Create new department."""
        if db.query(Department).filter(Department.code == dept_in.code.strip().upper()).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã phòng ban '{dept_in.code}' đã tồn tại."
            )
        new_dept = Department(
            code=dept_in.code.strip().upper(),
            name=dept_in.name.strip(),
            description=dept_in.description,
        )
        db.add(new_dept)
        db.commit()
        db.refresh(new_dept)
        return new_dept

    @staticmethod
    def get_roles(db: Session) -> List[Role]:
        """Fetch all roles."""
        return db.query(Role).all()


user_service = UserService()
