import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  MessageSquare, 
  Ticket, 
  CheckCircle2, 
  Clock, 
  TrendingUp, 
  Activity 
} from 'lucide-react';
import { api } from '../api/client';
import type { DashboardAnalytics } from '../types';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const resp = await api.get<DashboardAnalytics>('/dashboard/stats');
        setData(resp.data);
      } catch (err) {
        console.error('Failed to load dashboard stats', err);
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center text-xs text-slate-400 gap-2">
        <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
        <span>Đang tổng hợp dữ liệu phân tích hệ thống...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-xs text-rose-400">
        Không thể tải dữ liệu Dashboard. Vui lòng kiểm tra quyền hạn tài khoản.
      </div>
    );
  }

  const { summary, tickets_by_category, tickets_by_status, recent_activities } = data;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: AI Resolution Rate */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-emerald-500"></div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">AI Resolution Rate</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">{summary.ai_resolution_rate}%</div>
          <p className="text-[11px] text-slate-400 mt-1">Tỷ lệ câu hỏi AI tự giải quyết thành công</p>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full rounded-full transition-all duration-1000"
              style={{ width: `${summary.ai_resolution_rate}%` }}
            ></div>
          </div>
        </div>

        {/* Card 2: Total Questions */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-indigo-500"></div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Câu hỏi đã phục vụ</span>
            <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">{summary.total_questions}</div>
          <p className="text-[11px] text-slate-400 mt-1">Trong {summary.total_chat_sessions} phiên hội thoại AI</p>
        </div>

        {/* Card 3: IT Tickets */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-amber-500"></div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Sự cố IT Support</span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Ticket className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight flex items-baseline gap-2">
            <span>{summary.total_tickets}</span>
            <span className="text-xs font-medium text-emerald-400">({summary.resolved_tickets} đã xử lý)</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">{summary.open_tickets} ticket đang chờ giải quyết</p>
        </div>

        {/* Card 4: Knowledge Base Size */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-cyan-500"></div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Cơ sở Tri thức</span>
            <div className="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight flex items-baseline gap-2">
            <span>{summary.total_chunks}</span>
            <span className="text-xs font-normal text-slate-400">chunks</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">{summary.total_documents} tài liệu nội bộ đã số hóa</p>
        </div>
      </div>

      {/* Analytics Breakdown Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ticket Categories */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-400" />
            <span>Phân bố sự cố IT theo Danh mục</span>
          </h3>

          <div className="space-y-3 pt-2">
            {tickets_by_category.map((cat) => {
              const pct = summary.total_tickets > 0 ? Math.round((cat.count / summary.total_tickets) * 100) : 0;
              return (
                <div key={cat.category} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-300">{cat.category}</span>
                    <span className="text-slate-400">{cat.count} tickets ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-800/80 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full rounded-full transition-all duration-700"
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}

            {tickets_by_category.length === 0 && (
              <div className="text-center py-6 text-xs text-slate-500">Chưa có dữ liệu sự cố</div>
            )}
          </div>
        </div>

        {/* Ticket Statuses */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Tình trạng giải quyết Ticket</span>
          </h3>

          <div className="space-y-3 pt-2">
            {tickets_by_status.map((st) => {
              const pct = summary.total_tickets > 0 ? Math.round((st.count / summary.total_tickets) * 100) : 0;
              return (
                <div key={st.status} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-300">{st.status}</span>
                    <span className="text-slate-400">{st.count} tickets ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-800/80 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all duration-700"
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}

            {tickets_by_status.length === 0 && (
              <div className="text-center py-6 text-xs text-slate-500">Chưa có dữ liệu trạng thái</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activities Timeline */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span>Nhật ký hoạt động gần nhất trên hệ thống</span>
        </h3>

        <div className="divide-y divide-slate-800/60">
          {recent_activities.map((act, idx) => (
            <div key={idx} className="py-3 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className={`w-2 h-2 rounded-full ${act.type === 'TICKET' ? 'bg-amber-400' : 'bg-indigo-400'}`}></span>
                <div>
                  <span className="font-semibold text-white">{act.title}</span>
                  <span className="text-slate-400 text-[11px] ml-2">bởi {act.user_name}</span>
                </div>
              </div>
              <span className="text-slate-500 text-[11px] font-mono">
                {new Date(act.created_at).toLocaleString('vi-VN')}
              </span>
            </div>
          ))}

          {recent_activities.length === 0 && (
            <div className="text-center py-6 text-xs text-slate-500">Chưa có hoạt động nào được ghi nhận</div>
          )}
        </div>
      </div>
    </div>
  );
};
