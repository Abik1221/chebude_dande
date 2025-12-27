import React, { useState, useEffect } from 'react';
import {
  Plus,
  Video,
  Clock,
  PlayCircle,
  Activity,
  CheckCircle,
  AlertCircle,
  Terminal,
  FileVideo,
  ArrowRight,
  TrendingUp,
  ChevronRight
} from 'lucide-react';
import { PropertyVideo, GenerationStatus, SystemLog } from '../types';
import { apiService } from '../services/apiService';

interface DashboardProps {
  onStartGenerating: () => void;
  recentVideos: PropertyVideo[];
}

const Dashboard: React.FC<DashboardProps> = ({ onStartGenerating, recentVideos }) => {
  const [jobs, setJobs] = useState<PropertyVideo[]>(recentVideos);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [isLogsExpanded, setIsLogsExpanded] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch data from backend API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [fetchedJobs, fetchedLogs, fetchedStats] = await Promise.all([
          apiService.getJobs(),
          apiService.getSystemLogs(10),
          apiService.getSystemStats()
        ]);

        // Convert backend jobs to PropertyVideo format
        const convertedJobs: PropertyVideo[] = fetchedJobs.map(job => ({
          id: job.id.toString(),
          title: `Job #${job.id}`,
          description: `Status: ${job.status}`,
          thumbnailUrl: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&q=80&w=400',
          status: job.status as GenerationStatus,
          createdAt: new Date(job.created_at),
          language: job.target_language || 'en',
          duration: 'N/A'
        }));

        setJobs(convertedJobs);
        setLogs(fetchedLogs.map(log => ({
          ...log,
          timestamp: typeof log.timestamp === 'string' ? new Date(log.timestamp) : log.timestamp
        })));
        setStats(fetchedStats);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-10 max-w-[1400px] mx-auto animate-in fade-in duration-700">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-zinc-800 to-zinc-900 rounded-[2.5rem] p-12 shadow-2xl shadow-zinc-200/50 group">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-zinc-700/20 rounded-full blur-[100px] opacity-50 group-hover:opacity-75 transition-opacity"></div>
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-60 h-60 bg-zinc-700/10 rounded-full blur-[80px] opacity-30 group-hover:opacity-50 transition-opacity"></div>

        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="text-center md:text-left">
            <div className="inline-flex items-center gap-2 bg-zinc-800/50 backdrop-blur-sm px-4 py-2 rounded-full text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-6 border border-white/5">
              <TrendingUp size={12} />
              <span>Production Engine v4.2 Active</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-black text-white tracking-tighter mb-4 drop-shadow-sm">
              Metronavix <span className="text-zinc-400">Hub</span>
            </h1>
            <p className="text-white text-sm font-medium max-w-lg leading-relaxed shadow-sm opacity-90">
              Internal property video generation suite. Real-time AI processing with Gemini 3 and Veo 3.1 infrastructure.
            </p>
          </div>

          <button
            onClick={onStartGenerating}
            className="group relative bg-white hover:bg-zinc-100 text-zinc-900 px-8 py-5 rounded-2xl font-black uppercase tracking-widest text-xs flex items-center gap-4 transition-all active:scale-95 shadow-xl shadow-white/5"
          >
            <Plus size={18} className="group-hover:rotate-90 transition-transform duration-300" />
            New Generation Task
            <ArrowRight size={16} className="opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all" />
          </button>
        </div>
      </div>

      {/* Main Operations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">

        {/* Recent Generations Table */}
        <div className="lg:col-span-2 bg-white rounded-[2rem] p-8 border border-zinc-100 shadow-sm">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-zinc-50 rounded-xl flex items-center justify-center border border-zinc-100">
                <FileVideo size={20} className="text-zinc-600" />
              </div>
              <div>
                <h3 className="text-sm font-black uppercase tracking-widest text-zinc-900">Queue & History</h3>
                <p className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest mt-0.5">Real-time status tracking</p>
                <p className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest mt-0.5">Real-time status tracking</p>
              </div>
            </div>
            <button className="text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-zinc-900 transition-colors">View All</button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-zinc-100 italic">
                  <th className="text-left py-4 px-6 text-[10px] font-black uppercase tracking-widest text-zinc-500">Sequence</th>
                  <th className="text-left py-4 px-6 text-[10px] font-black uppercase tracking-widest text-zinc-500">Timestamp</th>
                  <th className="text-left py-4 px-6 text-[10px] font-black uppercase tracking-widest text-zinc-500">Status</th>
                  <th className="text-right py-4 px-6 text-[10px] font-black uppercase tracking-widest text-zinc-500">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-50/50">
                {jobs.length > 0 ? jobs.map((video) => (
                  <tr key={video.id} className="group hover:bg-zinc-50/50 transition-all cursor-default">
                    <td className="py-5 px-2">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-8 bg-zinc-100 rounded-lg border border-zinc-100 overflow-hidden flex-shrink-0 relative group">
                          <img src={video.thumbnailUrl} className="w-full h-full object-cover grayscale opacity-50 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-500" alt="" />
                          <div className="absolute inset-0 bg-zinc-900/10 group-hover:bg-transparent transition-colors"></div>
                        </div>
                        <span className="text-xs font-bold text-zinc-800 uppercase tracking-tight truncate max-w-[180px]">{video.title}</span>
                      </div>
                    </td>
                    <td className="py-5 px-2">
                      <span className="text-[9px] font-black uppercase tracking-widest bg-zinc-100 text-zinc-500 px-3 py-1 rounded-full border border-zinc-200/50">{video.language}</span>
                    </td>
                    <td className="py-5 px-2">
                      <span className="text-[10px] text-zinc-400 font-medium">{video.createdAt.toLocaleDateString()}</span>
                    </td>
                    <td className="py-5 px-2">
                      <div className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${video.status === GenerationStatus.COMPLETED ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-zinc-300'
                          }`} />
                        <span className="text-[9px] font-black uppercase tracking-widest text-zinc-500">{video.status}</span>
                      </div>
                    </td>
                    <td className="py-5 px-2 text-right">
                      <button className="p-2 text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 rounded-xl transition-all">
                        <PlayCircle size={18} />
                      </button>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={5} className="py-24 text-center">
                      <div className="flex flex-col items-center gap-4 opacity-30">
                        <Activity size={32} />
                        <p className="text-[10px] text-zinc-500 font-black uppercase tracking-[0.3em]">{loading ? 'Synchronizing Datastore...' : 'No system activity detected'}</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Logs */}
        <div className={`bg-zinc-900 rounded-[2rem] p-8 border border-white/10 shadow-2xl flex flex-col relative overflow-hidden group transition-all duration-500 ${isLogsExpanded ? 'h-[600px]' : 'h-[350px]'}`}>
          <div className="absolute top-0 right-0 w-40 h-40 bg-zinc-800/50 rounded-full blur-[60px] opacity-50"></div>

          <div className="relative z-10 flex flex-col h-full">
            <div className="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
                  <Terminal size={16} className="text-zinc-50" />
                </div>
                <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-zinc-50">Kernel Logs</h3>
              </div>
              <button
                onClick={() => setIsLogsExpanded(!isLogsExpanded)}
                className="text-[9px] font-black uppercase tracking-widest text-zinc-400 hover:text-white transition-colors flex items-center gap-2"
              >
                {isLogsExpanded ? 'Show Less' : 'Show All'}
                <ChevronRight size={14} className={`transition-transform duration-300 ${isLogsExpanded ? 'rotate-90' : ''}`} />
              </button>
            </div>

            <div className="space-y-4 flex-1 overflow-y-auto font-mono text-[10px] pr-2 scrollbar-thin scrollbar-thumb-zinc-700">
              {logs.length > 0 ? logs.map((log) => (
                <div key={log.id} className={`flex gap-3 leading-relaxed transition-colors border-l-2 border-transparent pl-3 hover:border-zinc-700 ${log.level === 'SUCCESS' ? 'text-emerald-400' :
                  log.level === 'ERROR' ? 'text-rose-400' :
                    log.level === 'WARNING' ? 'text-amber-400' : 'text-zinc-100'
                  }`}>
                  <span className="opacity-40 whitespace-nowrap font-medium">{new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}</span>
                  <span className="font-bold tracking-tight opacity-70">{log.module}:</span>
                  <span className="flex-1">{log.message}</span>
                </div>
              )) : (
                <div className="text-zinc-500 py-10 text-center italic">No system records available</div>
              )}
              <div className="pt-2 animate-pulse text-zinc-600 font-bold uppercase tracking-[0.3em] text-[8px]">_ Listening for broadcast...</div>
            </div>

            <div className="mt-8 pt-6 border-t border-white/5">
              <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-widest text-zinc-500">
                <span className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-emerald-400 rounded-full animate-ping"></div>
                  Metronavix_OS
                </span>
                <span className="text-zinc-600">SECURED_SSL_V3</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        {[
          { label: 'Network Uptime', value: stats?.network_uptime || '99.99%', icon: Activity, color: 'text-emerald-500' },
          { label: 'Total Jobs', value: stats?.total_jobs?.toString() || jobs.length.toString(), icon: FileVideo, color: 'text-blue-500' },
          {
            label: 'Success Velocity', value: stats?.success_rate || (jobs.length > 0
              ? `${Math.round((jobs.filter(j => j.status === GenerationStatus.COMPLETED).length / jobs.length) * 100)}%`
              : '100%'), icon: CheckCircle, color: 'text-zinc-900'
          },
          { label: 'Stream Latency', value: stats?.stream_latency || '0.8ms', icon: Clock, color: 'text-indigo-500' },
        ].map((stat, i) => (
          <div key={stat.label} className="bg-white rounded-[1.5rem] p-6 border border-zinc-100 shadow-sm hover:shadow-md transition-all group cursor-default">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-2 rounded-xl bg-zinc-50 ${stat.color} transition-transform group-hover:scale-110`}>
                <stat.icon size={20} />
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600 group-hover:text-zinc-900 transition-colors">{stat.label}</span>
            </div>
            <p className="text-2xl font-black text-zinc-900 tracking-tighter drop-shadow-sm">{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;