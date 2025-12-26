import React, { useState } from 'react';
import { Lock, User, Eye, EyeOff } from 'lucide-react';

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
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <div className="mx-auto w-16 h-16 bg-black flex items-center justify-center rounded-lg">
            <span className="text-white font-black text-2xl">EV</span>
          </div>
          <h1 className="text-2xl font-black uppercase tracking-tighter mt-4">EstateVision AI</h1>
          <p className="text-zinc-500 text-sm mt-2">Property Video Generation Platform</p>
        </div>

        <div className="bg-white border border-zinc-200 p-8 shadow-sm">
          <h2 className="text-xl font-black uppercase tracking-widest text-center mb-8">Access Portal</h2>
          
          {error && (
            <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label htmlFor="username" className="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User size={16} className="text-zinc-400" />
                </div>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-zinc-200 text-sm focus:border-black focus:ring-0 outline-none transition-all bg-zinc-50"
                  placeholder="Enter your username"
                  required
                />
              </div>
            </div>
            
            <div className="mb-6">
              <label htmlFor="password" className="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock size={16} className="text-zinc-400" />
                </div>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 border border-zinc-200 text-sm focus:border-black focus:ring-0 outline-none transition-all bg-zinc-50"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff size={16} className="text-zinc-400 hover:text-zinc-600" />
                  ) : (
                    <Eye size={16} className="text-zinc-400 hover:text-zinc-600" />
                  )}
                </button>
              </div>
            </div>
            
            <div className="flex items-center justify-between mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="h-4 w-4 text-black focus:ring-black border-zinc-300 rounded"
                />
                <span className="ml-2 text-sm text-zinc-600">Remember me</span>
              </label>
              <a href="#" className="text-sm text-black hover:underline font-medium">
                Forgot password?
              </a>
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3 px-4 text-white font-black uppercase tracking-widest text-sm rounded transition-all ${
                loading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-black hover:bg-zinc-800 active:scale-[0.98]'
              }`}
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>
          
          <div className="mt-8 text-center">
            <p className="text-sm text-zinc-600">
              Don't have an account?{' '}
              <a href="#" className="text-black font-medium hover:underline">
                Request Access
              </a>
            </p>
          </div>
        </div>
        
        <div className="mt-8 text-center">
          <p className="text-xs text-zinc-500 uppercase tracking-widest">
            © {new Date().getFullYear()} EstateVision AI. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;