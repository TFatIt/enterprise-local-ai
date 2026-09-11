import React, { useState, useEffect } from 'react';
import {
  Wrench,
  Terminal,
  FolderSync,
  ClipboardCheck,
  Code2,
  Copy,
  Check,
  Download,
  Play,
  RefreshCw,
  AlertTriangle,
  Printer,
  FileSpreadsheet,
  Network,
  HardDrive,
  PackageCheck,
  Upload,
  Trash2,
  CheckCircle2,
  Clock,
  Layers,
  ChevronRight,
  ShieldCheck,
  FileText
} from 'lucide-react';
import { api } from '../api/client';

interface QuickFixItem {
  id: string;
  title: string;
  category: string;
  description: string;
  script: string;
  script_type: string;
  requires_admin: boolean;
  execution_guide: string;
}

interface DiagnoseResult {
  problem_summary: string;
  category: string;
  root_cause_analysis: string;
  user_action_steps: string[];
  it_admin_steps: string[];
  recommended_script?: string;
  script_type?: string;
  prevention_tip?: string;
}

interface AutoImportFile {
  file_name: string;
  relative_path: string;
  category: string;
  extension: string;
  is_supported: boolean;
  size_bytes: number;
  size_human: string;
  modified_at: string;
  is_imported: boolean;
  imported_at?: string;
  document_id?: string;
  chunks_count: number;
  status: string;
}

interface AutoImportStatus {
  success: boolean;
  watch_directory: string;
  watch_directory_exists: boolean;
  total_files_in_folder: number;
  pending_import: number;
  already_imported: number;
  auto_imported_documents_in_db: number;
  last_scan?: string;
  vision_model_available: boolean;
}

