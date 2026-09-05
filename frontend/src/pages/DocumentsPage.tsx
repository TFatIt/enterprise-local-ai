import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Upload, 
  Trash2, 
  Search, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  Building2,
  ShieldCheck,
  Lock,
  Globe,
  Users,
  Pencil,
  Eye,
  RefreshCw,
  X,
  Clock,
  Key,
  RotateCcw,
  HelpCircle,
  Download,
  ExternalLink
} from 'lucide-react';
import { api } from '../api/client';
import type { 
  DocumentItem, 
  Department, 
  SecurityLevel, 
  DocumentPermissionItem, 
  DocumentVersionItem, 
  Role 
} from '../types';
import { useAuth } from '../context/AuthContext';

export const DocumentsPage: React.FC = () => {
  const { user, isAdmin, isDeptManager } = useAuth();
  
  // Data States
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Context View Tabs: 'all' | 'my_department'
  const [activeContextTab, setActiveContextTab] = useState<'all' | 'my_department'>('all');

  // Filter Toolbar States
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDeptId, setSelectedDeptId] = useState<number | ''>('');
  const [selectedDocType, setSelectedDocType] = useState<string>('');
  const [selectedSecLevel, setSelectedSecLevel] = useState<string>('');
  const [selectedRagStatus, setSelectedRagStatus] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // Modals
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Active Document for Details / Edit
  const [activeDoc, setActiveDoc] = useState<DocumentItem | null>(null);
  const [detailsTab, setDetailsTab] = useState<'overview' | 'content' | 'metadata' | 'permissions' | 'versions' | 'rag'>('overview');
  
  // Details Sub-data
  const [docChunks, setDocChunks] = useState<any[]>([]);
  const [docPermissions, setDocPermissions] = useState<DocumentPermissionItem[]>([]);
  const [docVersions, setDocVersions] = useState<DocumentVersionItem[]>([]);
  const [loadingDetailsSubdata, setLoadingDetailsSubdata] = useState(false);
  const [downloadingDocId, setDownloadingDocId] = useState<string | null>(null);
  const [chunkDisplayLimit, setChunkDisplayLimit] = useState<number>(20);

  // New Permission Form
  const [newPermUserId, setNewPermUserId] = useState('');
  const [newPermRoleId, setNewPermRoleId] = useState<number | ''>('');
  const [newPermType, setNewPermType] = useState<'VIEW' | 'EDIT' | 'MANAGE'>('VIEW');
  const [submittingPerm, setSubmittingPerm] = useState(false);

  // Upload Form State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDeptId, setUploadDeptId] = useState<number | ''>('');
  const [uploadDocType, setUploadDocType] = useState('POLICY');
  const [uploadCategory, setUploadCategory] = useState('Chung');
  const [uploadSecLevel, setUploadSecLevel] = useState<SecurityLevel>('DEPARTMENT');
  const [uploadVersion, setUploadVersion] = useState('1.0');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Edit Form State
  const [editTitle, setEditTitle] = useState('');
  const [editDeptId, setEditDeptId] = useState<number | ''>('');
  const [editDocType, setEditDocType] = useState('POLICY');
  const [editCategory, setEditCategory] = useState('');
  const [editSecLevel, setEditSecLevel] = useState<SecurityLevel>('DEPARTMENT');
  const [editVersion, setEditVersion] = useState('1.0');
  const [editing, setEditing] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const canUpload = isAdmin || isDeptManager;

  // Load documents from backend with active query params
  const loadDocuments = async (overrideDeptId?: number | '') => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.append('search', searchQuery.trim());

      const deptToUse = overrideDeptId !== undefined ? overrideDeptId : selectedDeptId;
      if (deptToUse !== '') params.append('department_id', deptToUse.toString());
      if (selectedDocType) params.append('document_type', selectedDocType);
      if (selectedSecLevel) params.append('security_level', selectedSecLevel);
      if (selectedRagStatus) params.append('rag_status', selectedRagStatus);
      if (selectedStatus) params.append('status', selectedStatus);

      const resp = await api.get<DocumentItem[]>(`/documents?${params.toString()}`);
      setDocuments(resp.data);
    } catch (err) {
      console.error('Failed to load documents', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDepartmentsAndRoles = async () => {
    try {
      const [deptResp, roleResp] = await Promise.all([
        api.get<Department[]>('/departments'),
        api.get<Role[]>('/departments/roles')
      ]);
      setDepartments(deptResp.data);
      setRoles(roleResp.data);
    } catch (err) {
      console.error('Failed to load departments or roles', err);
    }
  };

  useEffect(() => {
    loadDepartmentsAndRoles();
    loadDocuments();
  }, []);

  // Handle Context Tab Switching (All Documents vs My Department Documents)
  const handleContextTabChange = (tab: 'all' | 'my_department') => {
    setActiveContextTab(tab);
    if (tab === 'my_department') {
      const userDeptId = typeof user?.department === 'object' ? user.department?.id : undefined;
      if (userDeptId) {
        setSelectedDeptId(userDeptId);
        loadDocuments(userDeptId);
      } else {
        loadDocuments();
      }
    } else {
      setSelectedDeptId('');
      loadDocuments('');
    }
  };

  // Reset Filters
  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedDeptId(activeContextTab === 'my_department' && typeof user?.department === 'object' ? (user.department?.id || '') : '');
    setSelectedDocType('');
    setSelectedSecLevel('');
    setSelectedRagStatus('');
    setSelectedStatus('');
    loadDocuments(activeContextTab === 'my_department' && typeof user?.department === 'object' ? user.department?.id : '');
  };

  // Upload Submit
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError('Vui lòng chọn file tài liệu (.pdf, .docx, .txt)');
      return;
    }

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('title', uploadTitle.trim() || uploadFile.name);
    if (uploadDeptId !== '') {
      formData.append('department_id', uploadDeptId.toString());
    }
    formData.append('document_type', uploadDocType);
    formData.append('category', uploadCategory);
    formData.append('security_level', uploadSecLevel);
    formData.append('version', uploadVersion);

    try {
      await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadTitle('');
      setUploadDeptId('');
      setUploadDocType('POLICY');
      setUploadCategory('Chung');
      setUploadSecLevel('DEPARTMENT');
      setUploadVersion('1.0');
      loadDocuments();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Nạp tài liệu thất bại.');
    } finally {
      setUploading(false);
    }
  };

  // Delete Document
  const handleDeleteDocument = async (docId: string, title: string) => {
    if (!confirm(`Bạn có chắc muốn xóa vĩnh viễn tài liệu "${title}" và toàn bộ vector liên quan trong ChromaDB?`)) {
      return;
    }

    try {
      await api.delete(`/documents/${docId}`);
      setDocuments(documents.filter((d) => d.id !== docId));
      if (activeDoc?.id === docId) setShowDetailsModal(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Xóa tài liệu thất bại.');
    }
  };

  // Download or Preview raw document file directly
  const handleDownloadFile = async (doc: DocumentItem, inline: boolean = false) => {
    try {
      setDownloadingDocId(doc.id);
      const response = await api.get(`/documents/${doc.id}/file?download=${!inline}`, {
        responseType: 'blob',
      });
      
      const mimeType = (response.headers['content-type'] as string) || 'application/octet-stream';
      const blob = new Blob([response.data], { type: mimeType });
      const fileUrl = window.URL.createObjectURL(blob);

      if (inline) {
        // Open directly in a new browser tab for fast viewing without waiting for chunks/web RAG loading
        window.open(fileUrl, '_blank');
      } else {
        // Trigger browser download
        const link = document.createElement('a');
        link.href = fileUrl;
        link.setAttribute('download', doc.file_name || `${doc.title}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      }

      // Cleanup object URL after 60s
      setTimeout(() => {
        window.URL.revokeObjectURL(fileUrl);
      }, 60000);
    } catch (err: any) {
      console.error('File download/preview failed:', err);
      alert(err.response?.data?.detail || 'Không thể tải hoặc mở tệp tin. Vui lòng kiểm tra quyền hạn.');
    } finally {
      setDownloadingDocId(null);
    }
  };

  // Open Details Modal and fetch sub-data
  const handleOpenDetails = async (doc: DocumentItem, initialTab: 'overview' | 'content' | 'metadata' | 'permissions' | 'versions' | 'rag' = 'overview') => {
    setActiveDoc(doc);
    setDetailsTab(initialTab);
    setChunkDisplayLimit(20);
    setShowDetailsModal(true);
    loadDetailsSubdata(doc.id, initialTab);
  };

  const loadDetailsSubdata = async (docId: string, tab: string) => {
    setLoadingDetailsSubdata(true);
    try {
      if (tab === 'content') {
        const resp = await api.get(`/documents/${docId}/chunks`);
        setDocChunks(resp.data);
      } else if (tab === 'permissions') {
        const resp = await api.get<DocumentPermissionItem[]>(`/documents/${docId}/permissions`);
        setDocPermissions(resp.data);
      } else if (tab === 'versions') {
        const resp = await api.get<DocumentVersionItem[]>(`/documents/${docId}/versions`);
        setDocVersions(resp.data);
      }
    } catch (err) {
      console.error('Failed to load subdata for doc', err);
    } finally {
      setLoadingDetailsSubdata(false);
    }
  };

  const handleSwitchDetailsTab = (tab: 'overview' | 'content' | 'metadata' | 'permissions' | 'versions' | 'rag') => {
    setDetailsTab(tab);
    setChunkDisplayLimit(20);
    if (activeDoc) {
      loadDetailsSubdata(activeDoc.id, tab);
    }
  };

  // Open Edit Modal
  const handleOpenEdit = (doc: DocumentItem) => {
    setActiveDoc(doc);
    setEditTitle(doc.title);
    setEditDeptId(doc.department_id ?? '');
    setEditDocType(doc.document_type || 'POLICY');
    setEditCategory(doc.category || 'Chung');
    setEditSecLevel((doc.security_level as SecurityLevel) || 'DEPARTMENT');
    setEditVersion(doc.version || '1.0');
    setEditError(null);
    setShowEditModal(true);
  };

  // Edit Submit
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeDoc) return;

    setEditing(true);
    setEditError(null);

    try {
      const resp = await api.put<DocumentItem>(`/documents/${activeDoc.id}`, {
        title: editTitle,
        department_id: editDeptId === '' ? null : editDeptId,
        document_type: editDocType,
        category: editCategory,
        security_level: editSecLevel,
        version: editVersion,
      });
      setShowEditModal(false);
      setDocuments(documents.map((d) => (d.id === activeDoc.id ? resp.data : d)));
      setActiveDoc(resp.data);
    } catch (err: any) {
      setEditError(err.response?.data?.detail || 'Cập nhật thất bại.');
    } finally {
      setEditing(false);
    }
  };

  // Re-index Document
  const handleReindexDocument = async (docId: string) => {
    try {
      const resp = await api.post<DocumentItem>(`/documents/${docId}/reindex`);
      alert('Tái lập chỉ mục ChromaDB thành công!');
      setDocuments(documents.map((d) => (d.id === docId ? resp.data : d)));
      if (activeDoc?.id === docId) setActiveDoc(resp.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Tái lập chỉ mục thất bại.');
    }
  };

  // Add Permission
  const handleAddPermission = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeDoc) return;
    if (!newPermUserId.trim() && newPermRoleId === '') {
      alert('Vui lòng nhập User ID hoặc chọn Role để cấp quyền.');
      return;
    }

    setSubmittingPerm(true);
    try {
      const payload: any = { permission_type: newPermType };
      if (newPermUserId.trim()) payload.user_id = newPermUserId.trim();
      if (newPermRoleId !== '') payload.role_id = Number(newPermRoleId);

      const resp = await api.post<DocumentPermissionItem>(`/documents/${activeDoc.id}/permissions`, payload);
      setDocPermissions([resp.data, ...docPermissions]);
      setNewPermUserId('');
      setNewPermRoleId('');
      alert('Cấp quyền thành công!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Cấp quyền thất bại.');
    } finally {
      setSubmittingPerm(false);
    }
  };

  // Revoke Permission
  const handleRevokePermission = async (permissionId: string) => {
    if (!activeDoc || !confirm('Bạn có chắc muốn thu hồi quyền này?')) return;
    try {
      await api.delete(`/documents/${activeDoc.id}/permissions/${permissionId}`);
      setDocPermissions(docPermissions.filter((p) => p.id !== permissionId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Thu hồi quyền thất bại.');
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes || isNaN(bytes) || bytes <= 0) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getSecurityBadge = (level?: string) => {
    switch (level) {
      case 'PUBLIC':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
            <Globe className="w-3 h-3" />
            <span>PUBLIC</span>
          </span>
        );
      case 'INTERNAL':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/30">
            <Users className="w-3 h-3" />
            <span>INTERNAL</span>
          </span>
        );
      case 'DEPARTMENT':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/30">
            <Building2 className="w-3 h-3" />
            <span>DEPARTMENT</span>
          </span>
        );
      case 'CONFIDENTIAL':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/30">
            <Lock className="w-3 h-3" />
            <span>CONFIDENTIAL</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-700/40 text-slate-300 border border-slate-600/40">
            <span>{level || 'DEPARTMENT'}</span>
          </span>
        );
    }
  };

  const getRagStatusBadge = (status?: string) => {
    switch (status) {
      case 'READY':
        return (
          <span className="inline-flex items-center gap-1 text-emerald-400 font-medium text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>ChromaDB Ready</span>
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1 text-amber-400 font-medium text-[11px]">
            <Clock className="w-3.5 h-3.5 animate-spin" />
            <span>Đang xử lý</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 text-rose-400 font-medium text-[11px]">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Lỗi Index</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-slate-400 font-medium text-[11px]">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Chưa index</span>
          </span>
        );
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Context View Switcher */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-indigo-400" />
            <span>Kho Tri thức Doanh nghiệp & Phân quyền Tài liệu</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Quản lý tài liệu theo thẩm quyền phòng ban, bảo mật vector ChromaDB và kiểm soát truy cập phân tầng (EDAC).
          </p>
        </div>

        {/* Action Button */}
        {canUpload ? (
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/25 transition-all"
          >
            <Upload className="w-4 h-4" />
            <span>Nạp tài liệu mới (.pdf, .docx, .txt)</span>
          </button>
        ) : (
          <span className="text-xs text-slate-500 italic">Quyền xem theo thẩm quyền tài khoản</span>
        )}
      </div>

      {/* Context Navigation Tabs (All vs My Department) */}
      <div className="flex items-center gap-2 border-b border-slate-800/80 pb-2">
        <button
          onClick={() => handleContextTabChange('all')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
            activeContextTab === 'all'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
          }`}
        >
          <Globe className="w-4 h-4" />
          <span>Tất cả tài liệu được phép ({documents.length})</span>
        </button>

        <button
          onClick={() => handleContextTabChange('my_department')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
            activeContextTab === 'my_department'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
          }`}
        >
          <Building2 className="w-4 h-4" />
          <span>
            Tài liệu phòng ban tôi ({typeof user?.department === 'object' ? user.department?.name : 'Phòng ban'})
          </span>
        </button>
      </div>

      {/* Multi-Dimensional Filter Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800/80 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-2.5">
          {/* Search query input */}
          <div className="relative sm:col-span-2">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadDocuments()}
              placeholder="Tìm kiếm tài liệu nội bộ..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-indigo-500 transition-all placeholder:text-slate-500"
            />
          </div>

          {/* Department filter */}
          <div>
            <select
              value={selectedDeptId}
              onChange={(e) => setSelectedDeptId(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-indigo-500"
            >
              <option value="">Phòng ban: Tất cả</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          {/* Document Type filter */}
          <div>
            <select
              value={selectedDocType}
              onChange={(e) => setSelectedDocType(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-indigo-500"
            >
              <option value="">Loại: Tất cả</option>
              <option value="SOP">Quy trình (SOP)</option>
              <option value="POLICY">Chính sách (Policy)</option>
              <option value="PROCEDURE">Thủ tục (Procedure)</option>
              <option value="GUIDE">Hướng dẫn (Guide)</option>
              <option value="MANUAL">Sổ tay (Manual)</option>
              <option value="REPORT">Báo cáo (Report)</option>
              <option value="FORM">Biểu mẫu (Form)</option>
            </select>
          </div>

          {/* Security Level filter */}
          <div>
            <select
              value={selectedSecLevel}
              onChange={(e) => setSelectedSecLevel(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-indigo-500"
            >
              <option value="">Bảo mật: Tất cả</option>
              <option value="PUBLIC">PUBLIC (Công khai)</option>
              <option value="INTERNAL">INTERNAL (Nội bộ)</option>
              <option value="DEPARTMENT">DEPARTMENT (Phòng ban)</option>
              <option value="CONFIDENTIAL">CONFIDENTIAL (Tuyệt mật)</option>
            </select>
          </div>

          {/* RAG Status filter */}
          <div>
            <select
              value={selectedRagStatus}
              onChange={(e) => setSelectedRagStatus(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-indigo-500"
            >
              <option value="">RAG Status: Tất cả</option>
              <option value="READY">ChromaDB Ready</option>
              <option value="PROCESSING">Đang xử lý</option>
              <option value="FAILED">Lỗi Index</option>
            </select>
          </div>
        </div>

        {/* Buttons: Search & Reset */}
        <div className="flex items-center justify-between pt-1 text-xs">
          <span className="text-slate-500 text-[11px]">
            Đang hiển thị {documents.length} tài liệu phù hợp
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleResetFilters}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5 transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Làm mới</span>
            </button>
            <button
              onClick={() => loadDocuments()}
              className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium flex items-center gap-1.5 transition-all shadow-md shadow-indigo-600/20"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Tìm kiếm</span>
            </button>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-5 py-3.5">Tên tài liệu & File</th>
                <th className="px-5 py-3.5">Phòng ban</th>
                <th className="px-5 py-3.5">Loại</th>
                <th className="px-5 py-3.5">Bảo mật</th>
                <th className="px-5 py-3.5">Dung lượng</th>
                <th className="px-5 py-3.5">Chunks</th>
                <th className="px-5 py-3.5">Trạng thái RAG</th>
                <th className="px-5 py-3.5">Version</th>
                <th className="px-5 py-3.5">Cập nhật</th>
                <th className="px-5 py-3.5">Owner</th>
                <th className="px-5 py-3.5 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {documents.map((doc) => (
                <tr 
                  key={doc.id} 
                  className="hover:bg-slate-800/40 transition-all cursor-pointer group"
                  onClick={() => handleOpenDetails(doc, 'overview')}
                >
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="max-w-[220px]">
                        <div className="font-semibold text-white truncate group-hover:text-indigo-300 transition-colors" title={doc.title}>
                          {doc.title}
                        </div>
                        <div className="text-[11px] text-slate-400 truncate" title={doc.file_name}>
                          {doc.file_name}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="px-5 py-4 text-slate-300">
                    <div className="flex items-center gap-1.5">
                      <Building2 className="w-3.5 h-3.5 text-slate-500" />
                      <span className="truncate max-w-[140px]" title={doc.department_name || 'Chung toàn công ty'}>
                        {doc.department_name || 'Chung toàn công ty'}
                      </span>
                    </div>
                  </td>

                  <td className="px-5 py-4">
                    <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 text-[10px] font-semibold uppercase tracking-wider border border-slate-700">
                      {doc.document_type || 'POLICY'}
                    </span>
                  </td>

                  <td className="px-5 py-4">
                    {getSecurityBadge(doc.security_level)}
                  </td>

                  <td className="px-5 py-4 text-slate-400 font-mono text-[11px]">
                    {formatFileSize(doc.file_size ?? doc.file_size_bytes)}
                  </td>

                  <td className="px-5 py-4">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 font-medium">
                      <Layers className="w-3 h-3" />
                      <span>{doc.total_chunks ?? doc.chunk_count ?? 0}</span>
                    </span>
                  </td>

                  <td className="px-5 py-4">
                    {getRagStatusBadge(doc.rag_status)}
                  </td>

                  <td className="px-5 py-4 font-mono text-[11px] text-slate-300">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60">
                      v{doc.version || '1.0'}
                    </span>
                  </td>

                  <td className="px-5 py-4 text-slate-400 text-[11px]">
                    {new Date(doc.created_at).toLocaleDateString('vi-VN')}
                  </td>

                  <td className="px-5 py-4 text-slate-300 text-[11px]">
                    <span className="truncate max-w-[100px] block" title={doc.owner_name || doc.uploader_name || 'Hệ thống'}>
                      {doc.owner_name || doc.uploader_name || 'Hệ thống'}
                    </span>
                  </td>

                  <td className="px-5 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1">
                      {/* Direct Preview (Instant) */}
                      <button
                        onClick={() => handleDownloadFile(doc, true)}
                        disabled={downloadingDocId === doc.id}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all disabled:opacity-50"
                        title="Mở đọc trực tiếp tệp gốc (Nhanh)"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>

                      {/* Direct Download */}
                      <button
                        onClick={() => handleDownloadFile(doc, false)}
                        disabled={downloadingDocId === doc.id}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-all disabled:opacity-50"
                        title="Tải tệp tin gốc về máy"
                      >
                        <Download className="w-4 h-4" />
                      </button>

                      {/* View details */}
                      <button
                        onClick={() => handleOpenDetails(doc, 'overview')}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-indigo-500/10 transition-all"
                        title="Xem chi tiết"
                      >
                        <Eye className="w-4 h-4" />
                      </button>

                      {/* Edit metadata */}
                      {doc.can_edit && (
                        <button
                          onClick={() => handleOpenEdit(doc)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-all"
                          title="Chỉnh sửa thông tin"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                      )}

                      {/* Granular permissions */}
                      {doc.can_manage_permissions && (
                        <button
                          onClick={() => handleOpenDetails(doc, 'permissions')}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-amber-300 hover:bg-amber-500/10 transition-all"
                          title="Phân quyền tài liệu"
                        >
                          <Key className="w-4 h-4" />
                        </button>
                      )}

                      {/* Re-index (Admin only) */}
                      {isAdmin && (
                        <button
                          onClick={() => handleReindexDocument(doc.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-300 hover:bg-emerald-500/10 transition-all"
                          title="Tái lập chỉ mục ChromaDB"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}

                      {/* Delete */}
                      {doc.can_delete && (
                        <button
                          onClick={() => handleDeleteDocument(doc.id, doc.title)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
                          title="Xóa tài liệu"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}

              {documents.length === 0 && (
                <tr>
                  <td colSpan={11} className="px-5 py-12 text-center text-slate-500 text-xs">
                    {loading ? 'Đang tải danh sách tài liệu...' : 'Không tìm thấy tài liệu nào phù hợp với thẩm quyền của bạn.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Document Details Modal (6 Tabs) */}
      {showDetailsModal && activeDoc && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-panel w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl border border-slate-700 shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 gap-4">
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-base font-bold text-white truncate max-w-lg">{activeDoc.title}</h3>
                  {getSecurityBadge(activeDoc.security_level)}
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    v{activeDoc.version || '1.0'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 truncate">{activeDoc.file_name} • {activeDoc.department_name || 'Toàn doanh nghiệp'}</p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handleDownloadFile(activeDoc, true)}
                  disabled={downloadingDocId === activeDoc.id}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/25 text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
                  title="Mở xem trực tiếp trên tab mới của trình duyệt (Cực nhanh)"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Mở xem trực tiếp</span>
                </button>
                <button
                  onClick={() => handleDownloadFile(activeDoc, false)}
                  disabled={downloadingDocId === activeDoc.id}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/25 text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
                  title="Tải tệp tin gốc về máy"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Tải về</span>
                </button>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-slate-400 hover:text-white p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition-all ml-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* 6 Tabs Header */}
            <div className="flex border-b border-slate-800 bg-slate-900/50 px-5 gap-4 overflow-x-auto text-xs">
              {[
                { key: 'overview', label: 'Tổng quan' },
                { key: 'content', label: `Trích xuất (${activeDoc.total_chunks || 0} chunks)` },
                { key: 'metadata', label: 'Metadata' },
                { key: 'permissions', label: 'Phân quyền' },
                { key: 'versions', label: 'Lịch sử phiên bản' },
                { key: 'rag', label: 'Thông tin RAG' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => handleSwitchDetailsTab(tab.key as any)}
                  className={`py-3 font-semibold border-b-2 transition-all shrink-0 ${
                    detailsTab === tab.key
                      ? 'border-indigo-500 text-indigo-400'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Modal Tab Content */}
            <div className="p-6 overflow-y-auto flex-1 space-y-4">
              {/* TAB 1: OVERVIEW */}
              {detailsTab === 'overview' && (
                <div className="space-y-4">
                  {/* File Download & Direct Open Banner */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-900/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-md">
                    <div>
                      <h4 className="font-semibold text-white text-xs flex items-center gap-2">
                        <FileText className="w-4 h-4 text-indigo-400" />
                        <span>Tệp tin đính kèm: <span className="text-indigo-300 font-mono">{activeDoc.file_name}</span></span>
                      </h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Dung lượng: <span className="text-white font-mono">{formatFileSize(activeDoc.file_size)}</span> • Tải về máy để xem offline hoặc mở trực tiếp trên tab mới cực nhanh không cần chờ đợi.
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleDownloadFile(activeDoc, true)}
                        disabled={downloadingDocId === activeDoc.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all shadow-md disabled:opacity-50"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Mở đọc ngay</span>
                      </button>
                      <button
                        onClick={() => handleDownloadFile(activeDoc, false)}
                        disabled={downloadingDocId === activeDoc.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md disabled:opacity-50"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Tải file gốc</span>
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <span className="text-slate-400">Trạng thái RAG</span>
                      <div>{getRagStatusBadge(activeDoc.rag_status)}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <span className="text-slate-400">Dung lượng tệp</span>
                      <div className="font-semibold text-white">{formatFileSize(activeDoc.file_size)}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <span className="text-slate-400">Số lượng Chunks</span>
                      <div className="font-semibold text-indigo-300">{activeDoc.total_chunks || 0} chunks</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <span className="text-slate-400">Mức bảo mật</span>
                      <div>{getSecurityBadge(activeDoc.security_level)}</div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2 text-xs">
                    <h4 className="font-semibold text-white">Tóm tắt phân quyền truy cập</h4>
                    <p className="text-slate-300">
                      Tài liệu này được phân loại là <span className="font-bold text-indigo-400">{activeDoc.security_level}</span>.
                      {activeDoc.security_level === 'PUBLIC' && ' Mọi người dùng trong hệ thống đều có thể xem và tra cứu.'}
                      {activeDoc.security_level === 'INTERNAL' && ' Toàn bộ nhân viên chính thức trong công ty có thể xem.'}
                      {activeDoc.security_level === 'DEPARTMENT' && ` Chỉ nhân viên thuộc phòng ban ${activeDoc.department_name || 'được chỉ định'} cùng cấp quản lý mới được quyền truy cập.`}
                      {activeDoc.security_level === 'CONFIDENTIAL' && ' Chỉ những nhân viên hoặc vai trò được cấp quyền tường minh trong tab Phân quyền mới có thể truy cập.'}
                    </p>
                  </div>
                </div>
              )}

              {/* TAB 2: CONTENT CHUNKS */}
              {detailsTab === 'content' && (
                <div className="space-y-3">
                  {loadingDetailsSubdata ? (
                    <div className="text-center py-8 text-slate-400 text-xs">Đang tải các đoạn chunks trích xuất...</div>
                  ) : docChunks.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 text-xs">Tài liệu chưa có đoạn chunk nào trong ChromaDB.</div>
                  ) : (
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between text-xs text-slate-400 px-1 pb-1 border-b border-slate-800">
                        <span>Đang hiển thị {Math.min(chunkDisplayLimit, docChunks.length)} / {docChunks.length} chunks</span>
                        <button
                          onClick={() => handleDownloadFile(activeDoc, true)}
                          className="text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1 text-[11px] font-medium"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>Mở đọc trực tiếp file gốc</span>
                        </button>
                      </div>

                      {docChunks.slice(0, chunkDisplayLimit).map((c) => (
                        <div key={c.id} className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                          <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-800 pb-1">
                            <span className="font-mono text-indigo-400">Chunk #{c.chunk_index + 1}</span>
                            <span>{c.chroma_id}</span>
                          </div>
                          <p className="text-xs text-slate-200 leading-relaxed font-mono whitespace-pre-wrap">
                            {c.content}
                          </p>
                        </div>
                      ))}

                      {docChunks.length > chunkDisplayLimit && (
                        <div className="text-center pt-3 flex items-center justify-center gap-3">
                          <button
                            onClick={() => setChunkDisplayLimit((prev) => prev + 25)}
                            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 text-xs font-semibold transition-all shadow-sm"
                          >
                            Hiển thị thêm 25 chunks (còn lại {docChunks.length - chunkDisplayLimit})
                          </button>
                          <button
                            onClick={() => setChunkDisplayLimit(docChunks.length)}
                            className="px-3 py-2 rounded-xl bg-slate-800/60 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 text-xs transition-all"
                          >
                            Hiển thị tất cả ({docChunks.length})
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: METADATA TABLE */}
              {detailsTab === 'metadata' && (
                <div className="border border-slate-800 rounded-xl overflow-hidden text-xs">
                  <table className="w-full text-left">
                    <tbody className="divide-y divide-slate-800">
                      <tr>
                        <td className="px-4 py-3 font-semibold text-slate-400 bg-slate-900/60 w-1/3">Mã tài liệu (UUID)</td>
                        <td className="px-4 py-3 font-mono text-indigo-300">{activeDoc.id}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-semibold text-slate-400 bg-slate-900/60">Loại tài liệu</td>
                        <td className="px-4 py-3 text-white">{activeDoc.document_type || 'POLICY'}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-semibold text-slate-400 bg-slate-900/60">Danh mục nghiệp vụ</td>
                        <td className="px-4 py-3 text-white">{activeDoc.category || 'Chung'}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-semibold text-slate-400 bg-slate-900/60">Phòng ban quản lý</td>
                        <td className="px-4 py-3 text-white">{activeDoc.department_name || 'Chung toàn công ty'}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-semibold text-slate-400 bg-slate-900/60">Người sở hữu (Owner)</td>
                        <td className="px-4 py-3 text-white">{activeDoc.owner_name || 'Chưa gán'}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-semibold text-slate-400 bg-slate-900/60">Người nạp (Uploader)</td>
                        <td className="px-4 py-3 text-white">{activeDoc.uploader_name || 'Hệ thống'}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-semibold text-slate-400 bg-slate-900/60">Ngày tạo</td>
                        <td className="px-4 py-3 text-slate-300">{new Date(activeDoc.created_at).toLocaleString('vi-VN')}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-semibold text-slate-400 bg-slate-900/60">Ngày cập nhật</td>
                        <td className="px-4 py-3 text-slate-300">{activeDoc.updated_at ? new Date(activeDoc.updated_at).toLocaleString('vi-VN') : '—'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* TAB 4: PERMISSIONS */}
              {detailsTab === 'permissions' && (
                <div className="space-y-4 text-xs">
                  {activeDoc.can_manage_permissions && (
                    <form onSubmit={handleAddPermission} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                      <h4 className="font-semibold text-white flex items-center gap-1.5">
                        <Key className="w-4 h-4 text-amber-400" />
                        <span>Cấp quyền riêng cho User hoặc Role</span>
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        <div>
                          <label className="block text-slate-400 mb-1 text-[11px]">User ID (UUID)</label>
                          <input
                            type="text"
                            placeholder="Nhập UUID nhân viên..."
                            value={newPermUserId}
                            onChange={(e) => setNewPermUserId(e.target.value)}
                            className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-slate-400 mb-1 text-[11px]">Hoặc Vai trò (Role)</label>
                          <select
                            value={newPermRoleId}
                            onChange={(e) => setNewPermRoleId(e.target.value ? Number(e.target.value) : '')}
                            className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                          >
                            <option value="">Chọn Role...</option>
                            {roles.map((r) => (
                              <option key={r.id} value={r.id}>
                                {r.name} ({r.code})
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-slate-400 mb-1 text-[11px]">Cấp độ quyền</label>
                          <select
                            value={newPermType}
                            onChange={(e) => setNewPermType(e.target.value as any)}
                            className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                          >
                            <option value="VIEW">VIEW (Xem tài liệu)</option>
                            <option value="EDIT">EDIT (Xem & Sửa)</option>
                            <option value="MANAGE">MANAGE (Toàn quyền quản lý)</option>
                          </select>
                        </div>
                      </div>
                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={submittingPerm}
                          className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold shadow-md transition-all"
                        >
                          {submittingPerm ? 'Đang cấp...' : 'Cấp quyền'}
                        </button>
                      </div>
                    </form>
                  )}

                  {/* Permissions list */}
                  <div className="border border-slate-800 rounded-xl overflow-hidden">
                    <table className="w-full text-left">
                      <thead className="bg-slate-900 text-slate-400 text-[11px] font-semibold">
                        <tr>
                          <th className="px-4 py-2.5">Đối tượng</th>
                          <th className="px-4 py-2.5">Loại quyền</th>
                          <th className="px-4 py-2.5">Thời gian cấp</th>
                          {activeDoc.can_manage_permissions && <th className="px-4 py-2.5 text-right">Thao tác</th>}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {docPermissions.map((p) => (
                          <tr key={p.id}>
                            <td className="px-4 py-2.5 text-white">
                              {p.user_name ? (
                                <div>
                                  <span className="font-semibold">{p.user_name}</span>
                                  <span className="text-[10px] text-slate-400 block">{p.user_email}</span>
                                </div>
                              ) : p.role_name ? (
                                <span className="font-semibold text-amber-300">Vai trò: {p.role_name}</span>
                              ) : (
                                <span className="font-mono text-slate-400">{p.user_id || p.role_id}</span>
                              )}
                            </td>
                            <td className="px-4 py-2.5">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300">
                                {p.permission_type}
                              </span>
                            </td>
                            <td className="px-4 py-2.5 text-slate-400">
                              {new Date(p.created_at).toLocaleDateString('vi-VN')}
                            </td>
                            {activeDoc.can_manage_permissions && (
                              <td className="px-4 py-2.5 text-right">
                                <button
                                  onClick={() => handleRevokePermission(p.id)}
                                  className="text-rose-400 hover:text-rose-300 p-1 rounded"
                                  title="Thu hồi quyền"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </td>
                            )}
                          </tr>
                        ))}
                        {docPermissions.length === 0 && (
                          <tr>
                            <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                              Chưa có phân quyền riêng lẻ nào cho tài liệu này (đang áp dụng quyền kế thừa phòng ban).
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 5: VERSION HISTORY */}
              {detailsTab === 'versions' && (
                <div className="space-y-3 text-xs">
                  <div className="border border-slate-800 rounded-xl overflow-hidden">
                    <table className="w-full text-left">
                      <thead className="bg-slate-900 text-slate-400 text-[11px] font-semibold">
                        <tr>
                          <th className="px-4 py-2.5">Phiên bản</th>
                          <th className="px-4 py-2.5">Tệp lưu trữ</th>
                          <th className="px-4 py-2.5">Dung lượng</th>
                          <th className="px-4 py-2.5">Ghi chú thay đổi</th>
                          <th className="px-4 py-2.5">Người cập nhật</th>
                          <th className="px-4 py-2.5">Thời gian</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {docVersions.map((v) => (
                          <tr key={v.id}>
                            <td className="px-4 py-2.5 font-bold font-mono text-indigo-300">v{v.version_number}</td>
                            <td className="px-4 py-2.5 text-slate-300">{v.file_name}</td>
                            <td className="px-4 py-2.5 font-mono text-slate-400">{formatFileSize(v.file_size)}</td>
                            <td className="px-4 py-2.5 text-slate-300">{v.change_notes || '—'}</td>
                            <td className="px-4 py-2.5 text-slate-400">{v.creator_name || 'Hệ thống'}</td>
                            <td className="px-4 py-2.5 text-slate-400">{new Date(v.created_at).toLocaleString('vi-VN')}</td>
                          </tr>
                        ))}
                        {docVersions.length === 0 && (
                          <tr>
                            <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                              Chưa có lịch sử phiên bản nào được ghi nhận.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 6: RAG INFORMATION */}
              {detailsTab === 'rag' && (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                      <span className="text-slate-400">Vector Collection</span>
                      <div className="font-mono font-semibold text-indigo-300">enterprise_knowledge_base</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                      <span className="text-slate-400">Embedding Model</span>
                      <div className="font-semibold text-cyan-300">nomic-embed-text (768 dims)</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                      <span className="text-slate-400">Local LLM</span>
                      <div className="font-semibold text-purple-300">Qwen 2.5 3B (Offline)</div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-white">Tái lập chỉ mục Vector (Re-index)</h4>
                      <p className="text-slate-400 mt-0.5">Trích xuất lại văn bản và cập nhật toàn bộ vector embeddings vào ChromaDB.</p>
                    </div>
                    {isAdmin && (
                      <button
                        onClick={() => handleReindexDocument(activeDoc.id)}
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-2 transition-all shadow-md"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>Chạy Re-index</span>
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Edit Metadata Modal */}
      {showEditModal && activeDoc && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-slate-700 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Pencil className="w-4 h-4 text-cyan-400" />
                <span>Chỉnh sửa thông tin tài liệu</span>
              </h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {editError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{editError}</span>
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Tiêu đề tài liệu</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Phòng ban áp dụng</label>
                <select
                  value={editDeptId}
                  onChange={(e) => setEditDeptId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Chung (Toàn doanh nghiệp)</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Loại tài liệu</label>
                  <select
                    value={editDocType}
                    onChange={(e) => setEditDocType(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="SOP">Quy trình (SOP)</option>
                    <option value="POLICY">Chính sách (Policy)</option>
                    <option value="PROCEDURE">Thủ tục (Procedure)</option>
                    <option value="GUIDE">Hướng dẫn (Guide)</option>
                    <option value="MANUAL">Sổ tay (Manual)</option>
                    <option value="REPORT">Báo cáo (Report)</option>
                    <option value="FORM">Biểu mẫu (Form)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Phiên bản</label>
                  <input
                    type="text"
                    value={editVersion}
                    onChange={(e) => setEditVersion(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Mức độ bảo mật</label>
                <select
                  value={editSecLevel}
                  onChange={(e) => setEditSecLevel(e.target.value as SecurityLevel)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="PUBLIC">PUBLIC (Công khai mọi người dùng)</option>
                  <option value="INTERNAL">INTERNAL (Toàn bộ nhân viên công ty)</option>
                  <option value="DEPARTMENT">DEPARTMENT (Chỉ phòng ban áp dụng)</option>
                  <option value="CONFIDENTIAL">CONFIDENTIAL (Tuyệt mật - chỉ cấp quyền riêng)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Danh mục nghiệp vụ</label>
                <input
                  type="text"
                  value={editCategory}
                  onChange={(e) => setEditCategory(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={editing}
                  className="w-full py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition-all shadow-md shadow-cyan-600/20"
                >
                  {editing ? 'Đang lưu thay đổi...' : 'Cập nhật tài liệu'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-slate-700 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Upload className="w-4 h-4 text-indigo-400" />
                <span>Nạp tài liệu mới vào RAG</span>
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg bg-slate-800"
              >
                Hủy
              </button>
            </div>

            {uploadError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">File tài liệu (.pdf, .docx, .txt, .xlsx, .csv)</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.xlsx,.csv"
                  onChange={(e) => {
                    const f = e.target.files?.[0] || null;
                    setUploadFile(f);
                    if (f && !uploadTitle) {
                      setUploadTitle(f.name.replace(/\.[^/.]+$/, ''));
                    }
                  }}
                  className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Tiêu đề tài liệu</label>
                <input
                  type="text"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="Ví dụ: Quy định bảo mật thông tin 2026"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Phòng ban áp dụng</label>
                <select
                  value={uploadDeptId}
                  onChange={(e) => setUploadDeptId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Chung (Toàn doanh nghiệp)</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Loại tài liệu</label>
                  <select
                    value={uploadDocType}
                    onChange={(e) => setUploadDocType(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="SOP">Quy trình (SOP)</option>
                    <option value="POLICY">Chính sách (Policy)</option>
                    <option value="PROCEDURE">Thủ tục (Procedure)</option>
                    <option value="GUIDE">Hướng dẫn (Guide)</option>
                    <option value="MANUAL">Sổ tay (Manual)</option>
                    <option value="REPORT">Báo cáo (Report)</option>
                    <option value="FORM">Biểu mẫu (Form)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Mức độ bảo mật</label>
                  <select
                    value={uploadSecLevel}
                    onChange={(e) => setUploadSecLevel(e.target.value as SecurityLevel)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="PUBLIC">PUBLIC (Công khai)</option>
                    <option value="INTERNAL">INTERNAL (Toàn công ty)</option>
                    <option value="DEPARTMENT">DEPARTMENT (Phòng ban)</option>
                    <option value="CONFIDENTIAL">CONFIDENTIAL (Tuyệt mật)</option>
                  </select>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/25 flex items-center justify-center gap-2 disabled:opacity-50 transition-all"
                >
                  {uploading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Đang trích xuất & lập chỉ mục ChromaDB...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      <span>Bắt đầu số hóa & nạp vector</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
