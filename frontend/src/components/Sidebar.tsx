import React from 'react';
import { 
  Bot, 
  MessageSquare, 
  FileText, 
  Ticket, 
  BarChart3, 
  Users,
  LogOut, 
  Cpu, 
  ShieldCheck, 
  Database,
  Building2,
  ChevronRight,
  Wrench
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  activeTab: 'chat' | 'documents' | 'tickets' | 'it-support' | 'dashboard' | 'users';
  setActiveTab: (tab: 'chat' | 'documents' | 'tickets' | 'it-support' | 'dashboard' | 'users') => void;
  onOpenProfile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, onOpenProfile }) => {
  const { user, logout, isSuperAdmin, isITAdmin, roleCode } = useAuth();

  const deptName = typeof user?.department === 'string' ? user.department : user?.department?.name;

  const canManageUsers = ['SUPER_ADMIN', 'ADMIN', 'IT_ADMIN', 'IT_MANAGER', 'DEPARTMENT_MANAGER'].includes(roleCode);

  const getRoleBadge = (code?: string) => {
    switch (code) {
      case 'SUPER_ADMIN':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">Super Admin</span>;
      case 'ADMIN':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">Admin</span>;
      case 'IT_ADMIN':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">IT Admin</span>;
      case 'IT_MANAGER':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30">IT Manager</span>;
      case 'MANAGER':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">Quản lý</span>;
      case 'DEPARTMENT_MANAGER':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Trưởng phòng</span>;
      case 'VIEWER':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-slate-700/60 text-slate-300 border border-slate-600/40">Người xem</span>;
      default:
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Nhân viên</span>;
    }
  };

  return (
    <aside className="w-64 bg-slate-900/95 border-r border-slate-800/80 flex flex-col justify-between h-screen select-none">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-slate-800/80 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white text-sm tracking-tight flex items-center gap-1.5">
              Local AI Nội bộ doanh nghiệp
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">Local Assistant & RAG</p>
          </div>
        </div>

        {/* User Card - Clickable for Profile */}
        {user && (
          <div 
            onClick={onOpenProfile}
            role="button"
            tabIndex={0}
            title="Nhấn để xem & chỉnh sửa hồ sơ cá nhân"
            className="mx-3 my-4 p-3 rounded-xl bg-slate-800/50 hover:bg-slate-800/90 border border-slate-700/50 hover:border-indigo-500/40 transition-all cursor-pointer group shadow-sm"
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2 truncate">
                <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-indigo-500 to-cyan-500 text-[11px] font-bold text-white flex items-center justify-center shrink-0">
                  {user.full_name?.charAt(0) || user.username?.charAt(0) || 'U'}
                </div>
                <span className="text-xs font-semibold text-white truncate max-w-[110px] group-hover:text-indigo-300 transition-colors" title={user.full_name}>
                  {user.full_name}
                </span>
              </div>
              {getRoleBadge(roleCode)}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
              <div className="flex items-center gap-1.5 truncate max-w-[150px]">
                <Building2 className="w-3 h-3 text-slate-500 shrink-0" />
                <span className="truncate" title={deptName || 'Toàn doanh nghiệp'}>
                  {deptName || 'Toàn doanh nghiệp'}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 group-hover:text-indigo-400 font-medium">Hồ sơ →</span>
            </div>
          </div>
        )}

        {/* Navigation items */}
        <nav className="px-3 space-y-1">
          <button
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === 'chat'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <MessageSquare className="w-4 h-4" />
              <span>Trợ lý AI (Chat)</span>
            </div>
            {activeTab === 'chat' && <ChevronRight className="w-4 h-4 opacity-70" />}
          </button>

          <button
            onClick={() => setActiveTab('documents')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === 'documents'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <FileText className="w-4 h-4" />
              <span>Kho Tài liệu (RAG)</span>
            </div>
            {activeTab === 'documents' && <ChevronRight className="w-4 h-4 opacity-70" />}
          </button>

          <button
            onClick={() => setActiveTab('tickets')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === 'tickets'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <Ticket className="w-4 h-4" />
              <span>IT Support Tickets</span>
            </div>
            {activeTab === 'tickets' && <ChevronRight className="w-4 h-4 opacity-70" />}
          </button>

          <button
            onClick={() => setActiveTab('it-support')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === 'it-support'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <Wrench className="w-4 h-4" />
              <span>Hỗ trợ IT & Script</span>
            </div>
            {activeTab === 'it-support' && <ChevronRight className="w-4 h-4 opacity-70" />}
          </button>

          {canManageUsers && (
            <button
              onClick={() => setActiveTab('users')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === 'users'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                  : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <Users className="w-4 h-4" />
                <span>Quản lý Tài khoản</span>
              </div>
              {activeTab === 'users' && <ChevronRight className="w-4 h-4 opacity-70" />}
            </button>
          )}

          {(isSuperAdmin || isITAdmin) && (
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === 'dashboard'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                  : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <BarChart3 className="w-4 h-4" />
                <span>Admin Dashboard</span>
              </div>
              {activeTab === 'dashboard' && <ChevronRight className="w-4 h-4 opacity-70" />}
            </button>
          )}
        </nav>
      </div>

      {/* Hardware Status & Logout */}
      <div className="p-3 border-t border-slate-800/80 space-y-3">
        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Local LLM:</span>
            </span>
            <span className="text-cyan-300 font-semibold">Qwen 2.5 3B</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span>Vector Store:</span>
            </span>
            <span className="text-indigo-300 font-semibold">ChromaDB</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Privacy:</span>
            </span>
            <span className="text-emerald-400 font-semibold">100% Offline</span>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition-all"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Đăng xuất</span>
        </button>
      </div>
    </aside>
  );
};
