import React, { useState, useEffect } from 'react';
import { 
  Ticket, 
  Plus, 
  Filter, 
  MessageSquare, 
  User, 
  Lock, 
  ChevronRight,
  Send,
  Wrench,
  Sparkles
} from 'lucide-react';
import { api } from '../api/client';
import type { TicketItem } from '../types';
import { useAuth } from '../context/AuthContext';

interface TicketsPageProps {
  initialChatSessionId?: string | null;
  initialDescription?: string;
  onClearInitialChat?: () => void;
}

export const TicketsPage: React.FC<TicketsPageProps> = ({
  initialChatSessionId,
  initialDescription,
  onClearInitialChat
}) => {
  const { user, isITAdmin, isSuperAdmin } = useAuth();
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedTicket, setSelectedTicket] = useState<TicketItem | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(Boolean(initialChatSessionId));

  // Create Ticket Form
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState(initialDescription || '');
  const [newCat, setNewCat] = useState('GENERAL');
  const [newPriority, setNewPriority] = useState('MEDIUM');
  const [creating, setCreating] = useState(false);
  const [triageLoading, setTriageLoading] = useState(false);
  const [triageResult, setTriageResult] = useState<any>(null);

  const handleAutoTriage = async () => {
    if (!newTitle.trim() && !newDesc.trim()) {
      alert('Vui lòng nhập tiêu đề hoặc mô tả sự cố để AI phân tích.');
      return;
    }
    setTriageLoading(true);
    setTriageResult(null);
    try {
      const resp = await api.post('/tickets/auto-triage', {
        title: newTitle.trim() || 'Sự cố CNTT',
        description: newDesc.trim() || newTitle.trim(),
      });
      setNewCat(resp.data.suggested_category);
      setNewPriority(resp.data.suggested_priority);
      setTriageResult(resp.data);
    } catch {
      alert('Hệ thống AI bận, vui lòng chọn phân loại thủ công.');
    } finally {
      setTriageLoading(false);
    }
  };

  // Comment Form
  const [commentText, setCommentText] = useState('');
  const [isInternalComment, setIsInternalComment] = useState(false);
  const [commenting, setCommenting] = useState(false);

  // Status & Resolution update
  const [resolutionNotes, setResolutionNotes] = useState('');

  const canManage = isITAdmin || isSuperAdmin;

  const loadTickets = async () => {
    setLoading(true);
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const resp = await api.get<TicketItem[]>('/tickets', { params });
      setTickets(resp.data);
    } catch (err) {
      console.error('Failed to load tickets', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, [statusFilter]);

  const loadTicketDetail = async (ticketId: string) => {
    try {
      const resp = await api.get<TicketItem>(`/tickets/${ticketId}`);
      setSelectedTicket(resp.data);
    } catch (err) {
      console.error('Failed to load ticket detail', err);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDesc.trim()) return;

    setCreating(true);
    try {
      const payload: any = {
        title: newTitle.trim(),
        description: newDesc.trim(),
        category: newCat,
        priority: newPriority,
      };
      if (initialChatSessionId) {
        payload.chat_session_id = initialChatSessionId;
      }

      await api.post('/tickets', payload);
      setShowCreateModal(false);
      setNewTitle('');
      setNewDesc('');
      if (onClearInitialChat) onClearInitialChat();
      loadTickets();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Tạo ticket thất bại.');
    } finally {
      setCreating(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim() || !selectedTicket) return;

    setCommenting(true);
    try {
      await api.post(`/tickets/${selectedTicket.id}/comments`, {
        content: commentText.trim(),
        is_internal: isInternalComment,
      });
      setCommentText('');
      setIsInternalComment(false);
      loadTicketDetail(selectedTicket.id);
      loadTickets();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Thêm phản hồi thất bại.');
    } finally {
      setCommenting(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!selectedTicket) return;
    try {
      await api.patch(`/tickets/${selectedTicket.id}/status`, {
        status: newStatus,
        resolution_notes: resolutionNotes.trim() || undefined,
      });
      loadTicketDetail(selectedTicket.id);
      loadTickets();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Cập nhật trạng thái thất bại.');
    }
  };

  const handleAssignToMe = async () => {
    if (!selectedTicket || !user) return;
    try {
      await api.patch(`/tickets/${selectedTicket.id}/assign`, {
        assigned_to: user.id,
      });
      loadTicketDetail(selectedTicket.id);
      loadTickets();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Phân công thất bại.');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">Mới tạo (Open)</span>;
      case 'IN_PROGRESS':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-500/15 text-blue-300 border border-blue-500/30">Đang xử lý</span>;
      case 'WAITING':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-500/15 text-purple-300 border border-purple-500/30">Chờ phản hồi</span>;
      case 'RESOLVED':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">Đã giải quyết</span>;
      case 'CLOSED':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-700 text-slate-400">Đã đóng</span>;
      default:
        return <span>{status}</span>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'URGENT':
        return <span className="text-[10px] font-bold text-rose-400">Khẩn cấp</span>;
      case 'HIGH':
        return <span className="text-[10px] font-bold text-amber-400">Cao</span>;
      case 'MEDIUM':
        return <span className="text-[10px] font-medium text-blue-400">Trung bình</span>;
      default:
        return <span className="text-[10px] text-slate-400">Thấp</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-xs focus:outline-none"
          >
            <option value="">Tất cả trạng thái</option>
            <option value="OPEN">Mới tạo (Open)</option>
            <option value="IN_PROGRESS">Đang xử lý (In Progress)</option>
            <option value="WAITING">Chờ phản hồi (Waiting)</option>
            <option value="RESOLVED">Đã giải quyết (Resolved)</option>
            <option value="CLOSED">Đã đóng (Closed)</option>
          </select>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/25 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Tạo Ticket hỗ trợ mới</span>
        </button>
      </div>

      {/* Tickets List Table */}
      <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-5 py-3.5">Mã & Tiêu đề sự cố</th>
                <th className="px-5 py-3.5">Phân loại</th>
                <th className="px-5 py-3.5">Ưu tiên</th>
                <th className="px-5 py-3.5">Trạng thái</th>
                <th className="px-5 py-3.5">Người gửi</th>
                <th className="px-5 py-3.5">Phụ trách</th>
                <th className="px-5 py-3.5">Trao đổi</th>
                <th className="px-5 py-3.5 text-right">Chi tiết</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {tickets.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => loadTicketDetail(t.id)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-all"
                >
                  <td className="px-5 py-4">
                    <div className="font-mono text-[11px] text-indigo-400 font-semibold mb-0.5">{t.ticket_code}</div>
                    <div className="font-semibold text-white">{t.title}</div>
                  </td>
                  <td className="px-5 py-4 text-slate-300 font-medium">
                    {t.category}
                  </td>
                  <td className="px-5 py-4">
                    {getPriorityBadge(t.priority)}
                  </td>
                  <td className="px-5 py-4">
                    {getStatusBadge(t.status)}
                  </td>
                  <td className="px-5 py-4 text-slate-300">
                    {t.creator_full_name}
                  </td>
                  <td className="px-5 py-4 text-slate-400">
                    {t.assignee_full_name || <span className="italic text-slate-600">Chưa gán</span>}
                  </td>
                  <td className="px-5 py-4 text-slate-400">
                    <span className="inline-flex items-center gap-1">
                      <MessageSquare className="w-3 h-3" />
                      <span>{t.comment_count}</span>
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <ChevronRight className="w-4 h-4 text-slate-500 inline" />
                  </td>
                </tr>
              ))}

              {tickets.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-5 py-12 text-center text-slate-500 text-xs">
                    {loading ? 'Đang tải danh sách ticket...' : 'Chưa có yêu cầu hỗ trợ nào.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ticket Detail Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-panel w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl border border-slate-700 shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono font-bold text-xs text-indigo-400">{selectedTicket.ticket_code}</span>
                  {getStatusBadge(selectedTicket.status)}
                  <span className="text-xs text-slate-500">• {getPriorityBadge(selectedTicket.priority)}</span>
                </div>
                <h3 className="text-base font-bold text-white">{selectedTicket.title}</h3>
              </div>
              <button
                onClick={() => setSelectedTicket(null)}
                className="text-slate-400 hover:text-white text-xs px-2.5 py-1 rounded-lg bg-slate-800"
              >
                Đóng
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5">
              {/* Ticket Meta & Description */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-2">
                    <User className="w-3.5 h-3.5 text-slate-500" />
                    <span>Người yêu cầu: <strong className="text-white">{selectedTicket.creator_full_name}</strong></span>
                  </div>
                  <span>Ngày tạo: {new Date(selectedTicket.created_at).toLocaleString('vi-VN')}</span>
                </div>

                <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap pt-2 border-t border-slate-800/60">
                  {selectedTicket.description}
                </div>

                {selectedTicket.resolution_notes && (
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
                    <strong>Giải pháp khắc phục từ IT:</strong> {selectedTicket.resolution_notes}
                  </div>
                )}
              </div>

              {/* Admin Actions Bar */}
              {canManage && (
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-xs">
                    <Wrench className="w-4 h-4 text-blue-400" />
                    <span className="text-slate-400">Quản trị IT:</span>
                    {!selectedTicket.assigned_to && (
                      <button
                        onClick={handleAssignToMe}
                        className="px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-all"
                      >
                        Nhận phụ trách
                      </button>
                    )}
                    {selectedTicket.assignee_full_name && (
                      <span className="text-white font-medium">{selectedTicket.assignee_full_name}</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {selectedTicket.status !== 'IN_PROGRESS' && selectedTicket.status !== 'RESOLVED' && (
                      <button
                        onClick={() => handleStatusChange('IN_PROGRESS')}
                        className="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-semibold hover:bg-blue-500/30"
                      >
                        Chuyển Đang xử lý
                      </button>
                    )}
                    {selectedTicket.status !== 'RESOLVED' && (
                      <button
                        onClick={() => {
                          const notes = prompt('Nhập ghi chú giải pháp kỹ thuật đã xử lý:');
                          if (notes) {
                            setResolutionNotes(notes);
                            handleStatusChange('RESOLVED');
                          }
                        }}
                        className="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold hover:bg-emerald-500/30"
                      >
                        Hoàn thành & Giải quyết
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Comments Timeline */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Lịch sử trao đổi & Xử lý ({selectedTicket.comments?.length || 0})
                </h4>

                <div className="space-y-2.5">
                  {selectedTicket.comments?.map((c) => (
                    <div
                      key={c.id}
                      className={`p-3 rounded-xl border text-xs leading-relaxed ${
                        c.is_internal
                          ? 'bg-purple-950/30 border-purple-800/40 text-purple-200'
                          : 'bg-slate-900/60 border-slate-800 text-slate-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1 text-[11px]">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white">{c.user_full_name}</span>
                          <span className="text-slate-500">({c.user_role})</span>
                          {c.is_internal && (
                            <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-semibold">
                              <Lock className="w-2.5 h-2.5" /> Ghi chú nội bộ IT
                            </span>
                          )}
                        </div>
                        <span className="text-slate-500">{new Date(c.created_at).toLocaleTimeString('vi-VN')}</span>
                      </div>
                      <div>{c.content}</div>
                    </div>
                  ))}
                </div>

                {/* Post Comment Form */}
                <form onSubmit={handleAddComment} className="space-y-2 pt-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      placeholder="Nhập nội dung phản hồi trao đổi..."
                      className="flex-1 px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500 placeholder:text-slate-500"
                    />
                    <button
                      type="submit"
                      disabled={commenting || !commentText.trim()}
                      className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center gap-1.5 disabled:opacity-40"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>Gửi</span>
                    </button>
                  </div>

                  {canManage && (
                    <label className="flex items-center gap-2 text-xs text-purple-300 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={isInternalComment}
                        onChange={(e) => setIsInternalComment(e.target.checked)}
                        className="rounded border-slate-700 text-purple-600 focus:ring-purple-500"
                      />
                      <span>Đánh dấu là Ghi chú kỹ thuật nội bộ (Nhân viên không nhìn thấy)</span>
                    </label>
                  )}
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-panel w-full max-w-lg p-6 rounded-2xl border border-slate-700 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Ticket className="w-4 h-4 text-indigo-400" />
                <span>Gửi yêu cầu hỗ trợ IT Ticket</span>
              </h3>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  if (onClearInitialChat) onClearInitialChat();
                }}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg bg-slate-800"
              >
                Hủy
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Tiêu đề sự cố / yêu cầu</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Ví dụ: Máy tính không in được qua mạng LAN"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Phân loại sự cố</label>
                  <select
                    value={newCat}
                    onChange={(e) => setNewCat(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none"
                  >
                    <option value="GENERAL">Chung (General)</option>
                    <option value="NETWORK">Mạng / VPN / Wi-Fi</option>
                    <option value="HARDWARE">Phần cứng máy tính</option>
                    <option value="SOFTWARE">Phần mềm ứng dụng</option>
                    <option value="ACCOUNT">Tài khoản & Mật khẩu</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Mức độ ưu tiên</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none"
                  >
                    <option value="LOW">Thấp (Low)</option>
                    <option value="MEDIUM">Trung bình (Medium)</option>
                    <option value="HIGH">Cao (High)</option>
                    <option value="URGENT">Khẩn cấp (Urgent)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Mô tả chi tiết sự cố</label>
                <textarea
                  rows={4}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Mô tả hiện tượng, thông báo lỗi cụ thể..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* AI Auto-Triage Button */}
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={handleAutoTriage}
                  disabled={triageLoading}
                  className="w-full py-2 px-3 rounded-xl bg-gradient-to-r from-purple-600/20 to-indigo-600/20 hover:from-purple-600/30 hover:to-indigo-600/30 border border-purple-500/40 text-purple-300 text-xs font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 shadow-sm"
                >
                  {triageLoading ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
                      <span>AI đang phân tích sự cố...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                      <span>✨ AI Tự động phân loại & Gợi ý xử lý</span>
                    </>
                  )}
                </button>

                {triageResult && (
                  <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-xs space-y-1.5 animate-fadeIn">
                    <div className="flex items-center justify-between text-purple-300 font-bold text-[11px]">
                      <span className="flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                        AI Đề xuất: {triageResult.suggested_category} • Mức độ {triageResult.suggested_priority}
                      </span>
                    </div>
                    <p className="text-slate-300 text-[11px] leading-relaxed">{triageResult.reasoning}</p>
                    {triageResult.suggested_initial_actions?.length > 0 && (
                      <div className="pt-1 border-t border-purple-500/20 text-[11px]">
                        <span className="text-slate-400 font-semibold">Các bước nên thử trước:</span>
                        <ul className="list-disc list-inside mt-0.5 space-y-0.5 text-slate-300">
                          {triageResult.suggested_initial_actions.map((act: string, idx: number) => (
                            <li key={idx}>{act}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {initialChatSessionId && (
                <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-indigo-300 flex items-center gap-2">
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Ticket sẽ được tự động liên kết với phiên hỏi đáp AI hiện tại.</span>
                </div>
              )}

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={creating || !newTitle.trim() || !newDesc.trim()}
                  className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/25 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {creating ? 'Đang tạo...' : 'Gửi yêu cầu IT Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
