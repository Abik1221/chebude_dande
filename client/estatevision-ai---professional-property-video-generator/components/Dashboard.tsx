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
  FileVideo
} from 'lucide-react';
import { PropertyVideo, GenerationStatus, SystemLog } from '../types';
import { apiService } from '../services/apiService';

interface DashboardProps {
  onStartGenerating: () => void;
  recentVideos: PropertyVideo[];
}

const Dashboard: React.FC<DashboardProps> = ({ onStartGenerating, recentVideos }) => {
  const [jobs, setJobs] = useState<PropertyVideo[]>(recentVideos);
  const [loading, setLoading] = useState(true);

  // Fetch jobs from backend API
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const fetchedJobs = await apiService.getJobs();
        // Convert backend jobs to PropertyVideo format
        const convertedJobs: PropertyVideo[] = fetchedJobs.map(job => ({
          id: job.id.toString(),
          title: `Job #${job.id}`,
          description: `Status: ${job.status}`,
          thumbnailUrl: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&q=80&w=400',
          status: job.status as GenerationStatus,
          createdAt: new Date(job.created_at),
          language: 'en', // Default language, would need to enhance backend to store this
          duration: 'N/A' // Duration would need to be stored in backend
        }));
        setJobs(convertedJobs);
      } catch (error) {
        console.error('Error fetching jobs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
      {/* Quick Access Area */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="md:col-span-3 bg-black text-white p-8 flex items-center justify-between border border-black shadow-lg">
          <div>
            <h1 className="text-2xl font-black uppercase tracking-tighter mb-2">Company Production Hub</h1>
            <p className="text-zinc-400 text-xs uppercase tracking-widest max-w-md">
              Internal property video generation tool. AI infrastructure active and ready.
            </p>
          </div>
          <button 
            onClick={onStartGenerating}
            className="bg-white text-black px-6 py-3 font-bold uppercase tracking-widest text-xs flex items-center gap-2 hover:invert transition-all active:scale-95"
          >
            <Plus size={16} />
            New Generation
          </button>
        </div>
        <div className="bg-white border border-black p-6 flex flex-col justify-center">
          <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mb-1">Queue Status</p>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            <h3 className="text-xl font-black uppercase tracking-tighter">Optimal</h3>
          </div>
        </div>
      </div>

      {/* Main Operations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recent Generations Table */}
        <div className="lg:col-span-2 bg-white border border-black p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <FileVideo size={18} />
              <h3 className="text-sm font-black uppercase tracking-widest">Generation History</h3>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-zinc-100 text-[10px] font-black uppercase tracking-widest text-zinc-400">
                  <th className="pb-4 px-2">Project</th>
                  <th className="pb-4 px-2">Language</th>
                  <th className="pb-4 px-2">Timestamp</th>
                  <th className="pb-4 px-2">Status</th>
                  <th className="pb-4 px-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-50">
                {jobs.length > 0 ? jobs.map((video) => (
                  <tr key={video.id} className="group hover:bg-zinc-50 transition-colors">
                    <td className="py-4 px-2">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-7 bg-zinc-100 border border-zinc-200 overflow-hidden flex-shrink-0">
                          <img src={video.thumbnailUrl} className="w-full h-full object-cover grayscale" alt="" />
                        </div>
                        <span className="text-xs font-bold text-black uppercase truncate max-w-[150px]">{video.title}</span>
                      </div>
                    </td>
                    <td className="py-4 px-2">
                      <span className="text-[10px] font-bold uppercase bg-zinc-100 px-2 py-0.5">{video.language}</span>
                    </td>
                    <td className="py-4 px-2">
                      <span className="text-[10px] text-zinc-500 font-medium">{video.createdAt.toLocaleDateString()}</span>
                    </td>
                    <td className="py-4 px-2">
                      <div className="flex items-center gap-1.5">
                        <div className={`w-1.5 h-1.5 rounded-full ${
                          video.status === GenerationStatus.COMPLETED ? 'bg-black' : 'bg-zinc-300'
                        }`} />
                        <span className="text-[10px] font-black uppercase text-zinc-600">{video.status}</span>
                      </div>
                    </td>
                    <td className="py-4 px-2 text-right">
                      <button className="p-1 hover:bg-black hover:text-white rounded transition-colors">
                        <PlayCircle size={16} />
                      </button>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={5} className="py-20 text-center text-xs text-zinc-400 uppercase tracking-widest">
                      {loading ? 'Loading jobs...' : 'No generation tasks found in system.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Logs */}
        <div className="bg-black text-white p-6 border border-black flex flex-col h-full">
          <div className="flex items-center gap-2 mb-6 border-b border-zinc-800 pb-4">
            <Terminal size={18} />
            <h3 className="text-sm font-black uppercase tracking-widest">Operation Logs</h3>
          </div>
          
          <div className="space-y-4 flex-1 overflow-y-auto font-mono text-[10px]">
            <div className="pt-2 animate-pulse text-zinc-700">_ Waiting for events...</div>
          </div>

          <div className="mt-6 pt-4 border-t border-zinc-800">
            <div className="flex items-center justify-between text-[10px] font-black uppercase text-zinc-500">
              <span>Environment</span>
              <span>Production_V2</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Summary - Internal Focused */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'System Uptime', value: '99.9%', icon: Activity },
          { label: 'Total Jobs', value: jobs.length.toString(), icon: FileVideo },
          { label: 'Success Rate', value: jobs.length > 0 
            ? `${Math.round((jobs.filter(j => j.status === GenerationStatus.COMPLETED).length / jobs.length) * 100)}%` 
            : '0%', icon: CheckCircle },
          { label: 'Avg Latency', value: '1.2m', icon: Clock },
        ].map((stat, i) => (
          <div key={i} className="bg-white border border-black p-4 flex items-center gap-4">
            <div className="w-10 h-10 border border-zinc-100 flex items-center justify-center">
              <stat.icon size={20} className="text-zinc-400" />
            </div>
            <div>
              <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">{stat.label}</p>
              <h4 className="text-lg font-black tracking-tighter uppercase">{stat.value}</h4>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;