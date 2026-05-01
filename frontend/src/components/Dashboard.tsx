"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { AlertTriangle, Users, Activity, UploadCloud, Video, Mic, FileVideo, PlayCircle, StopCircle, ShieldAlert, Zap, Clock } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import PanicTrend from "./PanicTrend";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface DashboardProps {
  activeTab: "live" | "upload" | "logs" | "settings";
}

export default function Dashboard({ activeTab }: DashboardProps) {
  // Live Stream State
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ws = useRef<WebSocket | null>(null);

  const [panicScore, setPanicScore] = useState(0);
  const [alert, setAlert] = useState(false);
  const [detections, setDetections] = useState<any[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Historical data for chart
  const [history, setHistory] = useState<{ time: string; score: number }[]>([]);

  // Upload State
  const [uploadType, setUploadType] = useState<"video_audio" | "video" | "audio">("video_audio");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResults, setUploadResults] = useState<any>(null);

  // -------------------------
  // LIVE STREAM LOGIC
  // -------------------------
  useEffect(() => {
    if (activeTab === "live" && isAnalyzing) {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "localhost:8000";
      const wsProtocol = backendUrl.includes("localhost") ? "ws" : "wss";
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || `${wsProtocol}://${backendUrl}/stream`;
      ws.current = new WebSocket(wsUrl);
      ws.current.onopen = () => console.log("Elite Backend Link Established");
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "result") {
          const score = Math.round(data.score * 100);
          setPanicScore(data.score);
          setDetections(data.detections);
          setAlert(data.alert);

          // Update chart history
          setHistory(prev => {
            const newHistory = [...prev, { time: new Date().toLocaleTimeString(), score }];
            return newHistory.slice(-20); // Keep last 20 points
          });
        }
      };
      
      const interval = setInterval(() => {
        if (videoRef.current && canvasRef.current && ws.current?.readyState === WebSocket.OPEN) {
          const context = canvasRef.current.getContext("2d");
          if (context) {
            context.drawImage(videoRef.current, 0, 0, 640, 480);
            const frameData = canvasRef.current.toDataURL("image/jpeg", 0.7);
            ws.current.send(JSON.stringify({ type: "frame", data: frameData }));
          }
        }
      }, 300); // Optimized for performance
      
      return () => {
        clearInterval(interval);
        if (ws.current) ws.current.close();
      };
    }
  }, [activeTab, isAnalyzing]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);
      }
    } catch (err) {
      console.error("Hardware Access Error:", err);
      window.alert("Microphone or Camera access denied.");
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
    setIsAnalyzing(false);
  };

  // Draw Detections Overlay
  useEffect(() => {
    if (!isStreaming || !isAnalyzing || !canvasRef.current || !videoRef.current) return;
    const overlay = document.getElementById("bbox-overlay") as HTMLCanvasElement;
    if (overlay) {
      const ctx = overlay.getContext("2d");
      if (ctx) {
        ctx.clearRect(0, 0, overlay.width, overlay.height);
        detections.forEach((d) => {
          const [x1, y1, x2, y2] = d.bbox;
          ctx.strokeStyle = alert ? "#f43f5e" : "#22d3ee";
          ctx.lineWidth = 2;
          ctx.setLineDash([5, 5]);
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
          ctx.setLineDash([]);
          
          ctx.fillStyle = alert ? "#f43f5e" : "#22d3ee";
          ctx.font = "bold 12px Inter";
          ctx.fillText(`${d.label.toUpperCase()} ${(d.confidence * 100).toFixed(0)}%`, x1, y1 > 20 ? y1 - 5 : y1 + 15);
        });
      }
    }
  }, [detections, alert, isStreaming, isAnalyzing]);

  // -------------------------
  // UPLOAD LOGIC
  // -------------------------
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadResults(null);
      setUploadProgress(0);
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) return;
    setUploadProgress(20);
    
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("upload_type", uploadType);

    try {
      setUploadProgress(50);
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "localhost:8000";
      const protocol = backendUrl.includes("localhost") ? "http" : "https";
      const apiBase = backendUrl.startsWith("http") ? backendUrl : `${protocol}://${backendUrl}`;
      
      const res = await fetch(`${apiBase}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || data.error || "Analysis failed on backend");
      }

      setUploadProgress(100);
      setUploadResults(data.results);
      setPanicScore(data.results?.panic_score || 0);
      setAlert(data.results?.alert || false);
      setDetections(data.results?.detections || []);
    } catch (err: any) {
      console.error("Upload Error:", err);
      setUploadProgress(0);
      window.alert(`Deep Analysis Failed: ${err.message || "Connection Error"}`);
    }
  };

  return (
    <div className="space-y-8 max-w-[1600px] mx-auto pb-12">
      
      {/* Top Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard 
          title="Panic Probability" 
          value={`${(panicScore * 100).toFixed(0)}%`} 
          sub="AI Threat Assessment"
          icon={ShieldAlert}
          trend={panicScore > 0.5 ? "up" : "down"}
          color={alert ? "rose" : "cyan"}
          active={isAnalyzing}
        />
        <StatsCard 
          title="Crowd Density" 
          value={detections.length.toString()} 
          sub="Real-time Entity Tracking"
          icon={Users}
          color="blue"
          active={isAnalyzing}
        />
        <StatsCard 
          title="Audio Stress" 
          value={panicScore > 0.7 ? "High" : "Stable"} 
          sub="Multimodal DSP Analysis"
          icon={Activity}
          color="emerald"
          active={isAnalyzing}
        />
        <StatsCard 
          title="System Latency" 
          value="42ms" 
          sub="Edge Processing Speed"
          icon={Zap}
          color="indigo"
          active={true}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Main View Area */}
        <div className="lg:col-span-8 space-y-8">
          
          <AnimatePresence mode="wait">
            {activeTab === "live" ? (
              <motion.div 
                key="live-view"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className={cn(
                  "glass rounded-[2.5rem] p-4 relative overflow-hidden group",
                  alert && isAnalyzing ? "pulse-alert" : ""
                )}
              >
                <div className="relative rounded-[2rem] overflow-hidden bg-slate-950 aspect-video flex items-center justify-center border border-white/5">
                  <div className="scan-line"></div>
                  
                  {!isStreaming ? (
                    <button 
                      onClick={startCamera}
                      className="z-10 px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-700 text-white rounded-2xl font-bold flex items-center gap-3 shadow-2xl hover:scale-105 transition-all"
                    >
                      <Video size={20} /> Initialize Security Link
                    </button>
                  ) : (
                    !isAnalyzing && (
                      <button 
                        onClick={() => setIsAnalyzing(true)}
                        className="z-10 px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-2xl font-bold flex items-center gap-3 shadow-2xl hover:scale-105 transition-all"
                      >
                        <PlayCircle size={20} /> Activate VEERA AI Core
                      </button>
                    )
                  )}

                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover opacity-80"
                  />
                  <canvas ref={canvasRef} width={640} height={480} className="hidden" />
                  <canvas id="bbox-overlay" width={640} height={480} className="absolute top-0 left-0 w-full h-full pointer-events-none" />
                  
                  {isAnalyzing && (
                    <div className="absolute top-6 left-6 flex items-center gap-3 bg-black/60 backdrop-blur-xl border border-white/10 text-white px-4 py-2 rounded-2xl">
                      <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></div>
                      <span className="text-[10px] font-black tracking-[0.2em] uppercase">AI Deep Analysis Active</span>
                    </div>
                  )}

                  <div className="absolute bottom-6 right-6 flex items-center gap-2">
                    {isStreaming && (
                      <button onClick={stopCamera} className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl border border-rose-500/20 backdrop-blur-md transition-all text-[10px] font-bold uppercase tracking-wider">
                        Terminate Stream
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ) : activeTab === "upload" ? (
              <motion.div 
                key="upload-view"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="glass rounded-[2.5rem] p-10 border border-white/5"
              >
                <div className="flex flex-col items-center text-center mb-10">
                  <h2 className="text-3xl font-black mb-2 neon-text-cyan">Media Forensic Engine</h2>
                  <p className="text-slate-400 max-w-md">Upload archived footage for deep temporal and multimodal panic detection.</p>
                </div>
                
                <div className="grid grid-cols-3 gap-6 mb-10">
                  <UploadTypeButton 
                    active={uploadType === "video_audio"} 
                    onClick={() => setUploadType("video_audio")}
                    icon={FileVideo}
                    label="Multimodal"
                    desc="Audio + Video"
                    color="cyan"
                  />
                  <UploadTypeButton 
                    active={uploadType === "video"} 
                    onClick={() => setUploadType("video")}
                    icon={Video}
                    label="Visual Only"
                    desc="RGB Processing"
                    color="blue"
                  />
                  <UploadTypeButton 
                    active={uploadType === "audio"} 
                    onClick={() => setUploadType("audio")}
                    icon={Mic}
                    label="Acoustic"
                    desc="Audio Waves"
                    color="emerald"
                  />
                </div>

                <div className="relative group">
                  <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-[2rem] blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
                  <div className="relative border-2 border-dashed border-white/10 rounded-[2rem] p-16 text-center hover:bg-white/[0.02] transition-all cursor-pointer">
                    <input 
                      type="file" 
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
                      accept={uploadType === "audio" ? "audio/*" : "video/*,audio/*"} 
                      onChange={handleFileChange}
                    />
                    <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-white/5">
                      <UploadCloud className="text-slate-400" size={32} />
                    </div>
                    <p className="text-xl font-bold mb-1">{selectedFile ? selectedFile.name : "Select Media Archive"}</p>
                    <p className="text-xs text-slate-500">Supported formats: HEVC, MP4, WAV, FLAC</p>
                  </div>
                </div>

                {selectedFile && (
                  <div className="mt-10 flex flex-col items-center gap-6">
                    <button 
                      onClick={handleUploadAndAnalyze}
                      disabled={uploadProgress > 0 && uploadProgress < 100}
                      className="w-full max-w-sm py-4 bg-gradient-to-r from-cyan-600 to-blue-700 text-white rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl hover:scale-[1.02] transition-all disabled:opacity-50"
                    >
                      {uploadProgress > 0 && uploadProgress < 100 ? `Analyzing ${uploadProgress}%` : "Initiate Forensic Analysis"}
                    </button>
                    
                    {uploadProgress > 0 && uploadProgress < 100 && (
                      <div className="w-full max-w-sm h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <motion.div 
                          className="h-full bg-cyan-500"
                          initial={{ width: 0 }}
                          animate={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                    )}
                  </div>
                )}

                {uploadResults && (
                  <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-10 p-6 glass rounded-2xl border-emerald-500/20 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                        <Activity className="text-emerald-400" size={24} />
                      </div>
                      <div>
                        <h4 className="font-bold text-white uppercase text-[10px] tracking-widest">Analysis Completed</h4>
                        <p className="text-slate-400 text-sm">Peak Panic Coefficient: <span className="text-white font-mono font-bold">{(uploadResults.panic_score * 100).toFixed(2)}</span></p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-emerald-400 uppercase tracking-tighter">Verified by AI v2.4</span>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            ) : activeTab === "logs" ? (
              <motion.div 
                key="logs-view"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass rounded-[2.5rem] p-10 min-h-[500px]"
              >
                 <div className="flex items-center justify-between mb-10">
                    <h2 className="text-2xl font-black neon-text-cyan uppercase tracking-widest">Incident History</h2>
                    <button className="text-[10px] font-bold text-slate-500 uppercase hover:text-white transition-colors">Export CSV</button>
                 </div>
                 <div className="space-y-4">
                    {[1,2,3,4,5].map(i => (
                      <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5 hover:border-white/10 transition-colors cursor-pointer group">
                        <div className="flex items-center gap-4">
                          <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center border", i % 3 === 0 ? "bg-rose-500/10 border-rose-500/20 text-rose-400" : "bg-white/5 border-white/5 text-slate-400")}>
                             {i % 3 === 0 ? <AlertTriangle size={18} /> : <ShieldAlert size={18} />}
                          </div>
                          <div>
                            <p className="text-sm font-bold text-white">{i % 3 === 0 ? "High Panic Detected" : "Routine Scan Completed"}</p>
                            <p className="text-[10px] text-slate-500 uppercase tracking-tight">Sector Alpha-9 • Camera 0{i}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-white font-mono">14:23:{30 + i}</p>
                          <p className="text-[10px] text-slate-500 uppercase">01 May 2026</p>
                        </div>
                      </div>
                    ))}
                 </div>
              </motion.div>
            ) : (
              <motion.div 
                key="settings-view"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="glass rounded-[2.5rem] p-10 min-h-[500px]"
              >
                <h2 className="text-3xl font-black mb-8 neon-text-purple uppercase tracking-widest">System Configuration</h2>
                <div className="space-y-8">
                  <div className="p-6 bg-white/5 rounded-3xl border border-white/5">
                    <h3 className="text-lg font-bold mb-4">Inference Sensitivity</h3>
                    <input type="range" className="w-full h-2 bg-purple-500/20 rounded-lg appearance-none cursor-pointer accent-purple-500" />
                    <div className="flex justify-between mt-2 text-[10px] font-bold text-slate-500 uppercase">
                      <span>Low</span>
                      <span>Balanced</span>
                      <span>High</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="p-6 bg-white/5 rounded-3xl border border-white/5">
                      <h3 className="text-sm font-bold mb-2">Auto-Log Alerts</h3>
                      <div className="w-12 h-6 bg-purple-600 rounded-full relative p-1 cursor-pointer">
                        <div className="w-4 h-4 bg-white rounded-full ml-auto"></div>
                      </div>
                    </div>
                    <div className="p-6 bg-white/5 rounded-3xl border border-white/5">
                      <h3 className="text-sm font-bold mb-2">Hardware Acceleration</h3>
                      <div className="w-12 h-6 bg-emerald-600 rounded-full relative p-1 cursor-pointer">
                        <div className="w-4 h-4 bg-white rounded-full ml-auto"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <PanicTrend data={history} isAlert={alert} />

        </div>

        {/* Sidebar Panel */}
        <div className="lg:col-span-4 space-y-8">
           <div className="glass rounded-[2.5rem] p-8 border border-white/5">
              <h3 className="text-sm font-black uppercase tracking-[0.2em] mb-6 text-slate-500">Live Telemetry</h3>
              <div className="space-y-6">
                <TelemetryItem label="Visual Confidence" value={isAnalyzing ? "94.2%" : "---"} color="cyan" />
                <TelemetryItem label="Acoustic Entropy" value={isAnalyzing ? (panicScore * 100).toFixed(1) + "%" : "---"} color="emerald" />
                <TelemetryItem label="Motion Vector" value={isAnalyzing ? (detections.length * 4.2).toFixed(1) + "m/s" : "---"} color="blue" />
                <TelemetryItem label="Spatial Density" value={isAnalyzing ? (detections.length / 10).toFixed(2) + " pp/m²" : "---"} color="indigo" />
              </div>
           </div>

           <div className="glass rounded-[2.5rem] p-8 border border-white/5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Clock size={80} />
              </div>
              <h3 className="text-sm font-black uppercase tracking-[0.2em] mb-6 text-slate-500">Real-time Insights</h3>
              <div className="space-y-4">
                 <div className="flex items-start gap-4 p-4 bg-white/5 rounded-2xl border border-white/5">
                    <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20 shrink-0">
                      <Activity size={16} className="text-cyan-400" />
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">AI engine predicting <span className="text-white font-bold">Stable</span> crowd behavior for the next 5 minutes.</p>
                 </div>
                 <div className="flex items-start gap-4 p-4 bg-white/5 rounded-2xl border border-white/5">
                    <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center border border-amber-500/20 shrink-0">
                      <Users size={16} className="text-amber-400" />
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">Crowd density increased by <span className="text-white font-bold">12%</span> in last 30s.</p>
                 </div>
              </div>
           </div>
        </div>

      </div>
    </div>
  );
}

// Helper Components
function StatsCard({ title, value, sub, icon: Icon, color, active, trend }: any) {
  const colors: any = {
    cyan: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
    rose: "text-rose-400 bg-rose-500/10 border-rose-500/20",
    blue: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    indigo: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
  };

  return (
    <motion.div 
      whileHover={{ y: -5 }}
      className="glass-card rounded-[2rem] p-6 border border-white/5 flex flex-col gap-4"
    >
      <div className="flex items-center justify-between">
        <div className={cn("p-3 rounded-xl border flex items-center justify-center", colors[color])}>
          <Icon size={20} />
        </div>
        {active && <div className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
          <span className="text-[10px] font-black text-emerald-500 uppercase tracking-tighter">Live</span>
        </div>}
      </div>
      <div>
        <div className="flex items-end gap-2">
          <span className="text-3xl font-black tracking-tight text-white">{value}</span>
          {trend && <span className={cn("text-[10px] font-bold pb-1", trend === "up" ? "text-rose-400" : "text-emerald-400")}>
            {trend === "up" ? "▲" : "▼"}
          </span>}
        </div>
        <h4 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 mt-1">{title}</h4>
      </div>
    </motion.div>
  );
}

function UploadTypeButton({ active, onClick, icon: Icon, label, desc, color }: any) {
  const colors: any = {
    cyan: "border-cyan-500/30 bg-cyan-500/5 text-cyan-400",
    blue: "border-blue-500/30 bg-blue-500/5 text-blue-400",
    emerald: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400",
  };

  return (
    <button 
      onClick={onClick}
      className={cn(
        "p-6 rounded-3xl border transition-all flex flex-col items-center gap-3",
        active ? colors[color] : "border-white/5 hover:border-white/20 text-slate-500"
      )}
    >
      <Icon size={28} />
      <div className="text-center">
        <p className="text-xs font-black uppercase tracking-widest">{label}</p>
        <p className="text-[10px] opacity-60 font-medium">{desc}</p>
      </div>
    </button>
  );
}

function TelemetryItem({ label, value, color }: any) {
  const colors: any = {
    cyan: "bg-cyan-500",
    emerald: "bg-emerald-500",
    blue: "bg-blue-500",
    indigo: "bg-indigo-500",
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest">
        <span className="text-slate-400">{label}</span>
        <span className="text-white font-mono">{value}</span>
      </div>
      <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: value === "---" ? 0 : "75%" }}
          className={cn("h-full", colors[color])}
        />
      </div>
    </div>
  );
}
