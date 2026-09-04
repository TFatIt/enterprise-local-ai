import React from 'react';
import { 
  Bot, 
  MessageSquare, 
  FileText, 
  Ticket, 
  BarChart3, 
  LogOut, 
  Cpu, 
  ShieldCheck, 
  Database,
  Building2,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  activeTab: 'chat' | 'documents' | 'tickets' | 'dashboard';
  setActiveTab: (tab: 'chat' | 'documents' | 'tickets' | 'dashboard') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const { user, logout, isSuperAdmin, isITAdmin, roleCode } = useAuth();

  const deptName = typeof user?.department === 'string' ? user.department : user?.department?.name;

  const getRoleBadge = (code?: string) => {
    switch (code) {
      case 'SUPER_ADMIN':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">Super Admin</span>;
      case 'IT_ADMIN':
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">IT Admin</span>;
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
            <h1 className="font-bold text-white text-base tracking-tight flex items-center gap-1.5">
              Enterprise AI
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">Local Assistant & RAG</p>
          </div>
        </div>

        {/* User Card */}
        {user && (
          <div className="mx-3 my-4 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-white truncate max-w-[120px]" title={user.full_name}>
                {user.full_name}
              </span>
              {getRoleBadge(roleCode)}
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <Building2 className="w-3 h-3 text-slate-500 shrink-0" />
              <span className="truncate" title={deptName || 'Toàn doanh nghiệp'}>
                {deptName || 'Toàn doanh nghiệp'}
              </span>
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
