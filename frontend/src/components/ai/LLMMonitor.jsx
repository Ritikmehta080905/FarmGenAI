import React from 'react';
import { Cpu, Cloud, Zap, Server, ShieldAlert } from 'lucide-react';
import ChartCard from '../ui/ChartCard';

const mockTokenUsage = [
  { name: '00:00', value: 120000 },
  { name: '04:00', value: 85000 },
  { name: '08:00', value: 240000 },
  { name: '12:00', value: 450000 },
  { name: '16:00', value: 380000 },
  { name: '20:00', value: 150000 },
];

export default function LLMMonitor() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* Model Split KPI */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Cloud LLM (Gemini) */}
        <div className="bg-blue-900 p-6 rounded-2xl shadow-sm border border-blue-800 text-white flex flex-col h-full">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-xl font-bold flex items-center gap-2"><Cloud className="text-blue-400"/> Gemini 1.5 Pro</h3>
              <p className="text-blue-200 text-sm mt-1">Primary Orchestration & Complex Reasoning</p>
            </div>
            <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 text-xs font-bold rounded-lg border border-emerald-500/30">ONLINE</span>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-auto">
             <div>
               <p className="text-xs text-blue-300 font-bold uppercase tracking-wider mb-1">Daily Tokens</p>
               <p className="text-2xl font-black">2.4M</p>
             </div>
             <div>
               <p className="text-xs text-blue-300 font-bold uppercase tracking-wider mb-1">Est. Cost</p>
               <p className="text-2xl font-black text-amber-400">$18.50</p>
             </div>
             <div>
               <p className="text-xs text-blue-300 font-bold uppercase tracking-wider mb-1">Avg Latency</p>
               <p className="text-xl font-bold">450ms</p>
             </div>
             <div>
               <p className="text-xs text-blue-300 font-bold uppercase tracking-wider mb-1">Context Window</p>
               <p className="text-xl font-bold">128K</p>
             </div>
          </div>
        </div>

        {/* Local LLM (Ollama) */}
        <div className="bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-800 text-white flex flex-col h-full">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-xl font-bold flex items-center gap-2"><Cpu className="text-slate-400"/> Ollama (Llama3-8B)</h3>
              <p className="text-slate-400 text-sm mt-1">Fallback & Local Data Extraction</p>
            </div>
            <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 text-xs font-bold rounded-lg border border-emerald-500/30">ONLINE</span>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-auto">
             <div>
               <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">GPU VRAM Used</p>
               <p className="text-2xl font-black text-purple-400">6.8 GB</p>
             </div>
             <div>
               <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Tokens/Sec</p>
               <p className="text-2xl font-black">85 t/s</p>
             </div>
             <div>
               <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Avg Latency</p>
               <p className="text-xl font-bold">120ms</p>
             </div>
             <div>
               <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Requests Handled</p>
               <p className="text-xl font-bold">14,200</p>
             </div>
          </div>
        </div>
      </div>

      {/* Main Charts area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[350px]">
          <ChartCard 
            title="Global Token Consumption" 
            subtitle="Combined input/output tokens over 24h"
            data={mockTokenUsage} 
            color="#3b82f6" 
            height={260}
          />
        </div>
        
        {/* MCP Server Box */}
        <div className="lg:col-span-1 bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex flex-col">
          <h3 className="font-bold text-slate-800 border-b pb-2 mb-4 flex items-center gap-2">
            <Server size={18} className="text-purple-500"/> MCP Server Health
          </h3>
          <div className="space-y-4 flex-1">
            <div className="flex justify-between items-center bg-slate-50 p-3 rounded-xl border border-slate-100">
               <span className="text-sm font-medium text-slate-600">Weather API Tool</span>
               <span className="text-xs font-bold text-emerald-600">OK</span>
            </div>
            <div className="flex justify-between items-center bg-slate-50 p-3 rounded-xl border border-slate-100">
               <span className="text-sm font-medium text-slate-600">Market Price DB</span>
               <span className="text-xs font-bold text-emerald-600">OK</span>
            </div>
            <div className="flex justify-between items-center bg-red-50 p-3 rounded-xl border border-red-100">
               <span className="text-sm font-medium text-slate-600 flex items-center gap-1"><ShieldAlert size={14} className="text-red-500"/> Agmarknet Crawler</span>
               <span className="text-xs font-bold text-red-600">FAIL</span>
            </div>
            <div className="flex justify-between items-center bg-slate-50 p-3 rounded-xl border border-slate-100">
               <span className="text-sm font-medium text-slate-600">Zod Validator</span>
               <span className="text-xs font-bold text-emerald-600">OK</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
