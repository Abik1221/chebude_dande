import React, { useState, useRef } from 'react';
import { 
  Upload, 
  FileText, 
  Languages, 
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Play,
  ArrowRight,
  Monitor
} from 'lucide-react';
import { GenerationStatus } from '../types';
import { apiService } from '../services/apiService';

const LANGUAGES = [
  { id: 'en', label: 'English', voice: 'nova' },
  { id: 'te', label: 'Telugu', voice: 'onyx' },
  // Add more languages as needed
];

const VideoGenerator: React.FC<{ onComplete: (video: any) => void }> = ({ onComplete }) => {
  const [status, setStatus] = useState<GenerationStatus>(GenerationStatus.IDLE);
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('en');
  const [selectedVideo, setSelectedVideo] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [generatedResult, setGeneratedResult] = useState<{
    id: string;
    title: string;
    description: string;
    thumbnailUrl: string;
    status: GenerationStatus;
    createdAt: Date;
    language: string;
    videoUrl?: string;
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Only validate file size (max 100MB)
      if (file.size > 100 * 1024 * 1024) {
        setError('File size exceeds 100MB limit');
        return;
      }
      
      setSelectedVideo(file);
      setError(null); // Clear any previous errors
      
      // Create preview URL (only for video files)
      try {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } catch (err) {
        // If preview fails, just continue without preview
        setPreviewUrl(null);
      }
    }
  };

  const handleGenerate = async () => {
    if (!selectedVideo) return setError('Please select a video file.');
    if (!description.trim()) return setError('Please provide a property description.');
    
    setError(null);
    setStatus(GenerationStatus.SCRIPTING);
    
    try {
      // Submit the video generation job to backend
      const result = await apiService.submitVideoGeneration(
        selectedVideo,
        description,
        language
      );
      
      setStatus(GenerationStatus.VOICEOVER);
      
      // Poll for job status until completion
      let currentStatus = await apiService.getJobStatus(result.id);
      while (currentStatus.status !== 'COMPLETED' && currentStatus.status !== 'FAILED') {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds between polls
        currentStatus = await apiService.getJobStatus(result.id);
        
        // Update status based on progress
        if (currentStatus.progress < 30) {
          setStatus(GenerationStatus.SCRIPTING);
        } else if (currentStatus.progress < 60) {
          setStatus(GenerationStatus.VOICEOVER);
        } else {
          setStatus(GenerationStatus.VIDEO_GEN);
        }
      }
      
      if (currentStatus.status === 'COMPLETED') {
        setStatus(GenerationStatus.COMPLETED);
        
        // Create result object
        const newVideo = {
          id: result.id.toString(),
          title: `Generated Video #${result.id}`,
          description,
          videoUrl: currentStatus.output_file_path || `/api/v1/download/${result.id}`, // Use download endpoint if no direct path
          thumbnailUrl: previewUrl || 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&q=80&w=400',
          status: GenerationStatus.COMPLETED,
          createdAt: new Date(),
          language
        };
        
        setGeneratedResult(newVideo);
        onComplete(newVideo);
      } else {
        setStatus(GenerationStatus.FAILED);
        setError(currentStatus.error_message || 'Video generation failed');
      }
    } catch (err: any) {
      console.error('Generation error:', err);
      setStatus(GenerationStatus.FAILED);
      setError(err.message || 'An error occurred during video generation.');
    }
  };

  const handleReset = () => {
    setStatus(GenerationStatus.IDLE);
    setDescription('');
    setLanguage('en');
    setSelectedVideo(null);
    setPreviewUrl(null);
    setGeneratedResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const isProcessing = status !== GenerationStatus.IDLE && status !== GenerationStatus.COMPLETED && status !== GenerationStatus.FAILED;

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fadeIn text-black">
      {status === GenerationStatus.IDLE || status === GenerationStatus.FAILED ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          <div className="lg:col-span-3 space-y-6">
            {/* Video Upload */}
            <div className="bg-white border border-black p-8">
              <div className="flex items-center gap-3 mb-6">
                <Upload size={20} />
                <h3 className="text-sm font-black uppercase tracking-widest">Property Video Upload</h3>
              </div>
              
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="group relative h-48 border border-zinc-200 border-dashed flex flex-col items-center justify-center cursor-pointer hover:bg-zinc-50 transition-all overflow-hidden"
              >
                {previewUrl ? (
                  <>
                    <div className="w-full h-full bg-zinc-100 flex items-center justify-center">
                      <div className="text-center">
                        <Upload className="text-zinc-400 mb-2 mx-auto" size={24} />
                        <p className="text-[10px] font-black uppercase text-zinc-600 tracking-widest">File Selected</p>
                        <p className="text-[8px] text-zinc-500 mt-1">{selectedVideo?.name}</p>
                      </div>
                    </div>
                    <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="text-white text-[10px] font-black uppercase tracking-widest">Change File</span>
                    </div>
                  </>
                ) : (
                  <>
                    <Upload className="text-zinc-300 mb-2" size={24} />
                    <p className="text-[10px] font-black uppercase text-zinc-400 tracking-widest">Select Any File</p>
                    <p className="text-[8px] text-zinc-500 mt-1">Any video file up to 100MB</p>
                  </>
                )}
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  className="hidden" 
                />
              </div>
              
              {selectedVideo && (
                <div className="mt-3 text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
                  Selected: {selectedVideo.name} ({(selectedVideo.size / (1024 * 1024)).toFixed(2)} MB)
                </div>
              )}
            </div>

            {/* Project Input */}
            <div className="bg-white border border-black p-8">
              <div className="flex items-center gap-3 mb-6">
                <FileText size={20} />
                <h3 className="text-sm font-black uppercase tracking-widest">Property Description</h3>
              </div>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Provide detailed description of the property: features, amenities, location, size, etc..."
                className="w-full h-64 bg-zinc-50 border border-zinc-200 p-6 text-xs font-mono text-black placeholder-zinc-400 focus:border-black outline-none transition-all resize-none"
              />
              <div className="mt-4 flex justify-between items-center text-[10px] text-zinc-400 font-bold uppercase tracking-widest">
                <span>Max 5000 characters</span>
                <span>Payload: {description.length}/5000 chars</span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white border border-black p-8">
              <div className="flex items-center gap-3 mb-8">
                <Languages size={20} />
                <h3 className="text-sm font-black uppercase tracking-widest">Synthesis Parameters</h3>
              </div>
              
              <div className="space-y-8">
                <div>
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3 block">Output Language</label>
                  <div className="grid grid-cols-2 gap-2">
                    {LANGUAGES.map((lang) => (
                      <button
                        key={lang.id}
                        onClick={() => setLanguage(lang.id)}
                        className={`px-3 py-3 border text-[10px] font-black tracking-widest uppercase transition-all ${
                          language === lang.id 
                            ? 'bg-black border-black text-white' 
                            : 'bg-white border-zinc-200 text-zinc-400 hover:border-black'
                        }`}
                      >
                        {lang.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-3 block">Video Resolution</label>
                  <div className="flex border border-zinc-100 p-1">
                    <button className="flex-1 py-2 bg-black text-white text-[10px] font-black uppercase tracking-widest">720p Std</button>
                    <button className="flex-1 py-2 bg-white text-zinc-300 text-[10px] font-black uppercase tracking-widest cursor-not-allowed">1080p HQ</button>
                  </div>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-black text-white p-4 flex items-center gap-3 text-[10px] font-black uppercase tracking-widest border-l-4 border-red-500">
                <AlertCircle size={14} className="text-red-500" />
                {error}
              </div>
            )}

            <button 
              onClick={handleGenerate}
              disabled={!selectedVideo || !description.trim() || isProcessing}
              className={`w-full bg-black text-white py-6 font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 hover:invert transition-all border border-black ${
                (!selectedVideo || !description.trim() || isProcessing) ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              Start Synthesis <ArrowRight size={18} />
            </button>
            <p className="text-center text-[9px] text-zinc-400 font-bold uppercase tracking-widest mt-4">
              Operation will take ~120 seconds. Video will be processed on our servers.
            </p>
          </div>
        </div>
      ) : isProcessing ? (
        <div className="flex flex-col items-center justify-center py-32 bg-white border border-black shadow-2xl">
          <div className="relative mb-12">
            <div className="w-40 h-40 border border-zinc-100 border-t-black rounded-full animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Monitor size={48} className="animate-pulse" />
            </div>
          </div>
          <h2 className="text-xl font-black uppercase tracking-[0.3em] text-black mb-4">
            {status === GenerationStatus.SCRIPTING && 'Script Processing'}
            {status === GenerationStatus.VOICEOVER && 'Audio Generation'}
            {status === GenerationStatus.VIDEO_GEN && 'Video Merging'}
          </h2>
          <div className="flex flex-col items-center gap-6 max-w-sm w-full px-8 font-mono">
            <div className="w-full bg-zinc-100 h-1 border border-zinc-200">
              <div 
                className="h-full bg-black transition-all duration-1000" 
                style={{ 
                  width: status === GenerationStatus.SCRIPTING ? '25%' : 
                         status === GenerationStatus.VOICEOVER ? '55%' : '85%' 
                }} 
              />
            </div>
            <p className="text-zinc-400 text-center text-[10px] uppercase tracking-widest leading-loose">
              Processing your video... <br/>
              Synthesizing output for <span className="text-black">{language}</span>...
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-black p-10 space-y-10 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-8">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tighter mb-2 flex items-center gap-3">
                <CheckCircle2 size={28} />
                {status === GenerationStatus.COMPLETED ? 'Synthesis Successful' : 'Generation Failed'}
              </h2>
              <p className="text-zinc-400 text-xs font-bold uppercase tracking-widest">
                {status === GenerationStatus.COMPLETED 
                  ? 'Your property video with narration has been generated.' 
                  : 'There was an issue generating your video.'}
              </p>
            </div>
            <button 
              onClick={handleReset}
              className="px-8 py-3 bg-black text-white font-black text-xs uppercase tracking-widest border border-black hover:bg-white hover:text-black transition-all"
            >
              New Job
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div className="space-y-6">
              <div className="aspect-video bg-zinc-900 border border-black overflow-hidden relative shadow-inner">
                {generatedResult?.videoUrl ? (
                  <video 
                    src={generatedResult.videoUrl} 
                    controls 
                    className="w-full h-full object-cover"
                    poster={previewUrl || undefined}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-zinc-700 text-[10px] font-black uppercase tracking-widest">
                    {status === GenerationStatus.COMPLETED 
                      ? 'Video Processing...' 
                      : 'Preview Unavailable'}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-8">
              <div className="bg-zinc-50 border border-zinc-100 p-8">
                <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-6 border-b border-zinc-200 pb-2 inline-block">Property Details</h3>
                <h4 className="text-sm font-black uppercase tracking-tight mb-4">Property Description</h4>
                <div className="max-h-60 overflow-y-auto text-[11px] font-mono text-zinc-600 leading-relaxed pr-4">
                  {description}
                </div>
              </div>

              <div className="flex items-center gap-4">
                {generatedResult?.videoUrl && (
                  <a 
                    href={generatedResult.videoUrl} 
                    download
                    className="flex-1 bg-black text-white py-4 font-black uppercase tracking-widest text-[10px] hover:invert transition-all text-center"
                  >
                    Download Video (MP4)
                  </a>
                )}
                <button 
                  onClick={handleReset}
                  className="flex-1 bg-white text-black border border-black py-4 font-black uppercase tracking-widest text-[10px] hover:bg-zinc-50 transition-all"
                >
                  New Job
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoGenerator;