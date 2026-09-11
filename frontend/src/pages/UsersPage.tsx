import React, { useState, useEffect } from 'react';
import {
  Users as UsersIcon,
  UserPlus,
  Search,
  Filter,
  RotateCcw,
  Download,
  Upload,
  Lock,
  Unlock,
  KeyRound,
  Edit2,
  Trash2,
  Eye,
  Shield,
  Building2,
  CheckCircle2,
  AlertCircle,
  Clock,
  X,
  Copy,
  Plus,
  FileSpreadsheet,
  Activity
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type {
  User,
  Role,
  Department,
  PermissionItem,
  UserStats,
  UserActivityItem
} from '../types';

export const UsersPage: React.FC = () => {
  const { user: currentUser, isSuperAdmin, isITAdmin } = useAuth();

  // Navigation & Sub-tabs
  const [activeSubTab, setActiveSubTab] = useState<'users' | 'departments' | 'roles' | 'audit'>('users');

  // Stats state
  const [stats, setStats] = useState<UserStats | null>(null);

  // Users listing states
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDeptId, setSelectedDeptId] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // Metadata
  const [roles, setRoles] = useState<Role[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [permissions, setPermissions] = useState<PermissionItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<UserActivityItem[]>([]);

  // Selection & Bulk actions
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const [bulkDeptId, setBulkDeptId] = useState<string>('');

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Add User Form state
  const [addForm, setAddForm] = useState({
    fullName: '',
    username: '',
    email: '',
    phone: '',
    employeeCode: '',
    position: '',
    departmentId: '',
    roleCode: 'EMPLOYEE',
    password: '',
    confirmPassword: '',
    status: 'ACTIVE',
  });
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  // Edit User Form state
  const [editForm, setEditForm] = useState({
    fullName: '',
    phone: '',
    employeeCode: '',
    position: '',
    departmentId: '',
    roleCode: '',
    status: 'ACTIVE',
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  // Reset Password State
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [resetLoading, setResetLoading] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  // User Detail Activity & Permissions
  const [detailTab, setDetailTab] = useState<'overview' | 'permissions' | 'activity'>('overview');
  const [detailPermissions, setDetailPermissions] = useState<string[]>([]);
  const [detailActivity, setDetailActivity] = useState<UserActivityItem[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);

  // CSV Import State
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState<{ imported: number; errors: string[] } | null>(null);

  // Department Modal State
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [deptForm, setDeptForm] = useState({ code: '', name: '', description: '' });
  const [deptLoading, setDeptLoading] = useState(false);
  const [deptError, setDeptError] = useState<string | null>(null);

  // Notification Banner
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // Initial Data Fetch
  useEffect(() => {
    loadMetadata();
    loadStats();
    loadUsers();
  }, []);

  const loadMetadata = async () => {
    // Load departments with direct endpoint and fallback
    try {
      const dResp = await api.get<Department[]>('/departments').catch(() => api.get<Department[]>('/users/departments'));
      if (dResp?.data && Array.isArray(dResp.data)) {
        setDepartments(dResp.data);
      }
    } catch (err) {
      console.error('Failed to load departments', err);
    }

    // Load roles with direct endpoint and fallback
    try {
      const rResp = await api.get<Role[]>('/departments/roles').catch(() => api.get<Role[]>('/users/roles'));
      if (rResp?.data && Array.isArray(rResp.data)) {
        setRoles(rResp.data);
      }
    } catch (err) {
      console.error('Failed to load roles', err);
    }

    // Load permissions
    try {
      const pResp = await api.get<PermissionItem[]>('/users/permissions');
      if (pResp?.data && Array.isArray(pResp.data)) {
        setPermissions(pResp.data);
      }
    } catch (err) {
      console.error('Failed to load permissions', err);
    }
  };

  // -------------------------------------------------------------
  // Actions: Department Management
  // -------------------------------------------------------------
  const openAddDeptModal = () => {
    setEditingDept(null);
    setDeptForm({ code: '', name: '', description: '' });
    setDeptError(null);
    setShowDeptModal(true);
  };

  const openEditDeptModal = (d: Department) => {
    setEditingDept(d);
    setDeptForm({ code: d.code, name: d.name, description: d.description || '' });
    setDeptError(null);
    setShowDeptModal(true);
  };

  const handleSaveDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deptForm.name.trim()) {
      setDeptError('Vui lòng nhập tên phòng ban.');
      return;
    }
    if (!editingDept && !deptForm.code.trim()) {
      setDeptError('Vui lòng nhập mã phòng ban (ví dụ: RND, MARKETING).');
      return;
    }

    setDeptLoading(true);
    setDeptError(null);
    try {
      if (editingDept) {
        await api.put(`/departments/${editingDept.id}`, {
          name: deptForm.name.trim(),
          description: deptForm.description.trim() || undefined,
        });
        showNotification(`Đã cập nhật thông tin phòng ban "${deptForm.name}".`);
      } else {
        await api.post('/departments', {
          code: deptForm.code.trim().toUpperCase(),
          name: deptForm.name.trim(),
          description: deptForm.description.trim() || undefined,
        });
        showNotification(`Đã tạo mới phòng ban "${deptForm.name}".`);
      }
      setShowDeptModal(false);
      loadMetadata();
      loadStats();
    } catch (err: any) {
      setDeptError(err.response?.data?.detail || 'Không thể lưu thông tin phòng ban.');
    } finally {
      setDeptLoading(false);
    }
  };

  const handleDeleteDept = async (d: Department) => {
    const deptUsers = users.filter((u) => u.department_id === d.id);
    if (deptUsers.length > 0) {
      alert(`Không thể xóa phòng ban "${d.name}" vì đang có ${deptUsers.length} nhân viên trực thuộc. Vui lòng điều chuyển nhân sự sang phòng ban khác trước.`);
      return;
    }
    if (!window.confirm(`Bạn có chắc chắn muốn xóa phòng ban "${d.name}" (${d.code})?`)) return;

    try {
      await api.delete(`/departments/${d.id}`);
      showNotification(`Đã xóa phòng ban "${d.name}".`);
      loadMetadata();
      loadStats();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể xóa phòng ban.');
    }
  };

  const loadStats = async () => {
    try {
      const resp = await api.get<UserStats>('/users/stats/summary');
      setStats(resp.data);
    } catch (err) {
      console.error('Failed to load stats', err);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {};
      if (searchTerm.trim()) params.search = searchTerm.trim();
      if (selectedDeptId) params.department_id = selectedDeptId;
      if (selectedRole) params.role_code = selectedRole;
      if (selectedStatus) params.status = selectedStatus;

      const resp = await api.get<User[]>('/users', { params });
      setUsers(resp.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Không thể tải danh sách tài khoản.');
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    try {
      // Mock or fetch from api
      if (users.length > 0) {
        const resp = await api.get<UserActivityItem[]>(`/users/${users[0].id}/activity`);
        setAuditLogs(resp.data);
      }
    } catch (err) {
      console.error('Audit log error', err);
    }
  };

  // Search & Filter Trigger
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadUsers();
  };

  const handleResetFilter = () => {
    setSearchTerm('');
    setSelectedDeptId('');
    setSelectedRole('');
    setSelectedStatus('');
    setTimeout(() => {
      api.get<User[]>('/users').then((r) => setUsers(r.data));
    }, 0);
  };

  // Role Badge Formatter
  const getRoleBadge = (code?: string) => {
    switch (code) {
      case 'SUPER_ADMIN':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">Super Admin</span>;
      case 'ADMIN':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">Admin</span>;
      case 'IT_ADMIN':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">IT Admin</span>;
      case 'IT_MANAGER':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30">IT Manager</span>;
      case 'DEPARTMENT_MANAGER':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">Trưởng phòng</span>;
      case 'VIEWER':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-slate-700/60 text-slate-300 border border-slate-600/40">Viewer</span>;
      default:
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Nhân viên</span>;
    }
  };

  // Status Badge Formatter
  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Hoạt động
          </span>
        );
      case 'LOCKED':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-rose-400">
            <span className="w-2 h-2 rounded-full bg-rose-400"></span>
            Đã khóa
          </span>
        );
      case 'SUSPENDED':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-orange-400">
            <span className="w-2 h-2 rounded-full bg-orange-400"></span>
            Đình chỉ
          </span>
        );
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-yellow-400">
            <span className="w-2 h-2 rounded-full bg-yellow-400"></span>
            Chờ kích hoạt
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400">
            <span className="w-2 h-2 rounded-full bg-slate-400"></span>
            Vô hiệu hóa
          </span>
        );
    }
  };

  // -------------------------------------------------------------
  // Actions: Add User
  // -------------------------------------------------------------
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (addForm.password !== addForm.confirmPassword) {
      setAddError('Mật khẩu và xác nhận mật khẩu không khớp.');
      return;
    }
    setAddLoading(true);
    setAddError(null);

    try {
      await api.post('/users', {
        email: addForm.email,
        username: addForm.username,
        full_name: addForm.fullName,
        employee_code: addForm.employeeCode || undefined,
        phone: addForm.phone || undefined,
        position: addForm.position || undefined,
        role_code: addForm.roleCode,
        department_id: addForm.departmentId ? parseInt(addForm.departmentId) : undefined,
        password: addForm.password,
        status: addForm.status,
      });
      setShowAddModal(false);
      setAddForm({
        fullName: '',
        username: '',
        email: '',
        phone: '',
        employeeCode: '',
        position: '',
        departmentId: '',
        roleCode: 'EMPLOYEE',
        password: '',
        confirmPassword: '',
        status: 'ACTIVE',
      });
      showNotification('Tạo tài khoản người dùng thành công!');
      loadUsers();
      loadStats();
    } catch (err: any) {
      setAddError(err.response?.data?.detail || 'Không thể tạo người dùng.');
    } finally {
      setAddLoading(false);
    }
  };

  // -------------------------------------------------------------
  // Actions: Edit User
  // -------------------------------------------------------------
  const openEditModal = (u: User) => {
    setSelectedUser(u);
    const rCode = typeof u.role === 'string' ? u.role : u.role?.code;
    setEditForm({
      fullName: u.full_name,
      phone: u.phone || '',
      employeeCode: u.employee_code || '',
      position: u.position || '',
      departmentId: u.department_id ? u.department_id.toString() : '',
      roleCode: rCode || 'EMPLOYEE',
      status: u.status || 'ACTIVE',
    });
    setEditError(null);
    setShowEditModal(true);
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    setEditLoading(true);
    setEditError(null);

    try {
      await api.put(`/users/${selectedUser.id}`, {
        full_name: editForm.fullName,
        phone: editForm.phone || null,
        employee_code: editForm.employeeCode || null,
        position: editForm.position || null,
        role_code: editForm.roleCode,
        department_id: editForm.departmentId ? parseInt(editForm.departmentId) : null,
        status: editForm.status,
      });
      setShowEditModal(false);
      showNotification('Cập nhật tài khoản thành công!');
      loadUsers();
      loadStats();
    } catch (err: any) {
      setEditError(err.response?.data?.detail || 'Không thể cập nhật tài khoản.');
    } finally {
      setEditLoading(false);
    }
  };

  // -------------------------------------------------------------
  // Actions: Lock / Unlock
  // -------------------------------------------------------------
  const handleToggleLock = async (u: User) => {
    const isLocked = u.status === 'LOCKED';
    const actionText = isLocked ? 'mở khóa' : 'khóa';
    if (!window.confirm(`Bạn có chắc chắn muốn ${actionText} tài khoản "${u.username}"?`)) return;

    try {
      if (isLocked) {
        await api.post(`/users/${u.id}/unlock`);
        showNotification(`Đã mở khóa tài khoản "${u.username}".`);
      } else {
        await api.post(`/users/${u.id}/lock`);
        showNotification(`Đã khóa tài khoản "${u.username}".`);
      }
      loadUsers();
      loadStats();
    } catch (err: any) {
      alert(err.response?.data?.detail || `Không thể ${actionText} tài khoản.`);
    }
  };

  // -------------------------------------------------------------
  // Actions: Reset Password
  // -------------------------------------------------------------
  const openResetModal = (u: User) => {
    setSelectedUser(u);
    setTempPassword(null);
    setCopySuccess(false);
    setShowResetModal(true);
  };

  const handleConfirmResetPassword = async () => {
    if (!selectedUser) return;
    setResetLoading(true);
    try {
      const resp = await api.post<{ temporary_password: string }>(`/users/${selectedUser.id}/reset-password`);
      setTempPassword(resp.data.temporary_password);
      showNotification('Đặt lại mật khẩu thành công! Hãy lưu lại mật khẩu tạm.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể đặt lại mật khẩu.');
    } finally {
      setResetLoading(false);
    }
  };

  const handleCopyPassword = () => {
    if (tempPassword) {
      navigator.clipboard.writeText(tempPassword);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  // -------------------------------------------------------------
  // Actions: Delete (Soft Delete)
  // -------------------------------------------------------------
  const handleDeleteUser = async (u: User) => {
    if (!window.confirm(`CẢNH BÁO: Bạn có chắc chắn muốn vô hiệu hóa tài khoản "${u.username}" (${u.full_name})?`)) return;

    try {
      await api.delete(`/users/${u.id}`);
      showNotification(`Đã vô hiệu hóa tài khoản "${u.username}".`);
      loadUsers();
      loadStats();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể vô hiệu hóa tài khoản.');
    }
  };

  // -------------------------------------------------------------
  // Actions: User Detail View
  // -------------------------------------------------------------
  const openDetailModal = async (u: User) => {
    setSelectedUser(u);
    setDetailTab('overview');
    setShowDetailModal(true);
    setDetailLoading(true);

    try {
      const [permResp, actResp] = await Promise.all([
        api.get<string[]>(`/users/${u.id}/permissions`),
        api.get<UserActivityItem[]>(`/users/${u.id}/activity`),
      ]);
      setDetailPermissions(permResp.data);
      setDetailActivity(actResp.data);
    } catch (err) {
      console.error('Error loading user details', err);
    } finally {
      setDetailLoading(false);
    }
  };

  // -------------------------------------------------------------
  // Actions: Bulk Operations
  // -------------------------------------------------------------
  const toggleSelectUser = (id: string) => {
    if (selectedUserIds.includes(id)) {
      setSelectedUserIds(selectedUserIds.filter((uid) => uid !== id));
    } else {
      setSelectedUserIds([...selectedUserIds, id]);
    }
  };

  const toggleSelectAll = () => {
    if (selectedUserIds.length === users.length) {
      setSelectedUserIds([]);
    } else {
      setSelectedUserIds(users.map((u) => u.id));
    }
  };

  const handleBulkAction = async (action: 'ACTIVATE' | 'DEACTIVATE' | 'LOCK' | 'UNLOCK' | 'ASSIGN_DEPARTMENT') => {
    if (selectedUserIds.length === 0) return;
    if (!window.confirm(`Thực hiện thao tác "${action}" trên ${selectedUserIds.length} tài khoản đã chọn?`)) return;

    setBulkActionLoading(true);
    try {
      const resp = await api.post<{ affected: number; skipped: number }>('/users/bulk-action', {
        user_ids: selectedUserIds,
        action: action,
        target_department_id: action === 'ASSIGN_DEPARTMENT' && bulkDeptId ? parseInt(bulkDeptId) : undefined,
      });
      showNotification(`Đã xử lý ${resp.data.affected} tài khoản (${resp.data.skipped} bỏ qua do quy tắc phân quyền).`);
      setSelectedUserIds([]);
      loadUsers();
      loadStats();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Thao tác hàng loạt thất bại.');
    } finally {
      setBulkActionLoading(false);
    }
  };

  // -------------------------------------------------------------
  // Actions: CSV Export & Import
  // -------------------------------------------------------------
  const handleExportCSV = async () => {
    try {
      const resp = await api.get('/users/export/csv', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'enterprise_users.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      showNotification('Đã xuất danh sách người dùng ra file CSV!');
    } catch (err) {
      alert('Xuất CSV thất bại.');
    }
  };

  const handleImportCSV = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;

    setImportLoading(true);
    setImportResult(null);

    const formData = new FormData();
    formData.append('file', importFile);

    try {
      const resp = await api.post('/users/import/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setImportResult(resp.data);
      showNotification(`Đã nạp thành công ${resp.data.imported} tài khoản!`);
      loadUsers();
      loadStats();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Nhập CSV thất bại.');
    } finally {
      setImportLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-5 right-5 z-50 p-4 rounded-xl shadow-2xl flex items-center gap-3 text-xs font-semibold animate-in slide-in-from-top-5 duration-300 ${
          notification.type === 'success'
            ? 'bg-emerald-500 text-white shadow-emerald-500/20'
            : 'bg-rose-500 text-white shadow-rose-500/20'
        }`}>
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{notification.message}</span>
        </div>
      )}

      {/* Header & Sub-tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <UsersIcon className="w-6 h-6 text-indigo-400" />
            Quản trị Người dùng & Tài khoản Doanh nghiệp
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Quản lý danh tính nhân sự, phân quyền RBAC đa tầng và cô lập phạm vi phòng ban
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveSubTab('users')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeSubTab === 'users'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <UsersIcon className="w-3.5 h-3.5" />
            <span>Tài khoản ({users.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab('departments')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeSubTab === 'departments'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Phòng ban ({departments.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab('roles')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeSubTab === 'roles'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Vai trò & Quyền</span>
          </button>
          <button
            onClick={() => {
              setActiveSubTab('audit');
              loadAuditLogs();
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeSubTab === 'audit'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Audit Log</span>
          </button>
        </div>
      </div>

      {/* KPI Dashboard Metrics Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm">
            <span className="text-[11px] font-medium text-slate-400 block mb-1">Tổng người dùng</span>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-extrabold text-white tracking-tight">{stats.total_users}</span>
              <UsersIcon className="w-4 h-4 text-indigo-400 opacity-60" />
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 shadow-sm">
            <span className="text-[11px] font-medium text-emerald-300 block mb-1">Đang hoạt động</span>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-extrabold text-emerald-400 tracking-tight">{stats.active_users}</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400 opacity-80" />
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-rose-500/5 border border-rose-500/20 shadow-sm">
            <span className="text-[11px] font-medium text-rose-300 block mb-1">Tài khoản bị khóa</span>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-extrabold text-rose-400 tracking-tight">{stats.locked_users}</span>
              <Lock className="w-4 h-4 text-rose-400 opacity-80" />
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-yellow-500/5 border border-yellow-500/20 shadow-sm">
            <span className="text-[11px] font-medium text-yellow-300 block mb-1">Chờ kích hoạt</span>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-extrabold text-yellow-400 tracking-tight">{stats.pending_users}</span>
              <Clock className="w-4 h-4 text-yellow-400 opacity-80" />
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-cyan-500/5 border border-cyan-500/20 shadow-sm">
            <span className="text-[11px] font-medium text-cyan-300 block mb-1">Phòng ban</span>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-extrabold text-cyan-400 tracking-tight">{stats.total_departments}</span>
              <Building2 className="w-4 h-4 text-cyan-400 opacity-80" />
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-purple-500/5 border border-purple-500/20 shadow-sm">
            <span className="text-[11px] font-medium text-purple-300 block mb-1">Quản trị viên</span>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-extrabold text-purple-400 tracking-tight">{stats.admin_users}</span>
              <Shield className="w-4 h-4 text-purple-400 opacity-80" />
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SUB-TAB 1: USERS TABLE & ACTIONS */}
      {/* ========================================================= */}
      {activeSubTab === 'users' && (
        <div className="space-y-4">
          {/* Action and Filter Toolbars */}
          <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <form onSubmit={handleSearch} className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
              {/* Search input */}
              <div className="relative flex-1 min-w-[240px]">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Tìm theo Tên, Username, Email, Mã NV, Số điện thoại..."
                  className="w-full pl-9 pr-3.5 py-2 rounded-xl bg-slate-950/70 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-indigo-500 placeholder:text-slate-500"
                />
              </div>

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={selectedDeptId}
                  onChange={(e) => setSelectedDeptId(e.target.value)}
                  className="px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-700/80 text-slate-300 text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Tất cả phòng ban ({departments.length})</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>

                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-700/80 text-slate-300 text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Tất cả vai trò ({roles.length})</option>
                  {roles.map((r) => (
                    <option key={r.code} value={r.code}>
                      {r.name}
                    </option>
                  ))}
                </select>

                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-700/80 text-slate-300 text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Tất cả trạng thái</option>
                  <option value="ACTIVE">Hoạt động</option>
                  <option value="LOCKED">Đã khóa</option>
                  <option value="PENDING">Chờ kích hoạt</option>
                  <option value="INACTIVE">Vô hiệu hóa</option>
                  <option value="SUSPENDED">Đình chỉ</option>
                </select>

                <button
                  type="submit"
                  className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-all flex items-center gap-1.5"
                >
                  <Filter className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Lọc</span>
                </button>

                <button
                  type="button"
                  onClick={handleResetFilter}
                  className="p-2 rounded-xl bg-slate-800/60 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
                  title="Đặt lại bộ lọc"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                <button
                  type="button"
                  onClick={handleExportCSV}
                  className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Xuất CSV</span>
                </button>

                {isSuperAdmin || isITAdmin ? (
                  <button
                    type="button"
                    onClick={() => {
                      setImportFile(null);
                      setImportResult(null);
                      setShowImportModal(true);
                    }}
                    className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all flex items-center gap-1.5"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    <span>Nhập CSV</span>
                  </button>
                ) : null}

                <button
                  type="button"
                  onClick={() => {
                    setAddError(null);
                    setShowAddModal(true);
                  }}
                  className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all flex items-center gap-1.5 shrink-0"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Thêm tài khoản</span>
                </button>
              </div>
            </form>

            {/* Bulk Action Bar */}
            {selectedUserIds.length > 0 && (
              <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-indigo-950/20 p-2.5 rounded-xl border-indigo-900/30 animate-in fade-in">
                <span className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                  Đã chọn {selectedUserIds.length} tài khoản
                </span>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => handleBulkAction('ACTIVATE')}
                    disabled={bulkActionLoading}
                    className="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 text-xs font-medium border border-emerald-500/30 transition-all"
                  >
                    Kích hoạt
                  </button>
                  <button
                    onClick={() => handleBulkAction('LOCK')}
                    disabled={bulkActionLoading}
                    className="px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 text-xs font-medium border border-rose-500/30 transition-all"
                  >
                    Khóa tài khoản
                  </button>
                  <button
                    onClick={() => handleBulkAction('DEACTIVATE')}
                    disabled={bulkActionLoading}
                    className="px-2.5 py-1 rounded-lg bg-slate-700/60 text-slate-300 hover:bg-slate-700 text-xs font-medium border border-slate-600 transition-all"
                  >
                    Vô hiệu hóa
                  </button>

                  <div className="flex items-center gap-1">
                    <select
                      value={bulkDeptId}
                      onChange={(e) => setBulkDeptId(e.target.value)}
                      className="px-2 py-1 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300"
                    >
                      <option value="">Chọn phòng ban gán...</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => handleBulkAction('ASSIGN_DEPARTMENT')}
                      disabled={!bulkDeptId || bulkActionLoading}
                      className="px-2.5 py-1 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 text-xs font-medium transition-all disabled:opacity-50"
                    >
                      Gán PB
                    </button>
                  </div>

                  <button
                    onClick={() => setSelectedUserIds([])}
                    className="text-xs text-slate-400 hover:text-white px-2 py-1"
                  >
                    Hủy chọn
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* User Table */}
          <div className="rounded-2xl bg-slate-900/90 border border-slate-800 overflow-hidden shadow-xl">
            {loading ? (
              <div className="p-12 text-center text-slate-400">
                <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                <p className="text-xs">Đang tải danh sách người dùng...</p>
              </div>
            ) : error ? (
              <div className="p-8 text-center text-rose-400 text-xs">
                <AlertCircle className="w-6 h-6 mx-auto mb-2 opacity-80" />
                <p>{error}</p>
              </div>
            ) : users.length === 0 ? (
              <div className="p-12 text-center text-slate-500 text-xs">
                <UsersIcon className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p>Không tìm thấy tài khoản người dùng phù hợp.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="p-3.5 w-10 text-center">
                        <input
                          type="checkbox"
                          checked={selectedUserIds.length === users.length && users.length > 0}
                          onChange={toggleSelectAll}
                          className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                        />
                      </th>
                      <th className="p-3.5 font-semibold">Nhân viên & Tài khoản</th>
                      <th className="p-3.5 font-semibold">Mã NV</th>
                      <th className="p-3.5 font-semibold">Phòng ban</th>
                      <th className="p-3.5 font-semibold">Chức danh</th>
                      <th className="p-3.5 font-semibold">Vai trò</th>
                      <th className="p-3.5 font-semibold">Trạng thái</th>
                      <th className="p-3.5 font-semibold">Đăng nhập cuối</th>
                      <th className="p-3.5 font-semibold text-right">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {users.map((u) => {
                      const rCode = typeof u.role === 'string' ? u.role : u.role?.code;
                      const dept = typeof u.department === 'string' ? u.department : u.department?.name;
                      const isSelected = selectedUserIds.includes(u.id);

                      return (
                        <tr
                          key={u.id}
                          className={`hover:bg-slate-800/40 transition-colors ${
                            isSelected ? 'bg-indigo-950/15' : ''
                          }`}
                        >
                          <td className="p-3.5 text-center">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSelectUser(u.id)}
                              className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                            />
                          </td>
                          <td className="p-3.5">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-indigo-400 shrink-0">
                                {u.full_name ? u.full_name.charAt(0).toUpperCase() : 'U'}
                              </div>
                              <div className="min-w-0">
                                <div className="font-semibold text-white truncate max-w-[160px] flex items-center gap-1.5">
                                  <span>{u.full_name}</span>
                                  {u.id === currentUser?.id && (
                                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-mono">Tôi</span>
                                  )}
                                </div>
                                <div className="text-[11px] text-slate-400 truncate max-w-[180px]">
                                  {u.username} • {u.email}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="p-3.5 font-mono text-[11px] text-slate-300">
                            {u.employee_code || '-'}
                          </td>
                          <td className="p-3.5">
                            <span className="inline-flex items-center gap-1 text-[11px] text-slate-300 bg-slate-800/50 px-2 py-0.5 rounded-lg border border-slate-700/50">
                              <Building2 className="w-3 h-3 text-slate-500" />
                              <span className="truncate max-w-[130px]">{dept || 'Toàn cty'}</span>
                            </span>
                          </td>
                          <td className="p-3.5 text-[11px] text-slate-300">
                            {u.position || 'Nhân viên'}
                          </td>
                          <td className="p-3.5">
                            {getRoleBadge(rCode)}
                          </td>
                          <td className="p-3.5">
                            {getStatusBadge(u.status)}
                          </td>
                          <td className="p-3.5 text-[11px] text-slate-400">
                            {u.last_login_at
                              ? new Date(u.last_login_at).toLocaleDateString('vi-VN', { hour: '2-digit', minute: '2-digit' })
                              : 'Chưa có'}
                          </td>
                          <td className="p-3.5 text-right">
                            <div className="flex items-center justify-end gap-1">
                              {/* View Details */}
                              <button
                                onClick={() => openDetailModal(u)}
                                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
                                title="Xem chi tiết"
                              >
                                <Eye className="w-3.5 h-3.5" />
                              </button>

                              {/* Edit */}
                              <button
                                onClick={() => openEditModal(u)}
                                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-indigo-400 transition-all"
                                title="Chỉnh sửa tài khoản"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>

                              {/* Lock / Unlock */}
                              <button
                                onClick={() => handleToggleLock(u)}
                                className={`p-1.5 rounded-lg hover:bg-slate-800 transition-all ${
                                  u.status === 'LOCKED'
                                    ? 'text-emerald-400 hover:text-emerald-300'
                                    : 'text-slate-400 hover:text-rose-400'
                                }`}
                                title={u.status === 'LOCKED' ? 'Mở khóa tài khoản' : 'Khóa tài khoản'}
                              >
                                {u.status === 'LOCKED' ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
                              </button>

                              {/* Reset Password */}
                              <button
                                onClick={() => openResetModal(u)}
                                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-amber-400 transition-all"
                                title="Đặt lại mật khẩu"
                              >
                                <KeyRound className="w-3.5 h-3.5" />
                              </button>

                              {/* Soft Delete */}
                              {u.id !== currentUser?.id && (
                                <button
                                  onClick={() => handleDeleteUser(u)}
                                  className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-all"
                                  title="Vô hiệu hóa"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SUB-TAB 2: DEPARTMENTS OVERVIEW & MANAGEMENT */}
      {/* ========================================================= */}
      {activeSubTab === 'departments' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-md">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Building2 className="w-4 h-4 text-cyan-400" />
                Cơ cấu Tổ chức & Phòng ban Doanh nghiệp ({departments.length})
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Quản lý các phòng ban chức năng và cô lập phạm vi truy xuất tài liệu RAG
              </p>
            </div>
            {(isSuperAdmin || isITAdmin) && (
              <button
                onClick={openAddDeptModal}
                className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all cursor-pointer shrink-0"
              >
                <Plus className="w-4 h-4" />
                <span>Thêm Phòng ban mới</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {departments.map((dept) => {
              const deptUsers = users.filter((u) => u.department_id === dept.id);
              const isIT = dept.code === 'IT' || dept.code.startsWith('IT_');

              return (
                <div
                  key={dept.id}
                  className={`p-5 rounded-2xl border transition-all relative group ${
                    isIT
                      ? 'bg-cyan-950/20 border-cyan-800/40 hover:border-cyan-500/60'
                      : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white text-sm flex items-center gap-2">
                      <Building2 className={`w-4 h-4 ${isIT ? 'text-cyan-400' : 'text-indigo-400'}`} />
                      {dept.name}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                        {dept.code}
                      </span>
                      {(isSuperAdmin || isITAdmin) && (
                        <div className="flex items-center gap-0.5 opacity-80 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => openEditDeptModal(dept)}
                            title="Sửa phòng ban"
                            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteDept(dept)}
                            title="Xóa phòng ban"
                            className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 mb-4 line-clamp-2 leading-relaxed">
                    {dept.description || 'Chưa có mô tả chi tiết nhiệm vụ phòng ban.'}
                  </p>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Nhân sự trực thuộc:</span>
                    <span className="font-bold text-white px-2.5 py-0.5 rounded-full bg-slate-800 text-[11px]">
                      {deptUsers.length} thành viên
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SUB-TAB 3: ROLES & PERMISSIONS MATRIX */}
      {/* ========================================================= */}
      {activeSubTab === 'roles' && (
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-900/90 border border-slate-800 overflow-hidden shadow-xl p-5 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-indigo-400" />
                Ma trận Quyền hạn RBAC (Role-Based Access Control)
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Các quyền hạn được gắn với từng vai trò người dùng trong hệ sinh thái Local AI Nội bộ doanh nghiệp
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="p-3 font-semibold min-w-[200px]">Tính năng / Thẩm quyền</th>
                    <th className="p-3 font-semibold text-center">Super Admin</th>
                    <th className="p-3 font-semibold text-center">Admin</th>
                    <th className="p-3 font-semibold text-center">IT Admin</th>
                    <th className="p-3 font-semibold text-center">IT Manager</th>
                    <th className="p-3 font-semibold text-center">Trưởng phòng</th>
                    <th className="p-3 font-semibold text-center">Nhân viên</th>
                    <th className="p-3 font-semibold text-center">Người xem</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {[
                    { label: 'Xem danh sách người dùng (USER_VIEW)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER', 'DEPARTMENT_MANAGER'] },
                    { label: 'Thêm mới tài khoản (USER_CREATE)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER', 'DEPARTMENT_MANAGER'] },
                    { label: 'Chỉnh sửa tài khoản (USER_UPDATE)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER', 'DEPARTMENT_MANAGER'] },
                    { label: 'Khóa / Mở khóa người dùng (USER_LOCK)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER'] },
                    { label: 'Reset mật khẩu nhân viên (USER_RESET_PW)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER'] },
                    { label: 'Vô hiệu hóa / Xóa người dùng (USER_DELETE)', roles: ['SUPER_ADMIN', 'ADMIN'] },
                    { label: 'Thay đổi vai trò RBAC (USER_CHANGE_ROLE)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN'] },
                    { label: 'Điều chuyển phòng ban (USER_CHANGE_DEPT)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN'] },
                    { label: 'Xem & Tra cứu tài liệu (DOCUMENT_VIEW)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER', 'DEPARTMENT_MANAGER', 'EMPLOYEE', 'VIEWER'] },
                    { label: 'Upload tài liệu vào RAG (DOCUMENT_CREATE)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER', 'DEPARTMENT_MANAGER'] },
                    { label: 'Phân quyền tài liệu chéo phòng ban', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'DEPARTMENT_MANAGER'] },
                    { label: 'Tra cứu hỏi đáp AI (RAG_QUERY)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER', 'DEPARTMENT_MANAGER', 'EMPLOYEE', 'VIEWER'] },
                    { label: 'Xem nhật ký quản trị (AUDIT_VIEW)', roles: ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER'] },
                    { label: 'Quản trị hệ thống cấp cao (SYSTEM_SETTINGS)', roles: ['SUPER_ADMIN'] },
                  ].map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="p-3 font-medium text-white">{row.label}</td>
                      {['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER', 'DEPARTMENT_MANAGER', 'EMPLOYEE', 'VIEWER'].map((r) => (
                        <td key={r} className="p-3 text-center">
                          {row.roles.includes(r) ? (
                            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-[11px]">✓</span>
                          ) : (
                            <span className="text-slate-600">✗</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Dynamic System Permissions Catalog */}
            <div className="pt-5 border-t border-slate-800">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-indigo-400" />
                  Danh mục Quyền hạn Hệ thống ({permissions.length})
                </h4>
                <span className="text-[11px] text-slate-500">Được tải tự động từ cơ sở dữ liệu RBAC</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {permissions.map((p) => (
                  <div key={p.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono font-bold text-indigo-400 text-[11px] bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        {p.code}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                        {p.category || 'SYSTEM'}
                      </span>
                    </div>
                    <p className="text-slate-200 font-medium text-xs mt-1.5">{p.name}</p>
                    {p.description && (
                      <p className="text-slate-500 text-[11px] mt-0.5 leading-relaxed">{p.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SUB-TAB 4: AUDIT LOG */}
      {/* ========================================================= */}
      {activeSubTab === 'audit' && (
        <div className="rounded-2xl bg-slate-900/90 border border-slate-800 overflow-hidden shadow-xl p-5 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Nhật ký Vận hành & Thay đổi Tài khoản (Audit Trail)
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Ghi nhận toàn bộ thao tác khởi tạo, khóa, mở khóa, đổi quyền và cấp lại mật khẩu
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                <tr>
                  <th className="p-3 font-semibold">Thời gian</th>
                  <th className="p-3 font-semibold">Hành động</th>
                  <th className="p-3 font-semibold">Tài nguyên</th>
                  <th className="p-3 font-semibold">Kết quả</th>
                  <th className="p-3 font-semibold">Chi tiết</th>
                  <th className="p-3 font-semibold">Địa chỉ IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-slate-500">
                      Chưa có nhật ký hoạt động gần đây.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/30">
                      <td className="p-3 font-mono text-slate-400">
                        {new Date(log.created_at).toLocaleString('vi-VN')}
                      </td>
                      <td className="p-3 font-semibold text-indigo-400">{log.action}</td>
                      <td className="p-3 text-slate-300">{log.resource}</td>
                      <td className="p-3">
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          {log.result}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-[11px] text-slate-400 max-w-xs truncate">
                        {JSON.stringify(log.details)}
                      </td>
                      <td className="p-3 font-mono text-slate-500">{log.ip_address || '127.0.0.1'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL: ADD USER */}
      {/* ========================================================= */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-indigo-400" />
                Thêm mới Tài khoản Nhân viên
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="p-6 space-y-3.5 overflow-y-auto flex-1">
              {addError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{addError}</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Họ và tên *</label>
                  <input
                    type="text"
                    value={addForm.fullName}
                    onChange={(e) => setAddForm({ ...addForm, fullName: e.target.value })}
                    required
                    placeholder="Nguyễn Văn A"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Mã nhân viên</label>
                  <input
                    type="text"
                    value={addForm.employeeCode}
                    onChange={(e) => setAddForm({ ...addForm, employeeCode: e.target.value })}
                    placeholder="NV-IT01"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Tên đăng nhập *</label>
                  <input
                    type="text"
                    value={addForm.username}
                    onChange={(e) => setAddForm({ ...addForm, username: e.target.value })}
                    required
                    placeholder="nguyenvana"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Email doanh nghiệp *</label>
                  <input
                    type="email"
                    value={addForm.email}
                    onChange={(e) => setAddForm({ ...addForm, email: e.target.value })}
                    required
                    placeholder="a.nguyen@enterprise.local"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Số điện thoại</label>
                  <input
                    type="text"
                    value={addForm.phone}
                    onChange={(e) => setAddForm({ ...addForm, phone: e.target.value })}
                    placeholder="0901234567"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Chức danh công việc</label>
                  <input
                    type="text"
                    value={addForm.position}
                    onChange={(e) => setAddForm({ ...addForm, position: e.target.value })}
                    placeholder="Kỹ sư IT HelpDesk"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-slate-300">Phòng ban *</label>
                    {(isSuperAdmin || isITAdmin) && (
                      <button
                        type="button"
                        onClick={openAddDeptModal}
                        className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-0.5 cursor-pointer"
                      >
                        <Plus className="w-3 h-3" /> Thêm phòng ban
                      </button>
                    )}
                  </div>
                  <select
                    value={addForm.departmentId}
                    onChange={(e) => setAddForm({ ...addForm, departmentId: e.target.value })}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Chọn phòng ban ({departments.length})...</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.code})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Vai trò (Role) *</label>
                  <select
                    value={addForm.roleCode}
                    onChange={(e) => setAddForm({ ...addForm, roleCode: e.target.value })}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  >
                    {roles.map((r) => (
                      <option key={r.code} value={r.code}>
                        {r.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Mật khẩu ban đầu *</label>
                  <input
                    type="password"
                    value={addForm.password}
                    onChange={(e) => setAddForm({ ...addForm, password: e.target.value })}
                    required
                    placeholder="••••••••"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Xác nhận mật khẩu *</label>
                  <input
                    type="password"
                    value={addForm.confirmPassword}
                    onChange={(e) => setAddForm({ ...addForm, confirmPassword: e.target.value })}
                    required
                    placeholder="••••••••"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={addLoading}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                >
                  {addLoading ? 'Đang tạo...' : 'Tạo tài khoản'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL: EDIT USER */}
      {/* ========================================================= */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-indigo-400" />
                Chỉnh sửa Tài khoản: {selectedUser.username}
              </h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateUser} className="p-6 space-y-3.5 overflow-y-auto flex-1">
              {editError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{editError}</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Họ và tên *</label>
                  <input
                    type="text"
                    value={editForm.fullName}
                    onChange={(e) => setEditForm({ ...editForm, fullName: e.target.value })}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Mã nhân viên</label>
                  <input
                    type="text"
                    value={editForm.employeeCode}
                    onChange={(e) => setEditForm({ ...editForm, employeeCode: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Số điện thoại</label>
                  <input
                    type="text"
                    value={editForm.phone}
                    onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Chức danh</label>
                  <input
                    type="text"
                    value={editForm.position}
                    onChange={(e) => setEditForm({ ...editForm, position: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-slate-300">Phòng ban</label>
                    {(isSuperAdmin || isITAdmin) && (
                      <button
                        type="button"
                        onClick={openAddDeptModal}
                        className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-0.5 cursor-pointer"
                      >
                        <Plus className="w-3 h-3" /> Thêm phòng ban
                      </button>
                    )}
                  </div>
                  <select
                    value={editForm.departmentId}
                    onChange={(e) => setEditForm({ ...editForm, departmentId: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Chọn phòng ban ({departments.length})...</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.code})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Vai trò (Role)</label>
                  <select
                    value={editForm.roleCode}
                    onChange={(e) => setEditForm({ ...editForm, roleCode: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                  >
                    {roles.map((r) => (
                      <option key={r.code} value={r.code}>
                        {r.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Trạng thái tài khoản</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="ACTIVE">Hoạt động (ACTIVE)</option>
                  <option value="LOCKED">Khóa tài khoản (LOCKED)</option>
                  <option value="SUSPENDED">Đình chỉ tạm thời (SUSPENDED)</option>
                  <option value="INACTIVE">Vô hiệu hóa (INACTIVE)</option>
                  <option value="PENDING">Chờ kích hoạt (PENDING)</option>
                </select>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={editLoading}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                >
                  {editLoading ? 'Đang lưu...' : 'Lưu thay đổi'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL: RESET PASSWORD */}
      {/* ========================================================= */}
      {showResetModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <KeyRound className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Đặt lại mật khẩu</h3>
                <p className="text-xs text-slate-400">Tài khoản: {selectedUser.username}</p>
              </div>
            </div>

            {!tempPassword ? (
              <>
                <p className="text-xs text-slate-300">
                  Bạn có chắc chắn muốn đặt lại mật khẩu cho tài khoản <strong>{selectedUser.full_name}</strong>?
                </p>
                <p className="text-[11px] text-slate-500">
                  Hệ thống sẽ tạo mật khẩu ngẫu nhiên tạm thời và yêu cầu người dùng đổi mật khẩu ở lần đăng nhập tiếp theo.
                </p>

                <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                  <button
                    onClick={() => setShowResetModal(false)}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                  >
                    Hủy bỏ
                  </button>
                  <button
                    onClick={handleConfirmResetPassword}
                    disabled={resetLoading}
                    className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                  >
                    {resetLoading ? 'Đang sinh mật khẩu...' : 'Xác nhận đặt lại'}
                  </button>
                </div>
              </>
            ) : (
              <div className="space-y-4">
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
                  Đặt lại mật khẩu thành công! Hãy sao chép và gửi mật khẩu tạm thời này cho nhân viên:
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                  <span className="font-mono text-sm font-bold text-cyan-400 tracking-wider">
                    {tempPassword}
                  </span>
                  <button
                    onClick={handleCopyPassword}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 flex items-center gap-1.5 transition-all"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>{copySuccess ? 'Đã chép!' : 'Sao chép'}</span>
                  </button>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => setShowResetModal(false)}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
                  >
                    Hoàn tất
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL: USER DETAIL (OVERVIEW, PERMISSIONS, ACTIVITY) */}
      {/* ========================================================= */}
      {showDetailModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400 font-bold text-sm">
                  {selectedUser.full_name?.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">{selectedUser.full_name}</h3>
                  <p className="text-xs text-slate-400">{selectedUser.username} • {selectedUser.email}</p>
                </div>
              </div>
              <button
                onClick={() => setShowDetailModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Sub-tabs inside Detail Modal */}
            <div className="flex border-b border-slate-800 bg-slate-950/20 px-6 gap-6">
              <button
                onClick={() => setDetailTab('overview')}
                className={`py-3 text-xs font-semibold border-b-2 transition-all ${
                  detailTab === 'overview'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Tổng quan
              </button>
              <button
                onClick={() => setDetailTab('permissions')}
                className={`py-3 text-xs font-semibold border-b-2 transition-all ${
                  detailTab === 'permissions'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Quyền hạn ({detailPermissions.length})
              </button>
              <button
                onClick={() => setDetailTab('activity')}
                className={`py-3 text-xs font-semibold border-b-2 transition-all ${
                  detailTab === 'activity'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Lịch sử hoạt động ({detailActivity.length})
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1">
              {detailLoading ? (
                <div className="p-8 text-center text-slate-400 text-xs">
                  <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  Đang tải thông tin...
                </div>
              ) : detailTab === 'overview' ? (
                <div className="space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                    <div>
                      <span className="text-slate-500 block mb-0.5">Mã nhân viên:</span>
                      <span className="font-semibold text-slate-200 font-mono">{selectedUser.employee_code || 'Chưa gán'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">Chức danh:</span>
                      <span className="font-semibold text-slate-200">{selectedUser.position || 'Nhân viên'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">Phòng ban:</span>
                      <span className="font-semibold text-slate-200">
                        {typeof selectedUser.department === 'string' ? selectedUser.department : selectedUser.department?.name || 'Toàn cty'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">Vai trò RBAC:</span>
                      <span>{getRoleBadge(typeof selectedUser.role === 'string' ? selectedUser.role : selectedUser.role?.code)}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">Số điện thoại:</span>
                      <span className="font-semibold text-slate-200">{selectedUser.phone || 'Chưa cập nhật'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">Trạng thái:</span>
                      <span>{getStatusBadge(selectedUser.status)}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">Đăng nhập lần cuối:</span>
                      <span className="font-semibold text-slate-200">
                        {selectedUser.last_login_at ? new Date(selectedUser.last_login_at).toLocaleString('vi-VN') : 'Chưa có'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">Ngày tạo tài khoản:</span>
                      <span className="font-semibold text-slate-200">
                        {selectedUser.created_at ? new Date(selectedUser.created_at).toLocaleDateString('vi-VN') : '-'}
                      </span>
                    </div>
                  </div>
                </div>
              ) : detailTab === 'permissions' ? (
                <div className="space-y-2">
                  <p className="text-xs text-slate-400 mb-2">Các quyền hạn cấp hệ thống của tài khoản này:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {detailPermissions.map((code) => (
                      <div
                        key={code}
                        className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-xs flex items-center gap-2 text-emerald-300"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span className="font-mono text-[11px] truncate">{code}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {detailActivity.length === 0 ? (
                    <p className="text-xs text-slate-500 text-center py-6">Chưa có nhật ký hoạt động cho tài khoản này.</p>
                  ) : (
                    detailActivity.map((log) => (
                      <div key={log.id} className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-indigo-400">{log.action}</span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {new Date(log.created_at).toLocaleString('vi-VN')}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 font-mono truncate">{JSON.stringify(log.details)}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL: IMPORT CSV */}
      {/* ========================================================= */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
                Nhập danh sách người dùng từ CSV
              </h3>
              <button
                onClick={() => setShowImportModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleImportCSV} className="space-y-4">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 space-y-1.5">
                <p className="font-semibold text-slate-300">Định dạng file CSV yêu cầu các cột:</p>
                <p className="font-mono text-[11px] text-cyan-300">
                  username, email, full_name, employee_code, phone, position, department, role
                </p>
                <p className="text-[10px] text-slate-500">Mật khẩu mặc định được tạo là Employee@123456 (bắt buộc đổi ở lần đăng nhập đầu).</p>
              </div>

              <div>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setImportFile(e.target.files ? e.target.files[0] : null)}
                  required
                  className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500"
                />
              </div>

              {importResult && (
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                  <p className="text-emerald-400 font-semibold">Đã nạp thành công: {importResult.imported}</p>
                  {importResult.errors.length > 0 && (
                    <div className="text-rose-400 max-h-24 overflow-y-auto">
                      {importResult.errors.map((e, i) => (
                        <p key={i} className="text-[11px]">{e}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
                >
                  Đóng
                </button>
                <button
                  type="submit"
                  disabled={!importFile || importLoading}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {importLoading ? 'Đang nạp...' : 'Bắt đầu nạp dữ liệu'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL: ADD / EDIT DEPARTMENT */}
      {/* ========================================================= */}
      {showDeptModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Building2 className="w-4 h-4 text-cyan-400" />
                {editingDept ? `Chỉnh sửa: ${editingDept.name}` : 'Thêm mới Phòng ban Doanh nghiệp'}
              </h3>
              <button
                onClick={() => setShowDeptModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {deptError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{deptError}</span>
              </div>
            )}

            <form onSubmit={handleSaveDepartment} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Mã phòng ban * <span className="text-slate-500 font-normal">(Viết hoa không dấu, ví dụ: RND, MARKETING)</span>
                </label>
                <input
                  type="text"
                  value={deptForm.code}
                  onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value.toUpperCase() })}
                  disabled={!!editingDept}
                  required
                  placeholder="MARKETING"
                  className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs font-mono uppercase focus:outline-none focus:border-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Tên phòng ban *</label>
                <input
                  type="text"
                  value={deptForm.name}
                  onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                  required
                  placeholder="Phòng Tiếp thị & Truyền thông"
                  className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Mô tả chức năng & nhiệm vụ</label>
                <textarea
                  value={deptForm.description}
                  onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })}
                  rows={3}
                  placeholder="Phụ trách truyền thông thương hiệu, tiếp thị đa kênh và quan hệ khách hàng..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div className="pt-2 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowDeptModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={deptLoading}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50 cursor-pointer"
                >
                  {deptLoading ? 'Đang lưu...' : (editingDept ? 'Cập nhật' : 'Tạo phòng ban')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
