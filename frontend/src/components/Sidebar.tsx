"use client";

import { LayoutDashboard, Video, UploadCloud, History, Settings, ShieldCheck, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: "live" | "upload" | "logs") => void;
}

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const menuItems = [
    { id: "live", label: "Live Monitoring", icon: Video, color: "text-cyan-400" },
    { id: "upload", label: "Media Analysis", icon: UploadCloud, color: "text-emerald-400" },
    { id: "logs", label: "Incident Logs", icon: History, color: "text-indigo-400" },
    { id: "settings", label: "System Settings", icon: Settings, color: "text-purple-400" },
  ];

  return (
    <aside className="w-64 h-screen glass border-r border-white/5 sticky top-0 flex flex-col p-4 z-50">
      <div className="flex items-center gap-3 px-2 mb-10 mt-2">
        <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.4)]">
          <ShieldCheck size={24} className="text-white" />
        </div>
        <h1 className="text-xl font-black tracking-tight neon-text-cyan">VEERA_AI</h1>
      </div>

      <nav className="flex-1 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id as any)}
            className={cn(
              "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
              activeTab === item.id 
                ? "bg-white/10 text-white shadow-[inset_0_0_20px_rgba(255,255,255,0.05)]" 
                : "text-gray-400 hover:text-white hover:bg-white/5"
            )}
          >
            {activeTab === item.id && (
              <motion.div 
                layoutId="active-pill"
                className="absolute left-0 w-1 h-6 bg-cyan-500 rounded-full"
              />
            )}
            <item.icon size={20} className={cn("transition-colors", activeTab === item.id ? item.color : "group-hover:text-white")} />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="mt-auto space-y-2 pt-4 border-t border-white/5">

        
        <div className="mt-4 p-4 rounded-2xl bg-gradient-to-br from-gray-900 to-black border border-white/5">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={14} className="text-cyan-400 animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">System Health</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Inference Core</span>
            <span className="text-xs font-mono text-emerald-400">98%</span>
          </div>
          <div className="w-full bg-white/5 h-1 rounded-full mt-2 overflow-hidden">
            <div className="bg-emerald-500 h-full w-[98%]"></div>
          </div>
        </div>
      </div>
    </aside>
  );
}
