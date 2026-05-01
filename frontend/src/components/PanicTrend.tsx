"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { motion } from 'framer-motion';

interface PanicTrendProps {
  data: { time: string; score: number }[];
  isAlert: boolean;
}

export default function PanicTrend({ data, isAlert }: PanicTrendProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full h-full min-h-[300px] glass p-6 rounded-3xl"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          Real-time Panic Dynamics
          <span className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 text-[10px] font-bold rounded-full border border-cyan-500/20 uppercase tracking-tighter">AI Analysis</span>
        </h3>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-cyan-500"></div>
            <span className="text-gray-400">Probability Score</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></div>
            <span className="text-rose-400">Critical Threshold</span>
          </div>
        </div>
      </div>

      <div className="w-full h-[220px] min-w-0 min-h-0">
        <ResponsiveContainer width="100%" height="100%" key={data.length}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isAlert ? "#f43f5e" : "#06b6d4"} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={isAlert ? "#f43f5e" : "#06b6d4"} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
            <XAxis 
              dataKey="time" 
              hide 
            />
            <YAxis 
              domain={[0, 100]} 
              stroke="rgba(255,255,255,0.2)" 
              fontSize={10}
              tickFormatter={(val) => `${val}%`}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                borderColor: 'rgba(255,255,255,0.1)',
                borderRadius: '12px',
                backdropFilter: 'blur(8px)',
                fontSize: '12px',
                color: '#fff'
              }}
              itemStyle={{ color: isAlert ? '#f43f5e' : '#22d3ee' }}
            />
            <Area 
              type="monotone" 
              dataKey="score" 
              stroke={isAlert ? "#f43f5e" : "#22d3ee"} 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorScore)" 
              animationDuration={500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
