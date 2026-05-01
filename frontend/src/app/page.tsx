"use client";

import { useState } from "react";
import Dashboard from "@/components/Dashboard";
import Sidebar from "@/components/Sidebar";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"live" | "upload" | "logs" | "settings">("live");

  return (
    <main className="min-h-screen flex bg-[#020617] text-slate-100 selection:bg-cyan-500/30">
      {/* Dynamic Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-600/10 blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-rose-600/10 blur-[120px]"></div>
      </div>

      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex-1 relative z-10 flex flex-col overflow-hidden h-screen">
        <header className="h-16 flex items-center justify-between px-8 glass border-b border-white/5 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-xs font-bold uppercase tracking-widest text-slate-400">System Live</span>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="flex flex-col items-end">
              <span className="text-[10px] text-slate-500 uppercase tracking-tighter">Current Deployment</span>
              <span className="text-xs font-bold text-cyan-400">VEERA_ALPHA_V2</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-slate-800 to-slate-700 border border-white/10 flex items-center justify-center text-[10px] font-bold">
              IDP
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <Dashboard activeTab={activeTab} />
        </div>
      </div>
    </main>
  );
}
