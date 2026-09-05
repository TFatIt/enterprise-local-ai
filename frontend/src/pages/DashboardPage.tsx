import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  MessageSquare, 
  Ticket, 
  CheckCircle2, 
  Clock, 
  TrendingUp, 
  Activity,
  AlertTriangle,
  FileQuestion,
  UploadCloud,
  Search,
  BookOpen,
  ArrowRight,
  ShieldAlert,
  BarChart3
} from 'lucide-react';
import { api } from '../api/client';
import type { DashboardAnalytics, KnowledgeGapResponse, KnowledgeGapItem } from '../types';

interface DashboardPageProps {
  onNavigateDocuments?: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigateDocuments }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'knowledge_gaps'>('overview');
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [gapsData, setGapsData] = useState<KnowledgeGapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [gapSearch, setGapSearch] = useState('');
  const [gapDeptFilter, setGapDeptFilter] = useState('ALL');

  useEffect(() => {
    const loadAll = async () => {
      try {
        const [statsResp, gapsResp] = await Promise.all([
          api.get<DashboardAnalytics>('/dashboard/stats'),
          api.get<KnowledgeGapResponse>('/dashboard/knowledge-gaps')
        ]);
        setData(statsResp.data);
        setGapsData(gapsResp.data);
      } catch (err) {
        console.error('Failed to load dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };
    loadAll();
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center text-xs text-slate-400 gap-2 min-h-[400px]">
        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <span>Đang tổng hợp dữ liệu phân tích hệ thống & khoảng trống tri thức...</span>
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

  const filteredGaps = (gapsData?.items || []).filter((gap: KnowledgeGapItem) => {
    const matchesDept = gapDeptFilter === 'ALL' || gap.department_code === gapDeptFilter;
    const matchesSearch = 
      gap.topic.toLowerCase().includes(gapSearch.toLowerCase()) ||
      gap.sample_query.toLowerCase().includes(gapSearch.toLowerCase()) ||
      gap.department_name.toLowerCase().includes(gapSearch.toLowerCase());
    return matchesDept && matchesSearch;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header & Tab Selector Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
            <span>Trung tâm Điều hành & Quản trị Doanh nghiệp</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Giám sát hiệu suất trợ lý AI, Helpdesk Support, và khoảng trống tài liệu nội bộ
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'overview'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Tổng quan Vận hành</span>
          </button>

          <button
            onClick={() => setActiveTab('knowledge_gaps')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all relative ${
              activeTab === 'knowledge_gaps'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <FileQuestion className="w-3.5 h-3.5 text-amber-400" />
            <span>Khoảng trống Tri thức</span>
            {gapsData && gapsData.open_gaps > 0 && (
              <span className="px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
                {gapsData.open_gaps}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ================= VIEW 1: OVERVIEW TAB ================= */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
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
      )}

      {/* ================= VIEW 2: KNOWLEDGE GAP ANALYTICS TAB ================= */}
      {activeTab === 'knowledge_gaps' && gapsData && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Executive Alert Banner */}
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-300 flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">
                  Phát hiện {gapsData.open_gaps} Khoảng trống Tri thức Cần Bổ sung Tài liệu
                </h2>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  Hệ thống tự động phát hiện các câu hỏi nhân viên tra cứu nhưng AI chưa thể giải đáp do thiếu tài liệu quy chuẩn.
                  Bổ sung các tài liệu hướng dẫn (SOP) bên dưới sẽ trực tiếp nâng cao tỷ lệ tự phục vụ (AI Resolution Rate).
                </p>
              </div>
            </div>

            <button
              onClick={() => onNavigateDocuments?.()}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shrink-0 shadow-lg shadow-indigo-600/30 transition-all"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Nạp tài liệu mới ngay</span>
            </button>
          </div>

          {/* Metric Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Tổng chủ đề phát hiện</span>
                <BookOpen className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-3xl font-extrabold text-white tracking-tight">{gapsData.total_gaps}</div>
              <p className="text-[11px] text-slate-400 mt-1">Các nhóm câu hỏi nhân viên quan tâm</p>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-rose-500/30 bg-rose-500/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-rose-400 uppercase tracking-wider">Chưa có văn bản quy định</span>
                <ShieldAlert className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-3xl font-extrabold text-rose-300 tracking-tight">{gapsData.open_gaps}</div>
              <p className="text-[11px] text-rose-300/80 mt-1">Cần phòng ban biên soạn nạp lên RAG</p>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-emerald-500/30 bg-emerald-500/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Đã có tài liệu bao phủ</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-3xl font-extrabold text-emerald-300 tracking-tight">{gapsData.resolved_gaps}</div>
              <p className="text-[11px] text-emerald-300/80 mt-1">Đã có tài liệu hướng dẫn trong hệ thống</p>
            </div>
          </div>

          {/* Filtering and Search Controls */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Tìm kiếm khoảng trống tri thức..."
                value={gapSearch}
                onChange={(e) => setGapSearch(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
              {['ALL', 'HR', 'IT', 'ACC', 'GEN'].map((dept) => (
                <button
                  key={dept}
                  onClick={() => setGapDeptFilter(dept)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all shrink-0 ${
                    gapDeptFilter === dept
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800/60 text-slate-400 hover:text-white'
                  }`}
                >
                  {dept === 'ALL' ? 'Tất cả phòng ban' : dept}
                </button>
              ))}
            </div>
          </div>

          {/* Knowledge Gaps Data Table */}
          <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/50 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    <th className="py-3.5 px-4">Chủ đề & Câu hỏi thực tế của nhân viên</th>
                    <th className="py-3.5 px-4">Phòng ban</th>
                    <th className="py-3.5 px-4 text-center">Tần suất hỏi</th>
                    <th className="py-3.5 px-4">Trạng thái</th>
                    <th className="py-3.5 px-4">Đề xuất bổ sung tài liệu</th>
                    <th className="py-3.5 px-4 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs">
                  {filteredGaps.map((item: KnowledgeGapItem) => {
                    const isResolved = item.status === 'RESOLVED';
                    const deptColor = 
                      item.department_code === 'HR' ? 'bg-purple-500/10 text-purple-400 border-purple-500/30' :
                      item.department_code === 'IT' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' :
                      item.department_code === 'ACC' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                      'bg-slate-500/10 text-slate-400 border-slate-500/30';

                    return (
                      <tr key={item.id} className="hover:bg-slate-800/40 transition-colors group">
                        {/* Topic & Query */}
                        <td className="py-4 px-4 max-w-sm">
                          <div className="font-semibold text-white group-hover:text-indigo-300 transition-colors">
                            {item.topic}
                          </div>
                          <div className="text-[11px] text-slate-400 italic mt-1 line-clamp-2">
                            "{item.sample_query}"
                          </div>
                          <div className="text-[10px] text-slate-500 mt-1 font-mono">
                            Hỏi lần cuối: {item.last_queried_at}
                          </div>
                        </td>

                        {/* Department */}
                        <td className="py-4 px-4 whitespace-nowrap">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${deptColor}`}>
                            {item.department_name}
                          </span>
                        </td>

                        {/* Frequency */}
                        <td className="py-4 px-4 text-center whitespace-nowrap">
                          <div className="inline-flex flex-col items-center">
                            <span className="font-extrabold text-white text-sm">
                              {item.query_count}
                            </span>
                            <span className="text-[10px] text-slate-400">lượt tra cứu</span>
                          </div>
                        </td>

                        {/* Status */}
                        <td className="py-4 px-4 whitespace-nowrap">
                          {isResolved ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>Đã có tài liệu</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 animate-pulse">
                              <AlertTriangle className="w-3 h-3" />
                              <span>Chưa có tài liệu</span>
                            </span>
                          )}
                        </td>

                        {/* Suggested Action */}
                        <td className="py-4 px-4 max-w-xs">
                          <div className="text-slate-300 text-[11px] leading-relaxed">
                            {item.suggested_action}
                          </div>
                        </td>

                        {/* Action */}
                        <td className="py-4 px-4 text-right whitespace-nowrap">
                          <button
                            onClick={() => onNavigateDocuments?.()}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold transition-all shadow-sm"
                          >
                            <span>Bổ sung</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}

                  {filteredGaps.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-xs text-slate-500">
                        Không tìm thấy khoảng trống tri thức phù hợp với tiêu chí lọc.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