export const ITSupportPage: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'quick_fixes' | 'diagnose' | 'auto_import' | 'handover' | 'script_gen'>('quick_fixes');

  // Quick Fixes States
  const [quickFixes, setQuickFixes] = useState<QuickFixItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [loadingQuickFixes, setLoadingQuickFixes] = useState<boolean>(false);
  const [copiedScriptId, setCopiedScriptId] = useState<string | null>(null);

  // Diagnose States
  const [diagProblem, setDiagProblem] = useState<string>('');
  const [diagCategory, setDiagCategory] = useState<string>('PRINTER');
  const [diagErrorCode, setDiagErrorCode] = useState<string>('');
  const [diagLoading, setDiagLoading] = useState<boolean>(false);
  const [diagResult, setDiagResult] = useState<DiagnoseResult | null>(null);
  const [diagCopied, setDiagCopied] = useState<boolean>(false);

  // Auto-Import States
  const [autoStatus, setAutoStatus] = useState<AutoImportStatus | null>(null);
  const [autoFiles, setAutoFiles] = useState<AutoImportFile[]>([]);
  const [loadingAutoData, setLoadingAutoData] = useState<boolean>(false);
  const [scanning, setScanning] = useState<boolean>(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [reindexingFile, setReindexingFile] = useState<string | null>(null);
  const [deletingFile, setDeletingFile] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [autoSync, setAutoSync] = useState<boolean>(true);
  const [uploadFileObj, setUploadFileObj] = useState<File | null>(null);
  const [uploadSubfolder, setUploadSubfolder] = useState<string>('docs');
  const [uploadAutoIndex, setUploadAutoIndex] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);

  // Handover Checklist States
  const [hoEmpName, setHoEmpName] = useState<string>('');
  const [hoEmpCode, setHoEmpCode] = useState<string>('');
  const [hoDept, setHoDept] = useState<string>('Kế toán');
  const [hoPosition, setHoPosition] = useState<string>('Nhân viên Kế toán');
  const [hoPcType, setHoPcType] = useState<string>('LAPTOP');
  const [hoSpecs, setHoSpecs] = useState<string>('Dell Latitude 5440, Core i5-1345U, 16GB RAM, 512GB SSD');
  const [hoPrinters, setHoPrinters] = useState<string>('HP LaserJet Pro M404dn, Canon LBP2900');
  const [hoSoftware, setHoSoftware] = useState<string>('MISA SME.NET 2023, HTKK Thuế, Token Chữ ký số');
  const [hoLoading, setHoLoading] = useState<boolean>(false);
  const [hoMarkdown, setHoMarkdown] = useState<string | null>(null);
  const [hoCopied, setHoCopied] = useState<boolean>(false);

  // Script Generator States
  const [genTask, setGenTask] = useState<string>('');
  const [genLang, setGenLang] = useState<string>('powershell');
  const [genLoading, setGenLoading] = useState<boolean>(false);
  const [genResult, setGenResult] = useState<{ title: string; script_code: string; explanation: string } | null>(null);
  const [genCopied, setGenCopied] = useState<boolean>(false);

  // Fetch Quick Fixes
  const fetchQuickFixes = async () => {
    setLoadingQuickFixes(true);
    try {
      const res = await api.get('/it-support/quick-fixes', {
        params: { category: selectedCategory === 'ALL' ? undefined : selectedCategory }
      });
      setQuickFixes(res.data);
    } catch (err) {
      console.error('Error fetching quick fixes:', err);
    } finally {
      setLoadingQuickFixes(false);
    }
  };

  // Fetch Auto-Import Data
  const fetchAutoImportData = async () => {
    setLoadingAutoData(true);
    try {
      const [statusRes, filesRes] = await Promise.all([
        api.get('/auto-import/status'),
        api.get('/auto-import/files')
      ]);
      setAutoStatus(statusRes.data);
      setAutoFiles(filesRes.data.files || []);
    } catch (err) {
      console.error('Error fetching auto import data:', err);
    } finally {
      setLoadingAutoData(false);
    }
  };

  useEffect(() => {
    if (activeSubTab === 'quick_fixes') {
      fetchQuickFixes();
    } else if (activeSubTab === 'auto_import') {
      fetchAutoImportData();
      if (autoSync) {
        const intervalId = setInterval(() => {
          // Background sync without full-screen loading spinner
          Promise.all([
            api.get('/auto-import/status'),
            api.get('/auto-import/files')
          ]).then(([statusRes, filesRes]) => {
            setAutoStatus(statusRes.data);
            setAutoFiles(filesRes.data.files || []);
          }).catch(() => {});
        }, 4000);
        return () => clearInterval(intervalId);
      }
    }
  }, [activeSubTab, selectedCategory, autoSync]);

  // Handle Copy to Clipboard
  const copyToClipboard = (text: string, onDone: () => void) => {
    navigator.clipboard.writeText(text);
    onDone();
  };

  // Handle Download File (.ps1 or .bat or .md)
  const downloadFile = (filename: string, content: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Trigger Diagnose
  const handleDiagnose = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!diagProblem.trim()) return;
    setDiagLoading(true);
    setDiagResult(null);
    try {
      const res = await api.post('/it-support/diagnose', {
        problem_description: diagProblem,
        category: diagCategory,
        error_code_or_message: diagErrorCode || undefined
      });
      setDiagResult(res.data);
    } catch (err) {
      console.error('Diagnostic error:', err);
      alert('Có lỗi xảy ra khi chẩn đoán sự cố.');
    } finally {
      setDiagLoading(false);
    }
  };

  // Trigger Auto-Import Scan
  const handleTriggerScan = async () => {
    setScanning(true);
    setScanMessage(null);
    try {
      const res = await api.post('/auto-import/scan');
      const results = res.data.results || {};
      setScanMessage(`Quét xong: ${results.new || 0} mới, ${results.updated || 0} cập nhật, ${results.skipped || 0} bỏ qua.`);
      fetchAutoImportData();
    } catch (err) {
      console.error('Scan error:', err);
      setScanMessage('Lỗi trong quá trình quét thư mục.');
    } finally {
      setScanning(false);
    }
  };

  // Reindex single file
  const handleReindexFile = async (relPath: string) => {
    setReindexingFile(relPath);
    try {
      await api.post('/auto-import/reindex-file', null, {
        params: { relative_path: relPath }
      });
      fetchAutoImportData();
    } catch (err) {
      console.error('Reindex error:', err);
      alert('Không thể lập chỉ mục lại tệp.');
    } finally {
      setReindexingFile(null);
    }
  };

  // Delete file from auto_import
  const handleDeleteFile = async (relPath: string) => {
    if (!window.confirm(`Bạn có chắc muốn xóa tệp "${relPath}" khỏi thư mục và toàn bộ vector trong CSDL?`)) return;
    setDeletingFile(relPath);
    try {
      await api.delete('/auto-import/files', {
        params: { relative_path: relPath }
      });
      fetchAutoImportData();
    } catch (err) {
      console.error('Delete error:', err);
      alert('Lỗi khi xóa tệp.');
    } finally {
      setDeletingFile(null);
    }
  };

  // Upload file to auto_import
  const handleUploadFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFileObj) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFileObj);
      formData.append('subfolder', uploadSubfolder);
      formData.append('auto_index', uploadAutoIndex ? 'true' : 'false');

      await api.post('/auto-import/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setShowUploadModal(false);
      setUploadFileObj(null);
      fetchAutoImportData();
    } catch (err) {
      console.error('Upload error:', err);
      alert('Lỗi tải tệp lên thư mục.');
    } finally {
      setUploading(false);
    }
  };

  // Generate Handover Checklist
  const handleGenerateHandover = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hoEmpName.trim()) return;
    setHoLoading(true);
    setHoMarkdown(null);
    try {
      const res = await api.post('/it-support/handover-checklist', {
        employee_name: hoEmpName,
        employee_code: hoEmpCode,
        department: hoDept,
        position: hoPosition,
        pc_type: hoPcType,
        hardware_specs: hoSpecs,
        assigned_printers: hoPrinters ? hoPrinters.split(',').map(s => s.trim()) : [],
        software_packages: hoSoftware ? hoSoftware.split(',').map(s => s.trim()) : []
      });
      setHoMarkdown(res.data.checklist_markdown);
    } catch (err) {
      console.error('Handover error:', err);
      alert('Lỗi sinh biên bản bàn giao.');
    } finally {
      setHoLoading(false);
    }
  };

  // Generate Custom Script
  const handleGenerateScript = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!genTask.trim()) return;
    setGenLoading(true);
    setGenResult(null);
    try {
      const res = await api.post('/it-support/generate-script', {
        task_description: genTask,
        script_language: genLang,
        target_os: 'windows'
      });
      setGenResult(res.data);
    } catch (err) {
      console.error('Script gen error:', err);
      alert('Lỗi khi sinh script.');
    } finally {
      setGenLoading(false);
    }
  };

  const getCategoryIcon = (cat: string) => {
    switch (cat.toUpperCase()) {
      case 'PRINTER':
        return <Printer className="w-5 h-5 text-amber-400" />;
      case 'EXCEL_OFFICE':
        return <FileSpreadsheet className="w-5 h-5 text-emerald-400" />;
      case 'NETWORK':
        return <Network className="w-5 h-5 text-cyan-400" />;
      case 'SOFTWARE':
        return <PackageCheck className="w-5 h-5 text-indigo-400" />;
      case 'HARDWARE':
        return <HardDrive className="w-5 h-5 text-rose-400" />;
      default:
        return <Terminal className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800/80 p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Wrench className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">Trung tâm Hỗ trợ IT & Quản trị Hạ tầng</h1>
                <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold">
                  IT Support Toolkit
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Chẩn đoán lỗi thông minh, kho script PowerShell chạy ngay, biên bản bàn giao máy tính và đồng bộ thư mục tự động nạp tri thức
              </p>
            </div>
          </div>

          {/* Quick Sub-Navigation Pills */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-950/70 p-1.5 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveSubTab('quick_fixes')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSubTab === 'quick_fixes'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Script Nhanh</span>
            </button>

            <button
              onClick={() => setActiveSubTab('diagnose')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSubTab === 'diagnose'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Chẩn đoán AI</span>
            </button>

            <button
              onClick={() => setActiveSubTab('auto_import')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSubTab === 'auto_import'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <FolderSync className="w-3.5 h-3.5" />
              <span>Thư mục Tự nạp</span>
            </button>

            <button
              onClick={() => setActiveSubTab('handover')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSubTab === 'handover'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <ClipboardCheck className="w-3.5 h-3.5" />
              <span>Bàn giao Máy</span>
            </button>

            <button
              onClick={() => setActiveSubTab('script_gen')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSubTab === 'script_gen'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Tạo Script AI</span>
            </button>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SUB-TAB 1: QUICK FIXES                                                    */}
      {/* ========================================================================= */}
      {activeSubTab === 'quick_fixes' && (
        <div className="space-y-6">
          {/* Categories Filter Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { id: 'ALL', label: 'Tất cả giải pháp' },
                { id: 'PRINTER', label: 'Máy in (Print Spooler)' },
                { id: 'EXCEL_OFFICE', label: 'Excel & Office đơ' },
                { id: 'NETWORK', label: 'Mạng LAN & DNS' },
                { id: 'SOFTWARE', label: 'Bộ phần mềm Winget' },
                { id: 'HARDWARE', label: 'Dọn ổ đĩa C' },
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    selectedCategory === cat.id
                      ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <span className="text-xs text-slate-400 font-medium">
              {quickFixes.length} giải pháp được xác thực
            </span>
          </div>

          {/* Grid of Quick Fix Cards */}
          {loadingQuickFixes ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {quickFixes.map(fix => {
                const isCopied = copiedScriptId === fix.id;
                const fileExt = fix.script_type === 'bat' ? 'bat' : 'ps1';
                const downloadName = `${fix.id}.${fileExt}`;

                return (
                  <div
                    key={fix.id}
                    className="flex flex-col justify-between bg-slate-900/90 rounded-xl border border-slate-800 hover:border-slate-700 transition-all p-5 shadow-lg group"
                  >
                    <div>
                      {/* Card Header */}
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-3">
                          <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
                            {getCategoryIcon(fix.category)}
                          </div>
                          <div>
                            <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                              {fix.title}
                            </h3>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                                {fix.category}
                              </span>
                              {fix.requires_admin ? (
                                <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                                  Cần quyền Admin
                                </span>
                              ) : (
                                <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                                  User thường chạy được
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-xs text-slate-300 leading-relaxed mb-3">
                        {fix.description}
                      </p>

                      {/* Execution Guide */}
                      <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 mb-3 flex items-start gap-2">
                        <ChevronRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span><strong>Cách thực thi:</strong> {fix.execution_guide}</span>
                      </div>

                      {/* Script Preview Code Block */}
                      <div className="relative rounded-lg bg-[#050811] border border-slate-800/90 p-3 text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-36 select-all">
                        <pre className="whitespace-pre-wrap">{fix.script}</pre>
                      </div>
                    </div>

                    {/* Card Actions Footer */}
                    <div className="flex items-center justify-end gap-2 pt-4 mt-4 border-t border-slate-800/70">
                      <button
                        onClick={() => downloadFile(downloadName, fix.script)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors border border-slate-700"
                        title="Tải tệp script trực tiếp về máy tính"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Tải .{fileExt}</span>
                      </button>

                      <button
                        onClick={() => copyToClipboard(fix.script, () => {
                          setCopiedScriptId(fix.id);
                          setTimeout(() => setCopiedScriptId(null), 2000);
                        })}
                        className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                          isCopied
                            ? 'bg-emerald-600 text-white'
                            : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow shadow-indigo-600/25'
                        }`}
                      >
                        {isCopied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{isCopied ? 'Đã sao chép!' : 'Sao chép Script'}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* SUB-TAB 2: SMART DIAGNOSE                                                 */}
      {/* ========================================================================= */}
      {activeSubTab === 'diagnose' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Input Form Column */}
          <div className="lg:col-span-5 space-y-4">
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-lg">
              <h2 className="text-sm font-bold text-white flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Mô tả Sự cố cần Chẩn đoán
              </h2>
              <p className="text-xs text-slate-400 mb-4">
                AI sẽ kết hợp tài liệu kỹ thuật nội bộ (RAG) và tri thức chuyên sâu để đưa ra hướng dẫn từng bước và lệnh sửa lỗi.
              </p>

              <form onSubmit={handleDiagnose} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Phân loại sự cố</label>
                  <select
                    value={diagCategory}
                    onChange={(e) => setDiagCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="PRINTER">Máy in (Print Spooler / Lỗi in mạng 0x11b)</option>
                    <option value="EXCEL_OFFICE">Excel & Microsoft Office (Đơ, tính toán lâu, treo)</option>
                    <option value="NETWORK">Mạng nội bộ LAN / Wi-Fi / DNS / VPN</option>
                    <option value="SOFTWARE">Cài đặt & Xung đột phần mềm</option>
                    <option value="HARDWARE">Phần cứng & Ổ đĩa C bị đầy</option>
                    <option value="GENERAL">Sự cố CNTT chung</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Mã lỗi hoặc Thông báo cụ thể (nếu có)</label>
                  <input
                    type="text"
                    value={diagErrorCode}
                    onChange={(e) => setDiagErrorCode(e.target.value)}
                    placeholder="Vd: 0x0000011b, #VALUE!, Spooler stopped, 10060..."
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Mô tả chi tiết triệu chứng lỗi *</label>
                  <textarea
                    rows={4}
                    value={diagProblem}
                    onChange={(e) => setDiagProblem(e.target.value)}
                    placeholder="Vd: Máy kế toán mỗi lần lưu file Excel có nhiều công thức SUMIFS thì máy đơ rất lâu, quạt kêu to..."
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                {/* Quick Symptom Chips */}
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1.5">Gợi ý sự cố phổ biến:</label>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      { cat: 'PRINTER', text: 'Kẹt lệnh in trong hàng đợi Spooler không xóa được' },
                      { cat: 'PRINTER', text: 'Máy in mạng chia sẻ báo lỗi 0x0000011b' },
                      { cat: 'EXCEL_OFFICE', text: 'File Excel nhiều công thức bị đơ khi lưu file' },
                      { cat: 'NETWORK', text: 'Mất mạng nội bộ, rớt kết nối máy chủ tệp tin' },
                      { cat: 'HARDWARE', text: 'Ổ đĩa C đỏ báo động dưới 5GB dung lượng trống' }
                    ].map((chip, idx) => (
                      <button
                        type="button"
                        key={idx}
                        onClick={() => {
                          setDiagCategory(chip.cat);
                          setDiagProblem(chip.text);
                        }}
                        className="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/60"
                      >
                        + {chip.text}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={diagLoading || !diagProblem.trim()}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-all shadow-lg shadow-indigo-600/25"
                >
                  {diagLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>AI đang phân tích & tra cứu tài liệu...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      <span>Chẩn đoán & Lấy Script Sửa lỗi</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Diagnostic Result Column */}
          <div className="lg:col-span-7">
            {diagResult ? (
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-lg space-y-5">
                {/* Result Header */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <h3 className="text-sm font-bold text-white">Kết quả Chẩn đoán Chuyên sâu</h3>
                  </div>
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold">
                    {diagResult.category}
                  </span>
                </div>

                {/* 1. Root Cause */}
                <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/30">
                  <h4 className="text-xs font-bold text-indigo-300 mb-1 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" />
                    1. Phân tích Nguyên nhân gốc rễ (Root Cause)
                  </h4>
                  <p className="text-xs text-slate-200 leading-relaxed">{diagResult.root_cause_analysis}</p>
                </div>

                {/* 2. User Steps */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <h4 className="text-xs font-bold text-amber-300 mb-2">2. Hướng dẫn nhanh cho Người dùng</h4>
                  <ul className="space-y-1.5">
                    {diagResult.user_action_steps.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                        <span className="w-4 h-4 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 3. IT Admin Steps */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <h4 className="text-xs font-bold text-cyan-300 mb-2">3. Các bước xử lý chuyên sâu cho Kỹ thuật IT</h4>
                  <ul className="space-y-1.5">
                    {diagResult.it_admin_steps.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                        <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-300 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 4. Recommended Script */}
                {diagResult.recommended_script && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                        <Terminal className="w-4 h-4" />
                        4. Script PowerShell Khắc phục Tự động
                      </h4>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => downloadFile('it_repair_script.ps1', diagResult.recommended_script!)}
                          className="px-2 py-1 rounded text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1 border border-slate-700"
                        >
                          <Download className="w-3 h-3" />
                          <span>Tải .ps1</span>
                        </button>
                        <button
                          onClick={() => copyToClipboard(diagResult.recommended_script!, () => {
                            setDiagCopied(true);
                            setTimeout(() => setDiagCopied(false), 2000);
                          })}
                          className="px-2 py-1 rounded text-[11px] bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1 font-medium"
                        >
                          {diagCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                          <span>{diagCopied ? 'Đã sao chép' : 'Sao chép mã'}</span>
                        </button>
                      </div>
                    </div>

                    <div className="rounded-lg bg-[#050811] border border-slate-800 p-3 text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-48 select-all">
                      <pre className="whitespace-pre-wrap">{diagResult.recommended_script}</pre>
                    </div>
                  </div>
                )}

                {/* 5. Prevention Tip */}
                {diagResult.prevention_tip && (
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-xs text-emerald-200 flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span><strong>Biện pháp phòng ngừa lâu dài:</strong> {diagResult.prevention_tip}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 bg-slate-900/40 rounded-xl border border-dashed border-slate-800 text-center">
                <AlertTriangle className="w-10 h-10 text-slate-600 mb-3" />
                <h4 className="text-sm font-semibold text-slate-300 mb-1">Chưa có kết quả chẩn đoán</h4>
                <p className="text-xs text-slate-500 max-w-sm">
                  Chọn loại sự cố và nhập triệu chứng lỗi ở cột bên trái, AI sẽ phân tích và đưa ra giải pháp toàn diện.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SUB-TAB 3: AUTO IMPORT WATCHER                                            */}
      {/* ========================================================================= */}
      {activeSubTab === 'auto_import' && (
        <div className="space-y-6">
          {/* Status & Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Thư mục Giám sát</span>
                <FolderSync className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-sm font-bold text-white truncate" title={autoStatus?.watch_directory}>
                auto_import_documents
              </div>
              <span className="text-[10px] text-emerald-400 font-medium">Đang hoạt động</span>
            </div>

            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Tổng tệp trong thư mục</span>
                <FileText className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-xl font-bold text-white">{autoStatus?.total_files_in_folder || 0}</div>
              <span className="text-[10px] text-slate-400">docs, images, videos</span>
            </div>

            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Đã nạp vào ChromaDB</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-xl font-bold text-emerald-400">{autoStatus?.already_imported || 0}</div>
              <span className="text-[10px] text-slate-400">{autoStatus?.pending_import || 0} tệp đang chờ nạp</span>
            </div>

            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Hỗ trợ Vision Model</span>
                <Layers className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-sm font-bold text-white">
                {autoStatus?.vision_model_available ? 'Sẵn sàng (minicpm-v)' : 'Chưa tải (Fallback OCR)'}
              </div>
              <span className="text-[10px] text-slate-400">Đọc hình ảnh & video</span>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/70 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white">Danh sách Tệp Nạp Tự động</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Đường dẫn trên máy: <code className="text-indigo-300 font-mono text-[11px]">{autoStatus?.watch_directory || 'D:\\...\\auto_import_documents'}</code>
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setAutoSync(!autoSync)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                  autoSync
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/10'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
                title="Bật/Tắt chế độ tự động đồng bộ ngầm thời gian thực mỗi 4 giây"
              >
                <span className={`w-2 h-2 rounded-full ${autoSync ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`}></span>
                <span>{autoSync ? 'Live Sync: BẬT (4s)' : 'Live Sync: TẮT'}</span>
              </button>

              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Tải tệp vào thư mục</span>
              </button>

              <button
                onClick={handleTriggerScan}
                disabled={scanning}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-all shadow shadow-indigo-600/25"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
                <span>{scanning ? 'Đang quét...' : 'Quét & Nạp ngay'}</span>
              </button>
            </div>
          </div>

          {scanMessage && (
            <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-500/40 text-xs text-indigo-300 flex items-center justify-between">
              <span>{scanMessage}</span>
              <button onClick={() => setScanMessage(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>
          )}

          {/* Files Table */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-lg">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Tên tệp tin</th>
                    <th className="px-4 py-3 font-semibold">Thư mục</th>
                    <th className="px-4 py-3 font-semibold">Dung lượng</th>
                    <th className="px-4 py-3 font-semibold">Trạng thái Nạp</th>
                    <th className="px-4 py-3 font-semibold">Vector Chunks</th>
                    <th className="px-4 py-3 font-semibold text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loadingAutoData ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                        <span>Đang tải danh sách tệp...</span>
                      </td>
                    </tr>
                  ) : autoFiles.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-500">
                        Chưa có tệp nào trong thư mục auto_import_documents. Hãy thả tài liệu vào hoặc bấm "Tải tệp vào thư mục".
                      </td>
                    </tr>
                  ) : (
                    autoFiles.map((f, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-4 py-3 font-medium text-white flex items-center gap-2">
                          <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                          <span className="truncate max-w-xs" title={f.file_name}>{f.file_name}</span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                            {f.category}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-400">{f.size_human}</td>
                        <td className="px-4 py-3">
                          {f.is_imported ? (
                            <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px] font-semibold">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Đã nạp
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-amber-400 text-[11px] font-semibold">
                              <Clock className="w-3.5 h-3.5" />
                              Chờ quét
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className="font-mono text-indigo-300 font-semibold">{f.chunks_count} chunks</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleReindexFile(f.relative_path)}
                              disabled={reindexingFile === f.relative_path}
                              title="Lập chỉ mục lại tệp này"
                              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-indigo-400 transition-colors"
                            >
                              <RefreshCw className={`w-3.5 h-3.5 ${reindexingFile === f.relative_path ? 'animate-spin' : ''}`} />
                            </button>
                            <button
                              onClick={() => handleDeleteFile(f.relative_path)}
                              disabled={deletingFile === f.relative_path}
                              title="Xóa tệp và vector chunks"
                              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SUB-TAB 4: HANDOVER CHECKLIST                                             */}
      {/* ========================================================================= */}
      {activeSubTab === 'handover' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-lg space-y-4">
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <ClipboardCheck className="w-4 h-4 text-indigo-400" />
                Thông tin Bàn giao Thiết bị CNTT
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Tự động lập biên bản bàn giao máy tính, tài khoản và phân quyền cho nhân sự mới.
              </p>
            </div>

            <form onSubmit={handleGenerateHandover} className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Họ tên nhân viên *</label>
                  <input
                    type="text"
                    value={hoEmpName}
                    onChange={(e) => setHoEmpName(e.target.value)}
                    placeholder="Nguyễn Văn A"
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Mã nhân viên</label>
                  <input
                    type="text"
                    value={hoEmpCode}
                    onChange={(e) => setHoEmpCode(e.target.value)}
                    placeholder="NV-2026-001"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Phòng ban *</label>
                  <input
                    type="text"
                    value={hoDept}
                    onChange={(e) => setHoDept(e.target.value)}
                    placeholder="Kế toán / Nhân sự..."
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Chức danh</label>
                  <input
                    type="text"
                    value={hoPosition}
                    onChange={(e) => setHoPosition(e.target.value)}
                    placeholder="Chuyên viên..."
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Loại thiết bị</label>
                  <select
                    value={hoPcType}
                    onChange={(e) => setHoPcType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="LAPTOP">Máy tính xách tay (Laptop)</option>
                    <option value="DESKTOP">Máy tính để bàn (Desktop PC)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Cấu hình máy</label>
                  <input
                    type="text"
                    value={hoSpecs}
                    onChange={(e) => setHoSpecs(e.target.value)}
                    placeholder="Core i5, 16GB, 512GB SSD..."
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Máy in được kết nối</label>
                <input
                  type="text"
                  value={hoPrinters}
                  onChange={(e) => setHoPrinters(e.target.value)}
                  placeholder="HP LaserJet M404dn, Canon LBP2900..."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Phần mềm nghiệp vụ cài riêng</label>
                <input
                  type="text"
                  value={hoSoftware}
                  onChange={(e) => setHoSoftware(e.target.value)}
                  placeholder="MISA, HTKK, Photoshop, VS Code..."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={hoLoading || !hoEmpName.trim()}
                className="w-full py-2.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-all shadow-lg shadow-indigo-600/25"
              >
                {hoLoading ? 'Đang tạo biên bản...' : 'Sinh Biên bản Bàn giao'}
              </button>
            </form>
          </div>

          <div className="lg:col-span-7 bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-lg flex flex-col justify-between">
            {hoMarkdown ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Xem trước Biên bản Bàn giao
                  </h3>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => downloadFile(`Bien_ban_ban_giao_${hoEmpCode || 'PC'}.md`, hoMarkdown)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Tải .md</span>
                    </button>
                    <button
                      onClick={() => copyToClipboard(hoMarkdown, () => {
                        setHoCopied(true);
                        setTimeout(() => setHoCopied(false), 2000);
                      })}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1.5 shadow"
                    >
                      {hoCopied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{hoCopied ? 'Đã sao chép' : 'Sao chép văn bản'}</span>
                    </button>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#050811] border border-slate-800 font-mono text-xs text-slate-200 overflow-y-auto max-h-[500px] whitespace-pre-wrap select-all leading-relaxed">
                  {hoMarkdown}
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center text-slate-500">
                <ClipboardCheck className="w-10 h-10 text-slate-600 mb-3" />
                <h4 className="text-sm font-semibold text-slate-300 mb-1">Chưa có biên bản</h4>
                <p className="text-xs text-slate-500 max-w-sm">
                  Điền thông tin nhân viên và cấu hình bàn giao ở cột bên trái để sinh văn bản bàn giao tiêu chuẩn doanh nghiệp.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SUB-TAB 5: AI SCRIPT GENERATOR                                            */}
      {/* ========================================================================= */}
      {activeSubTab === 'script_gen' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-lg space-y-4">
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Code2 className="w-4 h-4 text-cyan-400" />
                Trình sinh Script Quản trị Tự động
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Nhập tác vụ bạn muốn tự động hóa, AI sẽ viết script PowerShell hoặc Batch an toàn, có bẫy lỗi và log màu.
              </p>
            </div>

            <form onSubmit={handleGenerateScript} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Ngôn ngữ Script</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'powershell', label: 'PowerShell (.ps1)' },
                    { id: 'bat', label: 'Batch File (.bat)' }
                  ].map(l => (
                    <button
                      type="button"
                      key={l.id}
                      onClick={() => setGenLang(l.id)}
                      className={`py-2 text-xs font-semibold rounded-lg border transition-all ${
                        genLang === l.id
                          ? 'bg-indigo-600 text-white border-indigo-500'
                          : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                      }`}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Yêu cầu tác vụ IT *</label>
                <textarea
                  rows={5}
                  value={genTask}
                  onChange={(e) => setGenTask(e.target.value)}
                  placeholder="Vd: Viết script kiểm tra card mạng, nếu ping tới 8.8.8.8 và 192.168.1.1 thất bại thì tự động flush DNS và khởi động lại card mạng..."
                  required
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={genLoading || !genTask.trim()}
                className="w-full py-2.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-all shadow-lg shadow-indigo-600/25"
              >
                {genLoading ? 'AI đang viết script...' : 'Tạo Script Tự động'}
              </button>
            </form>
          </div>

          <div className="lg:col-span-7 bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-lg flex flex-col justify-between">
            {genResult ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-emerald-400" />
                    {genResult.title}
                  </h3>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => downloadFile(`script_${genLang}.${genLang === 'bat' ? 'bat' : 'ps1'}`, genResult.script_code)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Tải về</span>
                    </button>
                    <button
                      onClick={() => copyToClipboard(genResult.script_code, () => {
                        setGenCopied(true);
                        setTimeout(() => setGenCopied(false), 2000);
                      })}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1.5 shadow"
                    >
                      {genCopied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{genCopied ? 'Đã sao chép' : 'Sao chép mã'}</span>
                    </button>
                  </div>
                </div>

                <div className="rounded-lg bg-[#050811] border border-slate-800 p-4 font-mono text-xs text-emerald-300 overflow-x-auto max-h-96 select-all whitespace-pre-wrap">
                  {genResult.script_code}
                </div>

                <p className="text-xs text-slate-400">{genResult.explanation}</p>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center text-slate-500">
                <Code2 className="w-10 h-10 text-slate-600 mb-3" />
                <h4 className="text-sm font-semibold text-slate-300 mb-1">Chưa có script nào được tạo</h4>
                <p className="text-xs text-slate-500 max-w-sm">
                  Nhập tác vụ bạn muốn thực hiện ở cột bên trái và bấm "Tạo Script Tự động".
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Upload to Auto-Import Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-slate-800 w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Upload className="w-5 h-5 text-indigo-400" />
              Tải tệp vào thư mục tự nạp
            </h3>

            <form onSubmit={handleUploadFile} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Chọn tệp tài liệu / ảnh / video</label>
                <input
                  type="file"
                  onChange={(e) => setUploadFileObj(e.target.files?.[0] || null)}
                  required
                  className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Thư mục phân loại con</label>
                <select
                  value={uploadSubfolder}
                  onChange={(e) => setUploadSubfolder(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200"
                >
                  <option value="docs">docs (Tài liệu Word, Excel, PDF, Text, Markdown...)</option>
                  <option value="images">images (Hình ảnh chụp màn hình, sơ đồ mạng...)</option>
                  <option value="videos">videos (Video hướng dẫn, quay thao tác...)</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="autoIndexCheckbox"
                  checked={uploadAutoIndex}
                  onChange={(e) => setUploadAutoIndex(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-700 text-indigo-600 focus:ring-0"
                />
                <label htmlFor="autoIndexCheckbox" className="text-xs text-slate-300 cursor-pointer">
                  Tự động phân tích & nạp vào Knowledge Base ngay lập tức
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-white"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFileObj}
                  className="px-4 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50"
                >
                  {uploading ? 'Đang tải lên...' : 'Tải lên ngay'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
