"""Department Permission Model for Cross-Department Access."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID


class DepartmentPermission(Base):
    __tablename__ = "department_permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=True, index=True)
    permission_type = Column(String(20), default="VIEW", nullable=False)  # VIEW, MANAGE
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    department = relationship("Department", foreign_keys=[department_id], lazy="joined")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    role = relationship("Role", foreign_keys=[role_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<DepartmentPermission dept={self.department_id} user={self.user_id} role={self.role_id} type={self.permission_type}>"
