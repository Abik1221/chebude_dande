
import React from 'react';
import { 
  LayoutDashboard, 
  Video, 
  Settings, 
  HelpCircle, 
  LogOut,
  ChevronRight,
  Bell,
  Building2
} from 'lucide-react';
import { AppView, User } from '../types';

interface LayoutProps {
  children: React.ReactNode;
  currentView: AppView;
  setView: (view: AppView) => void;
  user: User;
  onLogout: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, currentView, setView, user, onLogout }) => {
  const menuItems = [
    { id: AppView.DASHBOARD, icon: LayoutDashboard, label: 'Dashboard' },
    { id: AppView.GENERATE, icon: Video, label: 'Generate Video' },
  ];

  const bottomItems = [
    { id: AppView.SETTINGS, icon: Settings, label: 'Settings' },
    { id: AppView.HELP, icon: HelpCircle, label: 'Help' },
  ];

  return (
    <div className="flex h-screen bg-white overflow-hidden text-black">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-black flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-10">
            <div className="w-8 h-8 bg-black rounded flex items-center justify-center">
              <Building2 className="text-white w-5 h-5" />
            </div>
            <span className="text-lg font-black tracking-tighter uppercase">
              ESTATEVISION
            </span>
          </div>

          <nav className="space-y-1">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setView(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-none transition-all border-l-4 ${
                  currentView === item.id 
                    ? 'border-black bg-zinc-100 text-black font-bold' 
                    : 'border-transparent text-zinc-500 hover:text-black hover:bg-zinc-50'
                }`}
              >
                <item.icon size={18} />
                <span className="text-sm uppercase tracking-wide">{item.label}</span>
                {currentView === item.id && <ChevronRight size={14} className="ml-auto" />}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-auto p-6 border-t border-zinc-100">
          <nav className="space-y-1 mb-6">
            {bottomItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setView(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 text-zinc-500 hover:text-black transition-all ${
                  currentView === item.id ? 'text-black font-bold' : ''
                }`}
              >
                <item.icon size={18} />
                <span className="text-xs uppercase tracking-widest">{item.label}</span>
              </button>
            ))}
            <button
              onClick={onLogout}
              className="w-full flex items-center gap-3 px-3 py-2 text-zinc-400 hover:text-black transition-all"
            >
              <LogOut size={18} />
              <span className="text-xs uppercase tracking-widest">Logout</span>
            </button>
          </nav>

          <div className="flex items-center gap-3 p-3 bg-zinc-50 border border-zinc-200">
            <div className="w-8 h-8 bg-black rounded text-white flex items-center justify-center text-xs font-bold">
              {user.name.charAt(0)}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-bold truncate text-black uppercase">{user.name}</p>
              <p className="text-[10px] text-zinc-400 truncate uppercase">{user.company}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden bg-zinc-50">
        {/* Header */}
        <header className="h-14 bg-white border-b border-black flex items-center justify-between px-8">
          <h2 className="text-xs font-black uppercase tracking-widest text-zinc-400">
            Internal Management / <span className="text-black">{currentView}</span>
          </h2>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 px-3 py-1 bg-black text-white rounded-none text-[10px] font-bold uppercase tracking-widest">
              {user.credits} Credits Remaining
            </div>
            <button className="text-zinc-400 hover:text-black transition-colors relative">
              <Bell size={18} />
              <span className="absolute top-0 right-0 w-1.5 h-1.5 bg-black rounded-full border border-white" />
            </button>
          </div>
        </header>

        {/* View Port */}
        <div className="flex-1 overflow-y-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
