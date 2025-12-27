import React, { useState } from 'react';
import { Lock, User, Eye, EyeOff, Activity, ArrowRight } from 'lucide-react';

interface LoginProps {
  onLogin: (username: string, password: string) => void;
  loading?: boolean;
  error?: string;
}

const Login: React.FC<LoginProps> = ({ onLogin, loading = false, error }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin(username, password);
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center p-6 overflow-hidden bg-zinc-950">
      {/* Subtle Aesthetic Background */}
      <div className="absolute inset-0 z-0">
        <img
          src="/assets/login-bg.svg"
          alt=""
          className="w-full h-full object-cover opacity-40 grayscale"
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-zinc-950 via-transparent to-zinc-900/50"></div>
      </div>

      <div className="relative w-full max-w-sm mx-auto">
        <div className="bg-zinc-800/40 backdrop-blur-3xl p-10 rounded-[2.5rem] border border-white/10 shadow-3xl shadow-zinc-950/40 relative overflow-hidden group">
          <div className="absolute top-0 right-0 -mr-16 -mt-16 w-32 h-32 bg-zinc-700/20 rounded-full blur-3xl opacity-50 group-hover:opacity-75 transition-opacity duration-500"></div>
          <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-32 h-32 bg-zinc-700/10 rounded-full blur-3xl opacity-30 group-hover:opacity-50 transition-opacity duration-500"></div>
          <div className="relative z-10">
            <div className="text-center mb-10">
              <div className="mx-auto w-16 h-16 mb-6">
                <div className="w-full h-full bg-zinc-900 rounded-xl p-2 border border-zinc-700 flex items-center justify-center overflow-hidden">
                  <img
                    src="/logo.jpg"
                    alt="Metronavix Logo"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
              <h1 className="text-[10px] font-black uppercase tracking-[0.4em] text-zinc-500 mb-1">
                Internal Access
              </h1>
              <h2 className="text-3xl font-black text-white tracking-tighter drop-shadow-sm">
                Metronavix <span className="text-zinc-400">OS</span>
              </h2>
            </div>

            {error && (
              <div className="mb-8 p-4 bg-red-900/20 border border-red-800/50 text-red-300 text-[10px] font-bold uppercase tracking-wider text-center rounded-lg">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="username" className="block text-[10px] font-black uppercase tracking-[0.2em] text-zinc-300 mb-2.5 ml-0.5">
                  Username
                </label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <User size={16} className="text-zinc-400 group-focus-within:text-zinc-300 transition-colors" />
                  </div>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-11 pr-4 py-3.5 bg-zinc-800/50 border border-zinc-700/50 rounded-xl text-sm font-medium text-white focus:bg-zinc-800 focus:border-white/20 focus:ring-0 outline-none transition-all placeholder:text-zinc-500 drop-shadow-sm"
                    placeholder="Enter system username"
                    required
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-[10px] font-black uppercase tracking-[0.2em] text-zinc-300 mb-2.5 ml-0.5">
                  Password
                </label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock size={16} className="text-zinc-400 group-focus-within:text-zinc-300 transition-colors" />
                  </div>
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-11 pr-12 py-3.5 bg-zinc-800/50 border border-zinc-700/50 rounded-xl text-sm font-medium text-white focus:bg-zinc-800 focus:border-white/20 focus:ring-0 outline-none transition-all placeholder:text-zinc-500 drop-shadow-sm"
                    placeholder="Enter security password"
                    required
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-zinc-400 hover:text-white transition-colors"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="flex items-center pt-2">
                <label className="flex items-center cursor-pointer group">
                  <input
                    type="checkbox"
                    className="w-4 h-4 bg-zinc-800 border-zinc-700 rounded text-white focus:ring-white transition-all cursor-pointer"
                  />
                  <span className="ml-3 text-[10px] font-bold uppercase tracking-widest text-zinc-500 group-hover:text-white transition-colors drop-shadow-sm">Remember this session</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-white hover:bg-zinc-200 text-zinc-900 py-4 rounded-xl font-black uppercase tracking-[0.2em] text-[10px] flex items-center justify-center gap-3 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-xl shadow-white/5"
              >
                {loading ? (
                  <>
                    <Activity size={16} className="animate-spin" />
                    Authenticating...
                  </>
                ) : (
                  <>
                    Authenticate
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        <div className="mt-12 text-center">
          <p className="text-[9px] text-zinc-400 font-bold uppercase tracking-[0.5em] opacity-40">
            METRONAVIX SECURITY v4.0.1
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;