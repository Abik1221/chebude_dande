import React, { useState, useEffect } from 'react';
import { Settings, Key } from 'lucide-react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import VideoGenerator from './components/VideoGenerator';
import Login from './components/Login'; // Add Login component
import SettingsComponent from './components/Settings'; // Add Settings component
import { AppView, User as UserType, PropertyVideo, GenerationStatus } from './types';
import { apiService } from './services/apiService';
import axios from 'axios';

// Create axios instance for direct access
const apiClient = axios.create({
  baseURL: process.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

// Mock Initial State
const MOCK_USER: UserType = {
  id: 1,
  name: 'Internal Admin',
  email: 'admin@metronavix-internal.com',
  company: 'Metronavix HQ',
  avatar: '', // Custom letter avatar used instead
  credits: 500,
};

const App: React.FC = () => {
  const [currentView, setView] = useState<AppView>(AppView.DASHBOARD);
  const [user, setUser] = useState<UserType | null>(null);
  const [videos, setVideos] = useState<PropertyVideo[]>([]);
  const [isAuth, setIsAuth] = useState(false); // Changed to false initially to show login
  const [hasKey, setHasKey] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);

  // Check if user is already logged in (has token)
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Set the authorization header
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;

      // Try to get user info with the token
      const fetchUser = async () => {
        try {
          const userData = await apiService.getCurrentUser();
          // Convert backend user to frontend user format
          const frontendUser: UserType = {
            id: userData.id,
            name: userData.full_name || userData.username,
            email: userData.email,
            company: 'Metronavix',
            avatar: '',
            credits: userData.credits,
          };
          setUser(frontendUser);
          setIsAuth(true);
        } catch (error) {
          // Token might be invalid, clear it
          localStorage.removeItem('access_token');
          delete apiClient.defaults.headers.common['Authorization'];
          setIsAuth(false);
        }
      };
      fetchUser();
    }
  }, []);

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

  const handleLogin = async (username: string, password: string) => {
    setLoginLoading(true);
    setLoginError(null);

    try {
      // Call the login API
      const loginResponse = await apiService.login(username, password);

      // Convert backend user to frontend user format
      const frontendUser: UserType = {
        id: loginResponse.user.id,
        name: loginResponse.user.full_name || loginResponse.user.username,
        email: loginResponse.user.email,
        company: 'Metronavix',
        avatar: '',
        credits: loginResponse.user.credits,
      };

      setUser(frontendUser);
      setIsAuth(true);
    } catch (error: any) {
      setLoginError(error.response?.data?.detail || 'Invalid username or password. Please try again.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleVideoGenerated = (newVideo: PropertyVideo) => {
    setVideos(prev => [newVideo, ...prev]);
    if (user) {
      setUser({
        ...user,
        credits: user.credits - 5
      });
    }
  };

  const handleLogout = async () => {
    try {
      await apiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setIsAuth(false);
      setUser(null);
      localStorage.removeItem('access_token');
    }
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
      user={user!}
      onLogout={handleLogout}
    >
      {renderContent()}
    </Layout>
  );
};

export default App;