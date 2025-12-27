
export enum AppView {
  DASHBOARD = 'DASHBOARD',
  GENERATE = 'GENERATE',
  SETTINGS = 'SETTINGS',
  HELP = 'HELP',
  AUTH = 'AUTH'
}

export enum GenerationStatus {
  IDLE = 'IDLE',
  SCRIPTING = 'SCRIPTING',
  VOICEOVER = 'VOICEOVER',
  VIDEO_GEN = 'VIDEO_GEN',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED'
}

export interface PropertyVideo {
  id: string;
  title: string;
  description: string;
  videoUrl?: string;
  thumbnailUrl: string;
  status: GenerationStatus;
  createdAt: Date;
  language: string;
  duration?: string;
}

export interface User {
  id: number | string;
  name: string;
  email: string;
  company: string;
  avatar: string;
  credits: number;
}

export interface SystemLog {
  id: number | string;
  level: string;
  module: string;
  message: string;
  timestamp: Date | string;
}

export interface SystemStats {
  total_jobs: number;
  completed_jobs: number;
  success_rate: string;
  network_uptime: string;
  stream_latency: string;
}
