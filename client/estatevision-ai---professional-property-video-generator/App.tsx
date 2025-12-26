import React, { useState, useEffect } from 'react';
import { Settings, Key } from 'lucide-react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import VideoGenerator from './components/VideoGenerator';
import Login from './components/Login'; // Add Login component
import SettingsComponent from './components/Settings'; // Add Settings component
import { AppView, User, PropertyVideo, GenerationStatus } from './types';
import { apiService } from './services/apiService';

// Mock Initial State
const MOCK_USER: User = {
  name: 'Internal Admin',
  email: 'admin@estatevision-internal.com',
  company: 'EstateVision HQ',
  avatar: '', // Custom letter avatar used instead
  credits: 500,
};

const App: React.FC = () => {
  const [currentView, setView] = useState<AppView>(AppView.DASHBOARD);
  const [user, setUser] = useState<User>(MOCK_USER);
  const [videos, setVideos] = useState<PropertyVideo[]>([]);
  const [isAuth, setIsAuth] = useState(false); // Changed to false initially to show login
  const [hasKey, setHasKey] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);

  useEffect(() => {
    const checkKey = async () => {
      if ((window as any).aistudio) {
        const selected = await (window as any).aistudio.hasSelectedApiKey();
        setHasKey(selected);
      } else {
        setHasKey(true); 
      }
    };
    checkKey();
  }, []);

  const handleOpenKeySelection = async () => {
    if ((window as any).aistudio) {
      await (window as any).aistudio.openSelectKey();
      setHasKey(true); 
    }
  };

  const handleLogin = async (email: string, password: string) => {
    setLoginLoading(true);
    setLoginError(null);
    
    try {
      // In a real application, you would call your authentication API here
      // For now, we'll simulate authentication
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // For demo purposes, we'll just set the user and authenticate
      setIsAuth(true);
      setUser({
        ...MOCK_USER,
        email: email
      });
    } catch (error) {
      setLoginError('Invalid email or password. Please try again.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleVideoGenerated = (newVideo: PropertyVideo) => {
    setVideos(prev => [newVideo, ...prev]);
    setUser(prev => ({ ...prev, credits: prev.credits - 5 }));
  };

  const handleLogout = () => {
    setIsAuth(false);
  };

  // Show login page if not authenticated
  if (!isAuth) {
    return <Login onLogin={handleLogin} loading={loginLoading} error={loginError} />;
  }

  const renderContent = () => {
    switch (currentView) {
      case AppView.DASHBOARD:
        return (
          <Dashboard 
            onStartGenerating={() => setView(AppView.GENERATE)} 
            recentVideos={videos} 
          />
        );
      case AppView.GENERATE:
        return <VideoGenerator onComplete={handleVideoGenerated} />;
      case AppView.SETTINGS:
        return <SettingsComponent />;
      case AppView.HELP:
        return (
          <div className="flex flex-col items-center justify-center h-full text-zinc-300">
            <Settings size={48} className="mb-6 opacity-20" />
            <h3 className="text-xs font-black uppercase tracking-[0.5em]">Module Offline</h3>
          </div>
        );
      default:
        return <Dashboard onStartGenerating={() => setView(AppView.GENERATE)} recentVideos={videos} />;
    }
  };

  return (
    <Layout 
      currentView={currentView} 
      setView={setView} 
      user={user} 
      onLogout={handleLogout}
    >
      {renderContent()}
    </Layout>
  );
};

export default App;