import axios from 'axios';

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
  input_file_path?: string;
  output_file_path?: string;
  error_message?: string;
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

// API service functions
export const apiService = {
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
};