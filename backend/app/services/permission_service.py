"""Permission Service for Enterprise Document Access Control (EDAC)."""

from typing import Optional, List, Set
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.department_permission import DepartmentPermission


class PermissionService:
    """Service evaluating role-based and department-based document access control."""

    SUPER_ROLES = {"SUPER_ADMIN"}
    ADMIN_ROLES = {"SUPER_ADMIN", "ADMIN", "IT_ADMIN", "IT_MANAGER"}
    MANAGEMENT_ROLES = {"SUPER_ADMIN", "ADMIN", "IT_ADMIN", "IT_MANAGER", "MANAGER", "DEPARTMENT_MANAGER"}

    @classmethod
    def can_user_access_document(
        cls,
        db: Session,
        user: User,
        doc: Document,
        action: str = "VIEW"
    ) -> bool:
        """Evaluate if user has permission to perform action on document."""
        role_code = user.role.code if user.role else "EMPLOYEE"

        # 1. Super Admin has unrestricted access to everything
        if role_code in cls.SUPER_ROLES:
            return True

        # 2. Admin has full document access and management capabilities
        if role_code in cls.ADMIN_ROLES:
            return True

        # 3. Check explicit document permissions (User -> Document or Role -> Document)
        explicit_perms = db.query(DocumentPermission).filter(
            DocumentPermission.document_id == doc.id,
            or_(
                DocumentPermission.user_id == user.id,
                DocumentPermission.role_id == user.role_id
            )
        ).all()

        perm_types = {p.permission_type for p in explicit_perms}
        if "MANAGE" in perm_types:
            return True
        if "EDIT" in perm_types and action in ("VIEW", "DOWNLOAD", "EDIT"):
            return True
        if "VIEW" in perm_types and action in ("VIEW", "DOWNLOAD"):
            return True

        # 4. Handle CONFIDENTIAL security level
        # Confidential docs strictly require explicit permission or ownership
        if doc.security_level == "CONFIDENTIAL":
            if doc.owner_id == user.id or doc.uploaded_by == user.id:
                return True
            return False

        # 5. Handle VIEW / DOWNLOAD actions
        if action in ("VIEW", "DOWNLOAD"):
            if doc.security_level == "PUBLIC":
                return True

            if doc.security_level == "INTERNAL":
                return role_code != "VIEWER"

            if doc.security_level == "DEPARTMENT":
                # General Managers can view all company departments
                if role_code == "MANAGER":
                    return True

                # User belongs to document's department
                if user.department_id and doc.department_id and user.department_id == doc.department_id:
                    return True

                # Check Cross-department permissions
                if doc.department_id:
                    dept_perm = db.query(DepartmentPermission).filter(
                        DepartmentPermission.department_id == doc.department_id,
                        or_(
                            DepartmentPermission.user_id == user.id,
                            DepartmentPermission.role_id == user.role_id
                        )
                    ).first()
                    if dept_perm:
                        return True

                # Document owner / uploader can view their own document
                if doc.owner_id == user.id or doc.uploaded_by == user.id:
                    return True

                return False

        # 6. Handle EDIT, DELETE, MANAGE actions
        if action in ("EDIT", "DELETE", "MANAGE"):
            # Document owner or uploader
            if doc.owner_id == user.id or doc.uploaded_by == user.id:
                return True

            # Department Manager managing their own department's documents
            if role_code == "DEPARTMENT_MANAGER" and user.department_id and doc.department_id == user.department_id:
                return True

            # Check cross-department MANAGE permission
            if doc.department_id:
                dept_perm = db.query(DepartmentPermission).filter(
                    DepartmentPermission.department_id == doc.department_id,
                    DepartmentPermission.permission_type == "MANAGE",
                    or_(
                        DepartmentPermission.user_id == user.id,
                        DepartmentPermission.role_id == user.role_id
                    )
                ).first()
                if dept_perm:
                    return True

            return False

        return False

    @classmethod
    def get_document_query_filter(cls, db: Session, user: User):
        """Construct SQLAlchemy filter clause for safe backend-level document queries."""
        role_code = user.role.code if user.role else "EMPLOYEE"

        # Super Admin & Admin see everything
        if role_code in cls.ADMIN_ROLES:
            return None

        # Fetch all document IDs explicitly granted to user or role
        granted_doc_ids: List[UUID] = [
            row[0] for row in db.query(DocumentPermission.document_id).filter(
                or_(
                    DocumentPermission.user_id == user.id,
                    DocumentPermission.role_id == user.role_id
                )
            ).all()
        ]

        # Fetch department IDs granted to user or role
        granted_dept_ids: List[int] = [
            row[0] for row in db.query(DepartmentPermission.department_id).filter(
                or_(
                    DepartmentPermission.user_id == user.id,
                    DepartmentPermission.role_id == user.role_id
                )
            ).all()
        ]

        # General Managers see all non-confidential + granted confidential
        if role_code == "MANAGER":
            return or_(
                Document.security_level.in_(["PUBLIC", "INTERNAL", "DEPARTMENT"]),
                Document.id.in_(granted_doc_ids),
                Document.uploaded_by == user.id,
                Document.owner_id == user.id
            )

        # Department Managers and Employees
        if role_code in ("DEPARTMENT_MANAGER", "EMPLOYEE"):
            dept_conditions = []
            if user.department_id:
                dept_conditions.append(Document.department_id == user.department_id)
            if granted_dept_ids:
                dept_conditions.append(Document.department_id.in_(granted_dept_ids))

            own_dept_clause = or_(*dept_conditions) if dept_conditions else False

            return or_(
                Document.security_level == "PUBLIC",
                Document.security_level == "INTERNAL",
                and_(Document.security_level == "DEPARTMENT", own_dept_clause),
                Document.id.in_(granted_doc_ids),
                Document.uploaded_by == user.id,
                Document.owner_id == user.id
            )

        # Viewers (restricted)
        return or_(
            Document.security_level == "PUBLIC",
            Document.id.in_(granted_doc_ids),
            Document.uploaded_by == user.id,
            Document.owner_id == user.id
        )

    @classmethod
    def can_user_upload_to_department(
        cls,
        user: User,
        department_id: Optional[int]
    ) -> bool:
        """Check if user is allowed to upload documents into specified department."""
        role_code = user.role.code if user.role else "EMPLOYEE"
        if role_code in cls.ADMIN_ROLES:
            return True
        if role_code == "DEPARTMENT_MANAGER":
            return department_id is not None and user.department_id == department_id
        return False


permission_service = PermissionService()
