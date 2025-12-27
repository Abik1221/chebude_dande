import React, { ReactNode } from 'react';
import {
  Home,
  Settings,
  Play,
  HelpCircle,
  User,
  LogOut,
  CreditCard
} from 'lucide-react';
import { AppView, User as UserType } from '../types';

interface LayoutProps {
  children: ReactNode;
  currentView: AppView;
  setView: (view: AppView) => void;
  user: UserType;
  onLogout: () => void;
}

const Layout: React.FC<LayoutProps> = ({
  children,
  currentView,
  setView,
  user,
  onLogout
}) => {
  return (
    <div className="min-h-screen bg-[#F9FAFB] flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="bg-white/80 backdrop-blur-md border-b border-zinc-100 px-8 py-5 sticky top-0 z-50">
        <div className="flex items-center justify-between max-w-[1600px] mx-auto">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 relative">
              <div className="absolute inset-0 bg-zinc-100 rounded-xl rotate-3"></div>
              <div className="relative w-full h-full bg-white rounded-xl shadow-sm border border-zinc-100 flex items-center justify-center overflow-hidden p-1.5">
                <img src="/logo.jpg" alt="Metronavix" className="w-full h-full object-contain" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-black uppercase tracking-tight text-zinc-900 leading-none">Metronavix</h1>
              <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mt-1">Property Video Engine</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 bg-zinc-50 border border-zinc-100 px-4 py-2 rounded-2xl text-[10px] font-black uppercase tracking-widest text-zinc-600">
              <CreditCard size={12} className="text-zinc-400" />
              <span>{user.credits} Credits Available</span>
            </div>

            <div className="h-8 w-px bg-zinc-100 mx-2"></div>

            <div className="flex items-center gap-3 group cursor-pointer">
              <div className="text-right">
                <p className="text-[11px] font-black uppercase tracking-tighter text-zinc-900">{user.name}</p>
                <p className="text-[9px] text-zinc-400 font-medium">{user.company}</p>
              </div>
              <div className="w-10 h-10 bg-zinc-900 flex items-center justify-center text-white text-xs font-black rounded-2xl shadow-lg shadow-zinc-200">
                {user.name.charAt(0)}
              </div>
            </div>

            <button
              onClick={onLogout}
              className="p-2.5 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-2xl transition-all"
              title="Terminate Session"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 max-w-[1600px] mx-auto w-full">
        {/* Sidebar - Desktop */}
        <aside className="hidden lg:flex w-72 flex-col bg-zinc-900 border-r border-white/5 relative z-20 group">
          <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent pointer-events-none"></div>

          <div className="p-8 flex items-center gap-4 relative">
            <div className="w-10 h-10 bg-zinc-800 rounded-2xl flex items-center justify-center p-2 border border-white/10 shadow-lg shadow-zinc-900/20 group-hover:scale-105 transition-transform">
              <img src="/logo.jpg" alt="Logo" className="w-full h-full object-contain" />
            </div>
            <span className="text-lg font-black tracking-tighter text-zinc-50 uppercase">Metronavix</span>
          </div>

          <nav className="flex-1 px-6 py-8 space-y-4 relative">
            {[
              { view: AppView.DASHBOARD, icon: Home, label: 'Hub' },
              { view: AppView.GENERATE, icon: Play, label: 'Create' },
              { view: AppView.SETTINGS, icon: Settings, label: 'Config' },
              { view: AppView.HELP, icon: HelpCircle, label: 'Support' }
            ].map((item) => (
              <button
                key={item.view}
                onClick={() => setView(item.view)}
                className={`group flex items-center gap-3 px-4 py-3 rounded-xl text-[11px] font-black uppercase tracking-[0.2em] transition-all duration-300 w-full ${currentView === item.view
                  ? 'bg-white text-zinc-900 shadow-xl shadow-white/5'
                  : 'text-zinc-500 hover:text-zinc-50 hover:bg-white/5'
                  }`}
                title={item.label}
              >
                <item.icon size={22} />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-10 pb-20 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;