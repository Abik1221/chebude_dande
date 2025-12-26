import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Save, 
  RefreshCw, 
  Key,
  Globe,
  Volume2,
  Video,
  Mail,
  Lock,
  Shield,
  Zap,
  Download,
  Upload
} from 'lucide-react';
import { apiService } from '../services/apiService';

interface Setting {
  key: string;
  value: string;
  type: string;
  description?: string;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load settings from API
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const settingsData = await apiService.getSettings();
        setSettings(settingsData);
      } catch (err: any) {
        setError('Failed to load settings: ' + err.message);
        console.error('Error loading settings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  // Handle input changes
  const handleInputChange = (key: string, value: string) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Save settings to API
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await apiService.updateMultipleSettings(settings);
      setSuccess('Settings saved successfully');
    } catch (err: any) {
      setError('Failed to save settings: ' + err.message);
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  // Initialize default settings
  const initializeDefaults = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await apiService.initializeDefaultSettings();
      const settingsData = await apiService.getSettings();
      setSettings(settingsData);
      setSuccess(`${result.message} (${result.count} settings)`);
    } catch (err: any) {
      setError('Failed to initialize default settings: ' + err.message);
      console.error('Error initializing settings:', err);
    } finally {
      setLoading(false);
    }
  };

  // Settings categories with their icons
  const settingCategories = [
    {
      id: 'general',
      name: 'General',
      icon: SettingsIcon,
      settings: [
        { key: 'app_name', label: 'Application Name', type: 'text' },
        { key: 'app_version', label: 'Version', type: 'text' },
        { key: 'default_language', label: 'Default Language', type: 'select', options: ['en', 'te'] },
      ]
    },
    {
      id: 'video',
      name: 'Video Processing',
      icon: Video,
      settings: [
        { key: 'max_video_size_mb', label: 'Max Video Size (MB)', type: 'number' },
        { key: 'max_description_length', label: 'Max Description Length', type: 'number' },
        { key: 'video_processing_quality', label: 'Video Quality', type: 'select', options: ['720p', '1080p', '4K'] },
      ]
    },
    {
      id: 'tts',
      name: 'Text-to-Speech',
      icon: Volume2,
      settings: [
        { key: 'enable_tts_fallback', label: 'Enable TTS Fallback', type: 'checkbox' },
        { key: 'tts_fallback_service', label: 'Fallback Service', type: 'select', options: ['google', 'openai'] },
        { key: 'default_tts_voice', label: 'Default Voice', type: 'text' },
        { key: 'tts_speed', label: 'Speech Speed', type: 'text' },
      ]
    },
    {
      id: 'api',
      name: 'API & Security',
      icon: Shield,
      settings: [
        { key: 'enable_api_rate_limiting', label: 'Enable Rate Limiting', type: 'checkbox' },
        { key: 'api_rate_limit_requests', label: 'Requests per Window', type: 'number' },
        { key: 'api_rate_limit_window', label: 'Rate Limit Window (s)', type: 'number' },
      ]
    },
    {
      id: 'email',
      name: 'Email Notifications',
      icon: Mail,
      settings: [
        { key: 'enable_email_notifications', label: 'Enable Email Notifications', type: 'checkbox' },
        { key: 'email_smtp_server', label: 'SMTP Server', type: 'text' },
        { key: 'email_smtp_port', label: 'SMTP Port', type: 'number' },
      ]
    },
    {
      id: 'performance',
      name: 'Performance',
      icon: Zap,
      settings: [
        { key: 'enable_background_processing', label: 'Background Processing', type: 'checkbox' },
        { key: 'max_concurrent_jobs', label: 'Max Concurrent Jobs', type: 'number' },
      ]
    }
  ];

  // Render input based on type
  const renderInput = (setting: { key: string; label: string; type: string; options?: string[] }) => {
    const value = settings[setting.key] || '';
    
    switch (setting.type) {
      case 'checkbox':
        return (
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={value === 'true'}
              onChange={(e) => handleInputChange(setting.key, e.target.checked ? 'true' : 'false')}
              className="h-4 w-4 text-black focus:ring-black border-zinc-300 rounded"
            />
            <span className="ml-2 text-sm text-zinc-600">Enable</span>
          </label>
        );
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleInputChange(setting.key, e.target.value)}
            className="w-full px-3 py-2 border border-zinc-200 text-sm focus:border-black focus:ring-0 outline-none transition-all bg-zinc-50"
          >
            {setting.options?.map(option => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleInputChange(setting.key, e.target.value)}
            className="w-full px-3 py-2 border border-zinc-200 text-sm focus:border-black focus:ring-0 outline-none transition-all bg-zinc-50"
          />
        );
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleInputChange(setting.key, e.target.value)}
            className="w-full px-3 py-2 border border-zinc-200 text-sm focus:border-black focus:ring-0 outline-none transition-all bg-zinc-50"
          />
        );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-black"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fadeIn text-black">
      <div className="flex items-center justify-between border-b border-zinc-200 pb-6">
        <div className="flex items-center gap-3">
          <SettingsIcon size={24} className="text-black" />
          <h1 className="text-2xl font-black uppercase tracking-tight">System Configuration</h1>
        </div>
        <div className="flex gap-3">
          <button
            onClick={initializeDefaults}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 border border-zinc-300 text-sm font-black uppercase tracking-widest hover:bg-zinc-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Reset Defaults
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className={`flex items-center gap-2 px-4 py-2 text-white text-sm font-black uppercase tracking-widest transition-colors ${
              saving ? 'bg-gray-400 cursor-not-allowed' : 'bg-black hover:bg-zinc-800'
            }`}
          >
            {saving ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 border border-green-200 text-green-700 text-sm rounded">
          {success}
        </div>
      )}

      <div className="space-y-8">
        {settingCategories.map(category => (
          <div key={category.id} className="bg-white border border-black p-6">
            <div className="flex items-center gap-3 mb-6">
              <category.icon size={20} />
              <h3 className="text-sm font-black uppercase tracking-widest">{category.name}</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {category.settings.map(setting => (
                <div key={setting.key} className="space-y-2">
                  <label className="text-xs font-black uppercase tracking-widest text-zinc-500">
                    {setting.label}
                  </label>
                  {renderInput(setting)}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-zinc-50 border border-zinc-200 p-6">
        <h3 className="text-sm font-black uppercase tracking-widest mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-zinc-500">Application</p>
            <p className="font-bold">{settings.app_name || 'EstateVision AI'}</p>
          </div>
          <div>
            <p className="text-zinc-500">Version</p>
            <p className="font-bold">{settings.app_version || '1.0.0'}</p>
          </div>
          <div>
            <p className="text-zinc-500">Status</p>
            <p className="font-bold text-emerald-600">Operational</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;