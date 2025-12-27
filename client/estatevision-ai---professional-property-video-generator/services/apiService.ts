import axios from 'axios';
import { SystemLog, SystemStats } from '../types';

// Define API base URL
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
});

// Define TypeScript interfaces matching our backend
export interface Job {
  id: number;
  status: string;
  progress: number;
  target_language: string;
  created_at: string;
  updated_at: string;
}

export interface JobStatusResponse {
  id: number;
  status: string;
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  output_file_path?: string;
}

export interface VideoGenerationRequest {
  description_text: string;
  target_language: string;
}

export interface UploadResponse {
  filename: string;
  size: number;
  path: string;
}

export interface Language {
  code: string;
  name: string;
  tts_voice: string;
}

export interface Setting {
  key: string;
  value: string;
  type: string;
  description?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_admin: boolean;
  credits: number;
  created_at: string;
  updated_at: string;
}

export interface UserLoginRequest {
  username: string;
  password: string;
}

export interface UserLoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserRegistrationRequest {
  username: string;
  email: string;
  password?: string;
  full_name?: string;
}

export interface UserUpdateRequest {
  username?: string;
  email?: string;
  full_name?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// API service functions
export const apiService = {
  // Authentication methods
  login: async (username: string, password: string): Promise<UserLoginResponse> => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await apiClient.post('/api/v1/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    // Store token in localStorage
    const token = response.data.access_token;
    localStorage.setItem('access_token', token);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    return response.data;
  },

  register: async (userData: UserRegistrationRequest): Promise<User> => {
    const response = await apiClient.post('/api/v1/auth/register', userData);
    return response.data;
  },

  logout: async (): Promise<void> => {
    // Remove token from localStorage
    localStorage.removeItem('access_token');
    delete apiClient.defaults.headers.common['Authorization'];
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  },

  updateUser: async (userData: UserUpdateRequest): Promise<User> => {
    const response = await apiClient.put('/api/v1/auth/me', userData);
    return response.data;
  },

  changePassword: async (passwordData: ChangePasswordRequest): Promise<{ message: string }> => {
    const response = await apiClient.put('/api/v1/auth/change-password', passwordData);
    return response.data;
  },

  // Submit a new video generation job
  submitVideoGeneration: async (
    videoFile: File,
    descriptionText: string,
    targetLanguage: string
  ): Promise<{ id: number; status: string; progress: number }> => {
    const formData = new FormData();
    formData.append('video_file', videoFile);
    formData.append('description_text', descriptionText);
    formData.append('target_language', targetLanguage);

    const response = await apiClient.post('/api/v1/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // Get job status
  getJobStatus: async (jobId: number): Promise<JobStatusResponse> => {
    const response = await apiClient.get(`/api/v1/status/${jobId}`);
    return response.data;
  },

  // Get list of jobs
  getJobs: async (): Promise<Job[]> => {
    const response = await apiClient.get('/api/v1/jobs');
    return response.data;
  },

  // Get supported languages
  getSupportedLanguages: async (): Promise<Language[]> => {
    const response = await apiClient.get('/api/v1/languages');
    return response.data;
  },

  // Upload video without starting generation
  uploadVideo: async (videoFile: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('video_file', videoFile);

    const response = await apiClient.post('/api/v1/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // Delete a job
  deleteJob: async (jobId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/jobs/${jobId}`);
  },

  // Get all settings
  getSettings: async (): Promise<Record<string, string>> => {
    const response = await apiClient.get('/api/v1/settings');
    return response.data.settings;
  },

  // Get specific setting
  getSetting: async (key: string): Promise<Setting> => {
    const response = await apiClient.get(`/api/v1/settings/${key}`);
    return response.data;
  },

  // Update specific setting
  updateSetting: async (
    key: string,
    value: string,
    description?: string,
    type: string = 'string'
  ): Promise<Setting> => {
    const response = await apiClient.put(`/api/v1/settings/${key}`, null, {
      params: {
        value,
        description,
        type
      }
    });
    return response.data;
  },

  // Update multiple settings
  updateMultipleSettings: async (settings: Record<string, string>): Promise<Record<string, string>> => {
    const response = await apiClient.put('/api/v1/settings', settings);
    return response.data.updated_settings;
  },

  // Initialize default settings
  initializeDefaultSettings: async (): Promise<{ message: string; count: number }> => {
    const response = await apiClient.post('/api/v1/settings/initialize');
    return response.data;
  },

  // System statistics and logs
  getSystemLogs: async (limit: number = 20): Promise<SystemLog[]> => {
    const response = await apiClient.get('/api/v1/logs', { params: { limit } });
    return response.data;
  },

  getSystemStats: async (): Promise<SystemStats> => {
    const response = await apiClient.get('/api/v1/stats');
    return response.data;
  },
};