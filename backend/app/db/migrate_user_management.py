import sys
import os
from pathlib import Path

# Add backend directory to sys.path if not present
backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import logging
import sqlite3
from sqlalchemy import text
from app.db.session import engine, db_url
from app.db.base import Base
import app.models  # Ensures all models are registered

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Migrate SQLite schema safely adding columns and tables without data loss."""
    logger.info("Starting User Management database migration...")

    # 1. Create any missing tables (permissions, role_permissions)
    Base.metadata.create_all(bind=engine)
    logger.info("Ensured all tables exist.")

    # 2. If SQLite, add missing columns via ALTER TABLE
    with engine.connect() as conn:
        # Check users table columns
        users_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users);").fetchall()]
        logger.info(f"Existing columns in 'users': {users_cols}")

        columns_to_add = [
            ("employee_code", "VARCHAR(50)"),
            ("phone", "VARCHAR(30)"),
            ("position", "VARCHAR(100)"),
            ("status", "VARCHAR(20) DEFAULT 'ACTIVE'"),
            ("avatar", "VARCHAR(500)"),
            ("force_password_change", "BOOLEAN DEFAULT 0"),
            ("last_login_at", "DATETIME"),
            ("password_changed_at", "DATETIME"),
            ("deleted_at", "DATETIME"),
            ("created_by", "CHAR(36)"),
            ("updated_by", "CHAR(36)"),
            ("deleted_by", "CHAR(36)"),
        ]

        for col_name, col_def in columns_to_add:
            if col_name not in users_cols:
                logger.info(f"Adding column '{col_name}' to 'users' table...")
                conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};")

        # Check roles table columns
        roles_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(roles);").fetchall()]
        if "is_system_role" not in roles_cols:
            logger.info("Adding column 'is_system_role' to 'roles' table...")
            conn.exec_driver_sql("ALTER TABLE roles ADD COLUMN is_system_role BOOLEAN DEFAULT 1;")

        # Check audit_logs table columns
        audit_info = conn.exec_driver_sql("PRAGMA table_info(audit_logs);").fetchall()
        id_col = [row for row in audit_info if row[1] == "id"]
        if id_col and id_col[0][2].upper() == "BIGINT":
            logger.info("Migrating audit_logs.id from BIGINT to INTEGER PRIMARY KEY AUTOINCREMENT...")
            conn.exec_driver_sql("""
                CREATE TABLE IF NOT EXISTS audit_logs_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id CHAR(36),
                    target_user_id CHAR(36),
                    action VARCHAR(100) NOT NULL,
                    resource VARCHAR(100) NOT NULL,
                    result VARCHAR(20) DEFAULT 'SUCCESS' NOT NULL,
                    details JSON NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(255),
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
                );
            """)
            conn.exec_driver_sql("""
                INSERT INTO audit_logs_new (user_id, target_user_id, action, resource, result, details, ip_address, user_agent, created_at)
                SELECT user_id, 
                       CASE WHEN target_user_id IS NOT NULL THEN target_user_id ELSE NULL END, 
                       action, 
                       resource, 
                       COALESCE(result, 'SUCCESS'), 
                       details, 
                       ip_address, 
                       CASE WHEN user_agent IS NOT NULL THEN user_agent ELSE NULL END, 
                       created_at 
                FROM audit_logs;
            """)
            conn.exec_driver_sql("DROP TABLE audit_logs;")
            conn.exec_driver_sql("ALTER TABLE audit_logs_new RENAME TO audit_logs;")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);")
        else:
            audit_cols = [row[1] for row in audit_info]
            if "target_user_id" not in audit_cols:
                logger.info("Adding column 'target_user_id' to 'audit_logs' table...")
                conn.exec_driver_sql("ALTER TABLE audit_logs ADD COLUMN target_user_id CHAR(36);")
            if "result" not in audit_cols:
                logger.info("Adding column 'result' to 'audit_logs' table...")
                conn.exec_driver_sql("ALTER TABLE audit_logs ADD COLUMN result VARCHAR(20) DEFAULT 'SUCCESS';")
            if "user_agent" not in audit_cols:
                logger.info("Adding column 'user_agent' to 'audit_logs' table...")
                conn.exec_driver_sql("ALTER TABLE audit_logs ADD COLUMN user_agent VARCHAR(255);")

        # Ensure existing users have status='ACTIVE' if NULL
        conn.exec_driver_sql("UPDATE users SET status = 'ACTIVE' WHERE status IS NULL OR status = '';")
        conn.commit()

    logger.info("User Management migration completed successfully!")


if __name__ == "__main__":
    run_migration()
