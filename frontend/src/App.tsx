import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { ChatPage } from './pages/ChatPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { TicketsPage } from './pages/TicketsPage';
import { DashboardPage } from './pages/DashboardPage';
import { UsersPage } from './pages/UsersPage';
import { UserProfileModal } from './components/UserProfileModal';

const MainLayout: React.FC = () => {
  const { user, loading, updateCurrentUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'tickets' | 'dashboard' | 'users'>('chat');
  const [showProfileModal, setShowProfileModal] = useState<boolean>(false);

  // State when escalating chat to ticket
  const [chatTicketSessionId, setChatTicketSessionId] = useState<string | null>(null);
  const [chatTicketDesc, setChatTicketDesc] = useState<string>('');

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070a13] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400 font-medium">Đang khởi tạo phiên làm việc...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const handleOpenTicketFromChat = (sessionId: string, initialText: string) => {
    setChatTicketSessionId(sessionId);
    setChatTicketDesc(`Sự cố phát sinh từ phiên hỏi đáp AI:\n"${initialText}"\n\nAI chưa có tài liệu hướng dẫn giải quyết.`);
    setActiveTab('tickets');
  };

  const getHeaderInfo = () => {
    switch (activeTab) {
      case 'chat':
        return {
          title: 'Trợ lý AI Doanh nghiệp',
          subtitle: 'Hỏi đáp nghiệp vụ, quy trình và giải đáp sự cố IT với Local LLM & RAG',
        };
      case 'documents':
        return {
          title: 'Kho Tri thức Doanh nghiệp',
          subtitle: 'Quản lý tài liệu kỹ thuật, chính sách và cơ sở dữ liệu vector ChromaDB',
        };
      case 'tickets':
        return {
          title: 'Hệ thống IT Support Tickets',
          subtitle: 'Tiếp nhận, xử lý và điều phối các sự cố kỹ thuật hạ tầng CNTT',
        };
      case 'dashboard':
        return {
          title: 'Báo cáo & Phân tích Quản trị',
          subtitle: 'Theo dõi hiệu năng AI, tỷ lệ tự giải quyết sự cố và nhật ký vận hành',
        };
      case 'users':
        return {
          title: 'Quản lý Tài khoản & Phân quyền Nội bộ',
          subtitle: 'Quản lý danh tính nhân sự, phân quyền vai trò RBAC và phạm vi cô lập phòng ban',
        };
    }
  };

  const headerInfo = getHeaderInfo();

  return (
    <div className="flex h-screen bg-[#070a13] text-slate-100 overflow-hidden font-sans">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        onOpenProfile={() => setShowProfileModal(true)} 
      />

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header title={headerInfo.title} subtitle={headerInfo.subtitle} />

        <div className="flex-1 overflow-y-auto">
          {activeTab === 'chat' && (
            <ChatPage onOpenTicketWithChat={handleOpenTicketFromChat} />
          )}
          {activeTab === 'documents' && <DocumentsPage />}
          {activeTab === 'tickets' && (
            <TicketsPage
              initialChatSessionId={chatTicketSessionId}
              initialDescription={chatTicketDesc}
              onClearInitialChat={() => {
                setChatTicketSessionId(null);
                setChatTicketDesc('');
              }}
            />
          )}
          {activeTab === 'dashboard' && (
            <DashboardPage onNavigateDocuments={() => setActiveTab('documents')} />
          )}
          {activeTab === 'users' && <UsersPage />}
        </div>
      </main>

      <UserProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        currentUser={user}
        onUserUpdated={(updated) => updateCurrentUser(updated)}
      />
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}

export default App;
