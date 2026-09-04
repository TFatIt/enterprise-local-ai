import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, 
  User, 
  Send, 
  Plus, 
  Trash2, 
  Clock, 
  FileText, 
  AlertTriangle, 
  Ticket, 
  Sparkles 
} from 'lucide-react';
import { api } from '../api/client';
import type { ChatSession, ChatMessage, SourceItem } from '../types';

interface ChatPageProps {
  onOpenTicketWithChat?: (sessionId: string, initialText: string) => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({ onOpenTicketWithChat }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeCitation, setActiveCitation] = useState<SourceItem | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load user chat sessions
  const loadSessions = async () => {
    try {
      const resp = await api.get<ChatSession[]>('/chat/sessions');
      setSessions(resp.data);
      if (resp.data.length > 0 && !currentSessionId) {
        setCurrentSessionId(resp.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load sessions', err);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  // Load messages for current session
  useEffect(() => {
    if (!currentSessionId) {
      setMessages([]);
      return;
    }

    const loadMessages = async () => {
      try {
        const resp = await api.get<ChatMessage[]>(`/chat/sessions/${currentSessionId}/messages`);
        setMessages(resp.data);
      } catch (err) {
        console.error('Failed to load messages', err);
      }
    };
    loadMessages();
  }, [currentSessionId]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleCreateSession = async () => {
    try {
      const resp = await api.post<ChatSession>('/chat/sessions', { title: 'Cuộc hội thoại mới' });
      setSessions([resp.data, ...sessions]);
      setCurrentSessionId(resp.data.id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create session', err);
    }
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/chat/sessions/${sessionId}`);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (currentSessionId === sessionId) {
        setCurrentSessionId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err) {
      console.error('Failed to delete session', err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuestion.trim() || loading) return;

    let targetSessionId = currentSessionId;
    if (!targetSessionId) {
      try {
        const newSess = await api.post<ChatSession>('/chat/sessions', { title: 'Cuộc hội thoại mới' });
        targetSessionId = newSess.data.id;
        setSessions([newSess.data, ...sessions]);
        setCurrentSessionId(newSess.data.id);
      } catch {
        return;
      }
    }

    const userText = inputQuestion.trim();
    setInputQuestion('');

    // Optimistic user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: targetSessionId || '',
      sender_type: 'USER',
      content: userText,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    // Optimistic assistant placeholder
    const assistantTempId = `assistant-temp-${Date.now()}`;
    const tempAssistantMsg: ChatMessage = {
      id: assistantTempId,
      session_id: targetSessionId || '',
      sender_type: 'ASSISTANT',
      content: '',
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempAssistantMsg]);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/chat/sessions/${targetSessionId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content: userText }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Failed to start stream');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedAnswer = '';
      let sources: SourceItem[] = [];
      let suggestTicket = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === 'metadata') {
                sources = event.sources || [];
                suggestTicket = event.suggest_ticket || false;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantTempId ? { ...m, sources, suggest_ticket: suggestTicket } : m
                  )
                );
              } else if (event.type === 'token') {
                accumulatedAnswer += event.token;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantTempId ? { ...m, content: accumulatedAnswer } : m
                  )
                );
              } else if (event.type === 'done') {
                const responseTimeMs = event.response_time_ms || 0;
                suggestTicket = event.suggest_ticket ?? suggestTicket;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantTempId
                      ? {
                          ...m,
                          content: event.full_answer || accumulatedAnswer,
                          sources: event.sources || sources,
                          response_time_ms: responseTimeMs,
                          suggest_ticket: suggestTicket,
                        }
                      : m
                  )
                );
              }
            } catch {
              // ignore parse errors
            }
          }
        }
      }
      loadSessions(); // refresh title if auto-updated
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantTempId
            ? {
                ...m,
                content: 'Đã xảy ra lỗi khi kết nối tới Local LLM (Ollama). Vui lòng thử lại.',
                suggest_ticket: true,
              }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Session History Sidebar */}
      <div className="w-72 bg-slate-900/80 border-r border-slate-800/80 flex flex-col justify-between">
        <div className="p-3">
          <button
            onClick={handleCreateSession}
            className="w-full py-2.5 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Đoạn hội thoại mới</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => setCurrentSessionId(s.id)}
              className={`group w-full p-2.5 rounded-xl cursor-pointer flex items-center justify-between text-xs transition-all ${
                currentSessionId === s.id
                  ? 'bg-slate-800 border border-slate-700 text-white font-semibold'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-2.5 truncate max-w-[190px]">
                <Sparkles className={`w-3.5 h-3.5 shrink-0 ${currentSessionId === s.id ? 'text-indigo-400' : 'text-slate-500'}`} />
                <span className="truncate">{s.title}</span>
              </div>
              <button
                onClick={(e) => handleDeleteSession(s.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 rounded transition-all"
                title="Xóa phiên"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}

          {sessions.length === 0 && (
            <div className="text-center py-8 text-xs text-slate-500">
              Chưa có phiên hội thoại nào
            </div>
          )}
        </div>

        <div className="p-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
          <span>{sessions.length} phiên đã lưu</span>
          <span className="text-indigo-400 font-medium">Qwen 2.5 3B</span>
        </div>
      </div>

      {/* Main Chat Stream */}
      <div className="flex-1 flex flex-col bg-[#0b0f19] relative">
        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto">
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
                <Bot className="w-7 h-7" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">Tôi có thể giúp gì cho công việc của bạn?</h3>
              <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                Tra cứu nhanh quy định nội bộ, hướng dẫn cấu hình VPN từ xa, kết nối máy in, lỗi gia nhập Domain Active Directory, chính sách mật khẩu và hơn thế nữa.
              </p>

              <div className="grid grid-cols-2 gap-2.5 w-full text-left">
                <button
                  onClick={() => setInputQuestion('Làm thế nào để kết nối mạng VPN làm việc từ xa của công ty?')}
                  className="p-3 rounded-xl bg-slate-800/40 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-300 transition-all"
                >
                  🌐 Cấu hình VPN OpenVPN/WireGuard
                </button>
                <button
                  onClick={() => setInputQuestion('Mật khẩu tài khoản nhân viên quy định tối thiểu bao nhiêu ký tự và bao lâu đổi một lần?')}
                  className="p-3 rounded-xl bg-slate-800/40 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-300 transition-all"
                >
                  🔒 Quy định đổi mật khẩu định kỳ
                </button>
                <button
                  onClick={() => setInputQuestion('Địa chỉ IP máy chủ Domain Controller để cấu hình DNS là gì?')}
                  className="p-3 rounded-xl bg-slate-800/40 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-300 transition-all"
                >
                  🏢 DNS gia nhập Active Directory
                </button>
                <button
                  onClick={() => setInputQuestion('Địa chỉ IP và hướng dẫn cài đặt máy in văn phòng tầng 3 là gì?')}
                  className="p-3 rounded-xl bg-slate-800/40 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-300 transition-all"
                >
                  🖨️ Cài đặt máy in HP tầng 3
                </button>
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={`flex gap-3.5 ${m.sender_type === 'USER' ? 'justify-end' : 'justify-start'}`}>
              {m.sender_type !== 'USER' && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shrink-0 shadow-md shadow-indigo-500/20">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}

              <div className={`max-w-2xl space-y-2.5 ${m.sender_type === 'USER' ? 'items-end' : 'items-start'}`}>
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    m.sender_type === 'USER'
                      ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/20'
                      : 'glass-panel text-slate-200 rounded-bl-none border border-slate-800'
                  }`}
                >
                  {m.content}
                  {loading && m.id.startsWith('assistant-temp-') && (
                    <span className="inline-block w-2 h-4 bg-cyan-400 ml-1 animate-pulse align-middle"></span>
                  )}
                  {!m.content && loading && m.id.startsWith('assistant-temp-') && (
                    <span className="text-xs text-slate-400 italic flex items-center gap-2">
                      <span className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></span>
                      Đang tra cứu tri thức & sinh câu trả lời thời gian thực...
                    </span>
                  )}
                </div>

                {/* Meta details for Assistant response */}
                {m.sender_type === 'ASSISTANT' && (
                  <div className="space-y-2">
                    {/* Latency badge */}
                    {m.response_time_ms && (
                      <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>Phản hồi trong {(m.response_time_ms / 1000).toFixed(2)}s • Qwen 2.5 3B</span>
                      </div>
                    )}

                    {/* Citations Badges */}
                    {m.sources && m.sources.length > 0 && (
                      <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                          <FileText className="w-3 h-3 text-cyan-400" />
                          Nguồn trích dẫn kiểm chứng:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {m.sources.map((src) => (
                            <button
                              key={src.source_index}
                              onClick={() => setActiveCitation(src)}
                              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700/60 text-xs text-cyan-300 font-medium flex items-center gap-1.5 transition-all"
                            >
                              <span>[{src.source_index}] {src.document_title}</span>
                              <span className="text-[10px] text-slate-400">({Math.round(src.similarity_score * 100)}%)</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Escalate to IT Ticket Banner */}
                    {m.suggest_ticket && (
                      <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-3 text-xs">
                        <div className="flex items-center gap-2 text-amber-300">
                          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                          <span>Thông tin chưa có trong tài liệu nội bộ. Bạn có muốn gửi yêu cầu cho IT Admin hỗ trợ trực tiếp?</span>
                        </div>
                        {onOpenTicketWithChat && (
                          <button
                            onClick={() => onOpenTicketWithChat(m.session_id, messages[messages.length - 2]?.content || '')}
                            className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shrink-0 flex items-center gap-1.5 shadow-md shadow-amber-500/20 transition-all"
                          >
                            <Ticket className="w-3.5 h-3.5" />
                            <span>Tạo IT Ticket</span>
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {m.sender_type === 'USER' && (
                <div className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
                  <User className="w-4 h-4 text-slate-300" />
                </div>
              )}
            </div>
          ))}

          {loading && !messages.some((m) => m.id.startsWith('assistant-temp-')) && (
            <div className="flex gap-3.5 items-start">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="glass-panel p-3.5 rounded-2xl rounded-bl-none border border-slate-800 flex items-center gap-2.5 text-xs text-slate-300">
                <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
                <span>Đang truy hồi tri thức và suy luận câu trả lời...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-slate-900/80 border-t border-slate-800/80">
          <form onSubmit={handleSendMessage} className="flex gap-2.5 max-w-4xl mx-auto">
            <input
              type="text"
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              placeholder="Đặt câu hỏi về quy trình, kỹ thuật IT nội bộ..."
              disabled={loading}
              className="flex-1 px-4 py-3 rounded-xl bg-slate-950/80 border border-slate-700/80 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-slate-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !inputQuestion.trim()}
              className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all disabled:opacity-40"
            >
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Gửi</span>
            </button>
          </form>
        </div>
      </div>

      {/* Citation Snippet Modal Drawer */}
      {activeCitation && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-panel w-full max-w-lg p-6 rounded-2xl border border-slate-700 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
                <FileText className="w-4 h-4" />
                <span>Nguồn trích dẫn [{activeCitation.source_index}]</span>
              </div>
              <button
                onClick={() => setActiveCitation(null)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg bg-slate-800"
              >
                Đóng
              </button>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-white mb-1">{activeCitation.document_title}</h4>
              <p className="text-xs text-slate-400">File: {activeCitation.file_name} • Trang: {activeCitation.page_number} • Điểm tương đồng: {Math.round(activeCitation.similarity_score * 100)}%</p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed max-h-60 overflow-y-auto">
              {activeCitation.snippet}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
