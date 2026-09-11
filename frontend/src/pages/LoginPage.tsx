import React, { useState } from 'react';
import { Bot, Shield, Wrench, UserCheck, AlertCircle, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await login(username, password);
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(typeof err.response.data.detail === 'string' ? err.response.data.detail : JSON.stringify(err.response.data.detail));
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('Máy chủ phản hồi quá lâu (Timeout). Vui lòng kiểm tra lại kết nối Backend.');
      } else if (err.message === 'Network Error' || !err.response) {
        setError('Không thể kết nối đến máy chủ Backend (Port 8000). Vui lòng kiểm tra xem Backend đã khởi động chưa.');
      } else {
        setError('Đăng nhập thất bại. Vui lòng kiểm tra lại tài khoản.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setLoading(true);
    setError(null);
    try {
      await login(u, p);
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(typeof err.response.data.detail === 'string' ? err.response.data.detail : JSON.stringify(err.response.data.detail));
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('Máy chủ phản hồi quá lâu (Timeout). Vui lòng kiểm tra lại kết nối Backend.');
      } else if (err.message === 'Network Error' || !err.response) {
        setError('Không thể kết nối đến máy chủ Backend (Port 8000). Vui lòng kiểm tra xem Backend đã khởi động chưa.');
      } else {
        setError('Đăng nhập nhanh thất bại. Vui lòng thử lại.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070a13] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background glowing orbs */}
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo and Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-xl shadow-indigo-500/25 mb-4">
            <div className="w-full h-full bg-slate-950 rounded-2xl flex items-center justify-center">
              <Bot className="w-8 h-8 text-cyan-400" />
            </div>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Local AI Nội bộ doanh nghiệp</h1>
          <p className="text-xs text-slate-400 mt-1">Trợ lý Trí tuệ Nhân tạo & Hỗ trợ Kỹ thuật CNTT Nội bộ</p>
        </div>

        {/* Login Card */}
        <div className="glass-panel p-6 sm:p-8 rounded-2xl shadow-2xl border border-slate-800/80">
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center gap-2.5 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Tên đăng nhập hoặc Email</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="superadmin, itadmin, employee..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700/80 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-slate-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Mật khẩu</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700/80 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-slate-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <>
                  <span>Đăng nhập hệ thống</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-8 pt-6 border-t border-slate-800/80">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-cyan-400" />
                Đăng nhập nhanh demo (Đồ án)
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('superadmin', 'Admin@123456')}
                className="p-2 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-[11px] font-semibold text-purple-300 flex flex-col items-center gap-1 transition-all"
              >
                <Shield className="w-4 h-4 text-purple-400" />
                <span>Super Admin</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('itadmin', 'Admin@123456')}
                className="p-2 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-[11px] font-semibold text-blue-300 flex flex-col items-center gap-1 transition-all"
              >
                <Wrench className="w-4 h-4 text-blue-400" />
                <span>IT Admin</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('employee', 'Employee@123456')}
                className="p-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-[11px] font-semibold text-emerald-300 flex flex-col items-center gap-1 transition-all"
              >
                <UserCheck className="w-4 h-4 text-emerald-400" />
                <span>Nhân viên</span>
              </button>
            </div>
          </div>
        </div>

        {/* Local AI Assurance */}
        <div className="mt-6 text-center text-[11px] text-slate-500">
          Hệ thống chạy 100% Offline với Ollama Qwen 2.5 3B & ChromaDB. Bảo mật dữ liệu nội bộ.
        </div>
      </div>
    </div>
  );
};
