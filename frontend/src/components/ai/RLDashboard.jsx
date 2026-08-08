import React from 'react';
import { Target, TrendingUp, Cpu, Award } from 'lucide-react';
import ChartCard from '../ui/ChartCard';

const mockRewards = [
  { name: 'Ep 100', value: -120 },
  { name: 'Ep 200', value: 45 },
  { name: 'Ep 300', value: 150 },
  { name: 'Ep 400', value: 290 },
  { name: 'Ep 500', value: 310 },
  { name: 'Ep 600', value: 480 },
  { name: 'Ep 700', value: 520 },
];

export default function RLDashboard() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-800 text-white flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-400"><Target size={18}/> <span className="font-bold text-sm">Active Policy Version</span></div>
          <p className="text-3xl font-black">v2.4.1</p>
          <p className="text-xs text-emerald-400 border border-emerald-400/20 bg-emerald-400/10 px-2 py-0.5 rounded w-max">Stable (Converged)</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><TrendingUp size={18}/> <span className="font-bold text-sm">Epsilon (Exploration)</span></div>
          <p className="text-3xl font-black text-slate-800">0.05</p>
          <p className="text-xs text-slate-500">95% Exploitation Rate</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Cpu size={18}/> <span className="font-bold text-sm">Total Episodes</span></div>
          <p className="text-3xl font-black text-slate-800">14,204</p>
          <p className="text-xs text-slate-500">Simulated + Real Deals</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Award size={18}/> <span className="font-bold text-sm">Cumulative Reward</span></div>
          <p className="text-3xl font-black text-emerald-600">+1.2M</p>
          <p className="text-xs text-slate-500">Normalized Value</p>
        </div>
      </div>

      {/* Main Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[400px]">
          <ChartCard 
            title="Reinforcement Learning Convergence (PPO)" 
            subtitle="Tracking cumulative rewards over training episodes. Higher is better."
            data={mockRewards} 
            color="#8b5cf6" 
            height={310}
          />
        </div>
        
        {/* State Space Definition */}
        <div className="lg:col-span-1 bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex flex-col h-full">
          <h3 className="font-bold text-slate-800 border-b pb-2 mb-4">RL State-Action Space</h3>
          <div className="space-y-4 flex-1">
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">State Vector (Inputs)</p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600 font-medium">Market Price</span>
                <span className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600 font-medium">Weather Risk</span>
                <span className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600 font-medium">Storage Cap</span>
                <span className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600 font-medium">Opponent Trust</span>
              </div>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1 mt-4">Action Space (Outputs)</p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-blue-50 border border-blue-100 rounded text-xs text-blue-700 font-bold">Accept</span>
                <span className="px-2 py-1 bg-amber-50 border border-amber-100 rounded text-xs text-amber-700 font-bold">Counter (P_new)</span>
                <span className="px-2 py-1 bg-red-50 border border-red-100 rounded text-xs text-red-700 font-bold">Walk Away</span>
              </div>
            </div>
            <div className="p-3 bg-purple-50 rounded-xl mt-4">
              <p className="text-xs font-bold text-purple-600 mb-1">Reward Function</p>
              <p className="text-xs font-mono text-purple-800 break-words">R = (Final_Price - Min_Price) * Volume - Time_Penalty</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
