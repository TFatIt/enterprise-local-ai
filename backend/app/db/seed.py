"""Database Seeder script to initialize default roles, departments, permissions, and 25+ demo accounts."""

import logging
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.permission import Permission, role_permissions
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


def seed_database(db: Session) -> None:
    """Populate database with default roles, departments, permissions, and administrative/employee accounts."""
    logger.info("Checking and seeding default database entities...")

    # 1. Seed Roles
    roles_data = [
        {"code": "SUPER_ADMIN", "name": "Quản trị viên Hệ thống (Super Admin)", "description": "Toàn quyền quản trị hệ thống, người dùng, tài liệu và audit logs.", "is_system_role": True},
        {"code": "ADMIN", "name": "Quản trị viên Doanh nghiệp (Admin)", "description": "Toàn quyền quản lý tài liệu, phê duyệt và quản lý phân quyền.", "is_system_role": True},
        {"code": "IT_ADMIN", "name": "Quản trị viên IT (IT Admin)", "description": "Quản trị kỹ thuật, hỗ trợ hạ tầng, tài khoản người dùng và vận hành RAG.", "is_system_role": True},
        {"code": "IT_MANAGER", "name": "Trưởng phòng CNTT (IT Manager)", "description": "Quản lý khối công nghệ thông tin, kỹ thuật mạng, máy chủ và Helpdesk.", "is_system_role": True},
        {"code": "DEPARTMENT_MANAGER", "name": "Trưởng phòng ban (Dept Manager)", "description": "Quản lý và phân quyền tài liệu trong phạm vi phòng ban phụ trách.", "is_system_role": True},
        {"code": "EMPLOYEE", "name": "Nhân viên (Employee)", "description": "Xem và tìm kiếm tài liệu thuộc phòng ban mình và tài liệu nội bộ chung.", "is_system_role": True},
        {"code": "VIEWER", "name": "Người xem hạn chế (Viewer)", "description": "Chỉ xem các tài liệu công khai hoặc được chỉ định riêng biệt.", "is_system_role": True},
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

    # 2. Seed Permissions
    permissions_data = [
        # User Management
        {"code": "USER_VIEW", "name": "Xem danh sách người dùng", "description": "Xem thông tin hồ sơ và danh sách nhân sự", "category": "USER"},
        {"code": "USER_CREATE", "name": "Thêm mới tài khoản", "description": "Tạo tài khoản nhân viên mới vào hệ thống", "category": "USER"},
        {"code": "USER_UPDATE", "name": "Chỉnh sửa tài khoản", "description": "Cập nhật thông tin nhân viên, chức danh, liên hệ", "category": "USER"},
        {"code": "USER_DELETE", "name": "Vô hiệu hóa tài khoản", "description": "Soft delete / Vô hiệu hóa tài khoản nhân viên", "category": "USER"},
        {"code": "USER_LOCK", "name": "Khóa tài khoản", "description": "Tạm khóa quyền đăng nhập của người dùng", "category": "USER"},
        {"code": "USER_UNLOCK", "name": "Mở khóa tài khoản", "description": "Kích hoạt lại tài khoản bị khóa", "category": "USER"},
        {"code": "USER_RESET_PASSWORD", "name": "Đặt lại mật khẩu", "description": "Cấp mật khẩu tạm thời cho người dùng", "category": "USER"},
        {"code": "USER_CHANGE_ROLE", "name": "Thay đổi vai trò", "description": "Phân công vai trò RBAC cho người dùng", "category": "USER"},
        {"code": "USER_CHANGE_DEPARTMENT", "name": "Điều chuyển phòng ban", "description": "Thay đổi đơn vị công tác của nhân sự", "category": "USER"},
        # Document Management
        {"code": "DOCUMENT_VIEW", "name": "Xem tài liệu", "description": "Tra cứu và đọc tài liệu trong phạm vi được cấp quyền", "category": "DOCUMENT"},
        {"code": "DOCUMENT_CREATE", "name": "Tải lên tài liệu", "description": "Upload tài liệu nghiệp vụ mới lên hệ thống", "category": "DOCUMENT"},
        {"code": "DOCUMENT_UPDATE", "name": "Sửa đổi tài liệu", "description": "Cập nhật phiên bản hoặc thông tin tài liệu", "category": "DOCUMENT"},
        {"code": "DOCUMENT_DELETE", "name": "Xóa tài liệu", "description": "Xóa tài liệu khỏi kho tri thức doanh nghiệp", "category": "DOCUMENT"},
        {"code": "DOCUMENT_DOWNLOAD", "name": "Tải xuống tài liệu", "description": "Download tệp gốc của tài liệu", "category": "DOCUMENT"},
        {"code": "DOCUMENT_PERMISSION", "name": "Phân quyền tài liệu", "description": "Thiết lập quyền truy cập cho phòng ban hoặc cá nhân", "category": "DOCUMENT"},
        # RAG & AI
        {"code": "RAG_QUERY", "name": "Tra cứu hỏi đáp AI", "description": "Sử dụng Trợ lý AI để truy vấn tài liệu nội bộ", "category": "RAG"},
        {"code": "RAG_MANAGE", "name": "Quản trị cơ sở dữ liệu Vector", "description": "Quản lý ChromaDB, embedding và đồng bộ tri thức", "category": "RAG"},
        # Audit & System
        {"code": "AUDIT_VIEW", "name": "Xem nhật ký hệ thống", "description": "Truy xuất audit logs và lịch sử thao tác", "category": "AUDIT"},
        {"code": "SYSTEM_SETTINGS", "name": "Quản trị cấu hình hệ thống", "description": "Cài đặt tham số hệ sinh thái AI doanh nghiệp", "category": "SYSTEM"},
    ]

    perms_map = {}
    for p_data in permissions_data:
        perm = db.query(Permission).filter(Permission.code == p_data["code"]).first()
        if not perm:
            perm = Permission(**p_data)
            db.add(perm)
            db.flush()
            logger.info(f"Created permission: {perm.code}")
        perms_map[perm.code] = perm

    # Map permissions to roles
    role_perm_assignments = {
        "SUPER_ADMIN": list(perms_map.keys()),
        "ADMIN": [
            "USER_VIEW", "USER_CREATE", "USER_UPDATE", "USER_DELETE", "USER_LOCK", "USER_UNLOCK",
            "USER_RESET_PASSWORD", "USER_CHANGE_ROLE", "USER_CHANGE_DEPARTMENT",
            "DOCUMENT_VIEW", "DOCUMENT_CREATE", "DOCUMENT_UPDATE", "DOCUMENT_DELETE", "DOCUMENT_DOWNLOAD", "DOCUMENT_PERMISSION",
            "RAG_QUERY", "RAG_MANAGE", "AUDIT_VIEW"
        ],
        "IT_ADMIN": [
            "USER_VIEW", "USER_CREATE", "USER_UPDATE", "USER_LOCK", "USER_UNLOCK", "USER_RESET_PASSWORD",
            "USER_CHANGE_ROLE", "USER_CHANGE_DEPARTMENT",
            "DOCUMENT_VIEW", "DOCUMENT_CREATE", "DOCUMENT_UPDATE", "DOCUMENT_DOWNLOAD", "DOCUMENT_PERMISSION",
            "RAG_QUERY", "RAG_MANAGE", "AUDIT_VIEW"
        ],
        "IT_MANAGER": [
            "USER_VIEW", "USER_CREATE", "USER_UPDATE", "USER_LOCK", "USER_UNLOCK", "USER_RESET_PASSWORD",
            "DOCUMENT_VIEW", "DOCUMENT_CREATE", "DOCUMENT_DOWNLOAD",
            "RAG_QUERY", "AUDIT_VIEW"
        ],
        "DEPARTMENT_MANAGER": [
            "USER_VIEW", "USER_CREATE", "USER_UPDATE",
            "DOCUMENT_VIEW", "DOCUMENT_CREATE", "DOCUMENT_DOWNLOAD", "DOCUMENT_PERMISSION",
            "RAG_QUERY"
        ],
        "EMPLOYEE": [
            "DOCUMENT_VIEW", "DOCUMENT_DOWNLOAD", "RAG_QUERY"
        ],
        "VIEWER": [
            "DOCUMENT_VIEW", "RAG_QUERY"
        ],
    }

    for role_code, perm_codes in role_perm_assignments.items():
        role = roles_map.get(role_code)
        if role:
            for p_code in perm_codes:
                perm = perms_map.get(p_code)
                if perm and perm not in role.permissions:
                    role.permissions.append(perm)

    # 3. Seed Departments (Core + IT Sub-departments)
    dept_data = [
        # Enterprise Departments
        {"code": "IT", "name": "Phòng Công nghệ Thông tin", "description": "Khối hạ tầng mạng, phần mềm và kỹ thuật CNTT doanh nghiệp"},
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
        {"code": "MANAGEMENT", "name": "Ban Lãnh đạo & Điều hành", "description": "Ban Giám đốc và quản lý cấp cao doanh nghiệp"},
        # IT Sub-departments
        {"code": "IT_HELPDESK", "name": "Bộ phận IT HelpDesk & Hỗ trợ Người dùng", "description": "Tiếp nhận sự cố, cấp phát thiết bị và hỗ trợ kỹ thuật sơ cấp"},
        {"code": "IT_NETWORK", "name": "Bộ phận Quản trị Mạng & Viễn thông", "description": "Quản trị hệ thống Router, Switch, Firewall, VPN và Wifi"},
        {"code": "IT_SYSTEM", "name": "Bộ phận Quản trị Hệ thống Máy chủ", "description": "Quản trị Linux/Windows Server, ảo hóa VMware/Hyper-V và Active Directory"},
        {"code": "IT_INFRASTRUCTURE", "name": "Bộ phận Hạ tầng & Data Center", "description": "Hạ tầng phần cứng phòng máy chủ, UPS, máy phát và điều hòa chính xác"},
        {"code": "IT_SECURITY", "name": "Bộ phận An ninh Mạng & Bảo mật", "description": "Giám sát SOC, phòng chống mã độc, chính sách an toàn thông tin"},
        {"code": "IT_DBA", "name": "Bộ phận Quản trị Cơ sở Dữ liệu (DBA)", "description": "Quản trị PostgreSQL, Oracle, sao lưu dự phòng và tối ưu truy vấn"},
        {"code": "IT_DEVELOPMENT", "name": "Bộ phận Phát triển Phần mềm", "description": "Nghiên cứu và phát triển phần mềm nội bộ, tích hợp API và AI"},
        {"code": "IT_ASSET", "name": "Bộ phận Quản lý Tài sản CNTT", "description": "Theo dõi vòng đời tài sản CNTT, giấy phép phần mềm và hợp đồng bảo trì"},
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

    # 4. Seed 25+ Comprehensive Enterprise Accounts
    users_data = [
        # Executives & Admins
        {
            "username": "superadmin",
            "email": "admin@enterprise.local",
            "full_name": "System Administrator",
            "employee_code": "EMP-001",
            "phone": "0901234567",
            "position": "Giám đốc Công nghệ (CTO)",
            "password": "Admin@123456",
            "role_code": "SUPER_ADMIN",
            "dept_code": "MANAGEMENT",
            "status": "ACTIVE",
        },
        {
            "username": "admin",
            "email": "admin.corp@enterprise.local",
            "full_name": "Enterprise Administrator",
            "employee_code": "EMP-002",
            "phone": "0901234568",
            "position": "Trưởng ban Quản trị Hệ thống",
            "password": "Admin@123456",
            "role_code": "ADMIN",
            "dept_code": "MANAGEMENT",
            "status": "ACTIVE",
        },
        {
            "username": "itadmin",
            "email": "it.admin@enterprise.local",
            "full_name": "Nguyễn Văn IT Admin",
            "employee_code": "EMP-003",
            "phone": "0901234569",
            "position": "Chuyên viên Quản trị IT Cao cấp",
            "password": "Admin@123456",
            "role_code": "IT_ADMIN",
            "dept_code": "IT",
            "status": "ACTIVE",
        },
        {
            "username": "itmanager",
            "email": "it.manager@enterprise.local",
            "full_name": "Trần Quản Lý IT",
            "employee_code": "EMP-004",
            "phone": "0901234570",
            "position": "Trưởng phòng Công nghệ Thông tin",
            "password": "Admin@123456",
            "role_code": "IT_MANAGER",
            "dept_code": "IT",
            "status": "ACTIVE",
        },
        # IT Department Specialists
        {
            "username": "it_helpdesk",
            "email": "helpdesk@enterprise.local",
            "full_name": "Lê Kỹ Thuật HelpDesk",
            "employee_code": "EMP-005",
            "phone": "0902001001",
            "position": "Kỹ sư Hỗ trợ IT HelpDesk",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "IT_HELPDESK",
            "status": "ACTIVE",
        },
        {
            "username": "it_network",
            "email": "network@enterprise.local",
            "full_name": "Phạm Hạ Tầng Mạng",
            "employee_code": "EMP-006",
            "phone": "0902001002",
            "position": "Kỹ sư Quản trị Mạng",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "IT_NETWORK",
            "status": "ACTIVE",
        },
        {
            "username": "it_system",
            "email": "system@enterprise.local",
            "full_name": "Hoàng Máy Chủ System",
            "employee_code": "EMP-007",
            "phone": "0902001003",
            "position": "Kỹ sư Quản trị Hệ thống",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "IT_SYSTEM",
            "status": "ACTIVE",
        },
        {
            "username": "it_security",
            "email": "security@enterprise.local",
            "full_name": "Vũ An Ninh Mạng",
            "employee_code": "EMP-008",
            "phone": "0902001004",
            "position": "Chuyên viên An toàn Thông tin",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "IT_SECURITY",
            "status": "ACTIVE",
        },
        {
            "username": "it_dev",
            "email": "dev@enterprise.local",
            "full_name": "Đặng Phần Mềm Dev",
            "employee_code": "EMP-009",
            "phone": "0902001005",
            "position": "Kỹ sư Phát triển Phần mềm",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "IT_DEVELOPMENT",
            "status": "ACTIVE",
        },
        # Accounting Department
        {
            "username": "accounting_manager",
            "email": "acc.manager@enterprise.local",
            "full_name": "Bùi Trưởng Phòng Kế Toán",
            "employee_code": "EMP-010",
            "phone": "0903001001",
            "position": "Trưởng phòng Kế toán",
            "password": "Admin@123456",
            "role_code": "DEPARTMENT_MANAGER",
            "dept_code": "ACCOUNTING",
            "status": "ACTIVE",
        },
        {
            "username": "accounting01",
            "email": "acc01@enterprise.local",
            "full_name": "Ngô Kế Toán Tổng Hợp",
            "employee_code": "EMP-011",
            "phone": "0903001002",
            "position": "Kế toán Tổng hợp",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "ACCOUNTING",
            "status": "ACTIVE",
        },
        {
            "username": "accounting02",
            "email": "acc02@enterprise.local",
            "full_name": "Đỗ Kế Toán Thuế",
            "employee_code": "EMP-012",
            "phone": "0903001003",
            "position": "Kế toán Thuế & Ngân sách",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "ACCOUNTING",
            "status": "ACTIVE",
        },
        {
            "username": "accounting03",
            "email": "acc03@enterprise.local",
            "full_name": "Hồ Kế Toán Thanh Toán",
            "employee_code": "EMP-013",
            "phone": "0903001004",
            "position": "Kế toán Thanh toán & Quỹ",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "ACCOUNTING",
            "status": "ACTIVE",
        },
        # HR Department
        {
            "username": "hr_manager",
            "email": "hr.manager@enterprise.local",
            "full_name": "Dương Trưởng Phòng Nhân Sự",
            "employee_code": "EMP-014",
            "phone": "0904001001",
            "position": "Trưởng phòng Nhân sự",
            "password": "Admin@123456",
            "role_code": "DEPARTMENT_MANAGER",
            "dept_code": "HR",
            "status": "ACTIVE",
        },
        {
            "username": "hr01",
            "email": "hr01@enterprise.local",
            "full_name": "Mai Chuyên Viên Tuyển Dụng",
            "employee_code": "EMP-015",
            "phone": "0904001002",
            "position": "Chuyên viên Tuyển dụng & Đãi ngộ",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "HR",
            "status": "ACTIVE",
        },
        {
            "username": "hr02",
            "email": "hr02@enterprise.local",
            "full_name": "Lý Chuyên Viên C&B",
            "employee_code": "EMP-016",
            "phone": "0904001003",
            "position": "Chuyên viên Lương & Phúc lợi",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "HR",
            "status": "ACTIVE",
        },
        {
            "username": "hr03",
            "email": "hr03@enterprise.local",
            "full_name": "Vương Đào Tạo Nội Bộ",
            "employee_code": "EMP-017",
            "phone": "0904001004",
            "position": "Chuyên viên Đào tạo & Phát triển",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "HR",
            "status": "ACTIVE",
        },
        # Sales Department
        {
            "username": "sales_manager",
            "email": "sales.manager@enterprise.local",
            "full_name": "Trịnh Trưởng Phòng Kinh Doanh",
            "employee_code": "EMP-018",
            "phone": "0905001001",
            "position": "Trưởng phòng Kinh doanh",
            "password": "Admin@123456",
            "role_code": "DEPARTMENT_MANAGER",
            "dept_code": "SALES",
            "status": "ACTIVE",
        },
        {
            "username": "sales01",
            "email": "sales01@enterprise.local",
            "full_name": "Chu Kinh Doanh Miền Bắc",
            "employee_code": "EMP-019",
            "phone": "0905001002",
            "position": "Chuyên viên Bán hàng Doanh nghiệp",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "SALES",
            "status": "ACTIVE",
        },
        {
            "username": "sales02",
            "email": "sales02@enterprise.local",
            "full_name": "Đinh Tư Vấn Dự Án",
            "employee_code": "EMP-020",
            "phone": "0905001003",
            "position": "Chuyên viên Tư vấn Giải pháp",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "SALES",
            "status": "ACTIVE",
        },
        {
            "username": "sales03",
            "email": "sales03@enterprise.local",
            "full_name": "Lâm Hợp Đồng Bán Hàng",
            "employee_code": "EMP-021",
            "phone": "0905001004",
            "position": "Chuyên viên Quản lý Hợp đồng",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "SALES",
            "status": "ACTIVE",
        },
        # QA Department
        {
            "username": "qa01",
            "email": "qa01@enterprise.local",
            "full_name": "Cao Kỹ Sư QA ISO",
            "employee_code": "EMP-022",
            "phone": "0906001001",
            "position": "Kỹ sư Đảm bảo Chất lượng ISO",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "QA",
            "status": "ACTIVE",
        },
        {
            "username": "qa02",
            "email": "qa02@enterprise.local",
            "full_name": "Phùng Kiểm Soát Quy Trình",
            "employee_code": "EMP-023",
            "phone": "0906001002",
            "position": "Chuyên viên Kiểm toán Quy trình",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "QA",
            "status": "ACTIVE",
        },
        # QC Department
        {
            "username": "qc01",
            "email": "qc01@enterprise.local",
            "full_name": "Tô KCS Sản Phẩm",
            "employee_code": "EMP-024",
            "phone": "0907001001",
            "position": "Kỹ thuật viên KCS",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "QC",
            "status": "ACTIVE",
        },
        {
            "username": "qc02",
            "email": "qc02@enterprise.local",
            "full_name": "Hà Giám Định Tiêu Chuẩn",
            "employee_code": "EMP-025",
            "phone": "0907001002",
            "position": "Chuyên viên Giám định Tiêu chuẩn",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "QC",
            "status": "ACTIVE",
        },
        # Procurement Department
        {
            "username": "procurement01",
            "email": "proc01@enterprise.local",
            "full_name": "Quách Mua Hàng Thiết Bị",
            "employee_code": "EMP-026",
            "phone": "0908001001",
            "position": "Chuyên viên Thu mua Vật tư",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "PROCUREMENT",
            "status": "ACTIVE",
        },
        {
            "username": "procurement02",
            "email": "proc02@enterprise.local",
            "full_name": "Thái Đấu Thầu Cung Ứng",
            "employee_code": "EMP-027",
            "phone": "0908001002",
            "position": "Chuyên viên Đánh giá Nhà cung cấp",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "PROCUREMENT",
            "status": "ACTIVE",
        },
        # Legal Department
        {
            "username": "legal01",
            "email": "legal01@enterprise.local",
            "full_name": "Lương Luật Sư Doanh Nghiệp",
            "employee_code": "EMP-028",
            "phone": "0909001001",
            "position": "Luật sư Doanh nghiệp",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "LEGAL",
            "status": "ACTIVE",
        },
        {
            "username": "legal02",
            "email": "legal02@enterprise.local",
            "full_name": "Nghiêm Pháp Chế Tuân Thủ",
            "employee_code": "EMP-029",
            "phone": "0909001002",
            "position": "Chuyên viên Rà soát Hợp đồng",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "LEGAL",
            "status": "ACTIVE",
        },
        # Planning Department
        {
            "username": "planning01",
            "email": "plan01@enterprise.local",
            "full_name": "Tạ Điều Độ Kế Hoạch",
            "employee_code": "EMP-030",
            "phone": "0910001001",
            "position": "Chuyên viên Kế hoạch Chiến lược",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "PLANNING",
            "status": "ACTIVE",
        },
        {
            "username": "planning02",
            "email": "plan02@enterprise.local",
            "full_name": "Châu Quản Trị Dự Án",
            "employee_code": "EMP-031",
            "phone": "0910001002",
            "position": "Chuyên viên Quản lý Tiến độ",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "PLANNING",
            "status": "ACTIVE",
        },
        # General Employee & Viewer
        {
            "username": "employee",
            "email": "employee@enterprise.local",
            "full_name": "Standard Corporate Employee",
            "employee_code": "EMP-032",
            "phone": "0911001001",
            "position": "Nhân viên Nội bộ Doanh nghiệp",
            "password": "Employee@123456",
            "role_code": "EMPLOYEE",
            "dept_code": "HR",
            "status": "ACTIVE",
        },
        {
            "username": "viewer",
            "email": "viewer@enterprise.local",
            "full_name": "Limited Viewer / Auditor",
            "employee_code": "EMP-033",
            "phone": "0911001002",
            "position": "Cố vấn / Quan sát viên Bên ngoài",
            "password": "Admin@123456",
            "role_code": "VIEWER",
            "dept_code": "MANAGEMENT",
            "status": "ACTIVE",
        },
    ]

    for u_data in users_data:
        from sqlalchemy import or_
        user = db.query(User).filter(
            or_(
                User.username == u_data["username"],
                User.email == u_data["email"]
            )
        ).first()
        role = roles_map.get(u_data["role_code"])
        dept = dept_map.get(u_data["dept_code"])
        if not user:
            user = User(
                email=u_data["email"],
                username=u_data["username"],
                full_name=u_data["full_name"],
                employee_code=u_data.get("employee_code"),
                phone=u_data.get("phone"),
                position=u_data.get("position"),
                hashed_password=get_password_hash(u_data["password"]),
                role_id=role.id if role else roles_map["EMPLOYEE"].id,
                department_id=dept.id if dept else None,
                status=u_data.get("status", "ACTIVE"),
                is_active=True,
            )
            db.add(user)
            logger.info(f"Created user: {user.username} ({user.email})")
        else:
            # Update existing account with username, email, employee code, position, phone, status
            user.username = u_data["username"]
            user.email = u_data["email"]
            user.full_name = u_data["full_name"]
            user.employee_code = u_data.get("employee_code") or user.employee_code
            user.phone = u_data.get("phone") or user.phone
            user.position = u_data.get("position") or user.position
            user.status = u_data.get("status", "ACTIVE")
            if role:
                user.role_id = role.id
            if dept:
                user.department_id = dept.id

    db.commit()
    logger.info("Database seeding completed successfully with all permissions, departments, and 33 demo accounts.")
