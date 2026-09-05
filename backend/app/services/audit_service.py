"""Audit Service for Enterprise Compliance and Security Event Logging."""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for registering auditable enterprise actions."""

    @staticmethod
    def log_event(
        db: Session,
        action: str,
        resource: str = "DOCUMENTS",
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[AuditLog]:
        """Record an audit log entry in database."""
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                ip_address=ip_address,
                details=details or {},
            )
            db.add(audit)
            db.commit()
            return audit
        except Exception as e:
            logger.warning(f"Failed to write audit log [{action}]: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            return None


audit_service = AuditService()
