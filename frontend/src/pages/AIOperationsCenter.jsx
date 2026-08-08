import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Brain, Activity, BrainCircuit, LineChart, ArrowLeft, Bot, Cpu } from 'lucide-react';
import SystemTelemetry from '../components/ai/SystemTelemetry';
import RLDashboard from '../components/ai/RLDashboard';
import ReflectionPanel from '../components/ai/ReflectionPanel';
import AgentMonitor from '../components/ai/AgentMonitor';
import LLMMonitor from '../components/ai/LLMMonitor';

export default function AIOperationsCenter() {
  const [activeTab, setActiveTab] = useState('telemetry');

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex justify-between items-center">
        <div>
          <Link to="/" className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-purple-600 mb-2 transition">
            <ArrowLeft size={16} className="mr-1" /> Back to Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Brain className="text-purple-600" /> AI Operations & Transparency Center
          </h1>
          <p className="text-slate-500 mt-1">Deep visibility into System Health, Reinforcement Learning, Multi-Agent Fleet, and LLM Economics.</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex bg-white rounded-xl shadow-sm border border-slate-100 p-1 overflow-x-auto whitespace-nowrap">
        <button 
          onClick={() => setActiveTab('telemetry')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-bold text-sm transition ${
            activeTab === 'telemetry' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
          }`}
        >
          <Activity size={18} /> System Telemetry
        </button>
        <button 
          onClick={() => setActiveTab('agents')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-bold text-sm transition ${
            activeTab === 'agents' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
          }`}
        >
          <Bot size={18} /> Agent Fleet Health
        </button>
        <button 
          onClick={() => setActiveTab('llms')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-bold text-sm transition ${
            activeTab === 'llms' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
          }`}
        >
          <Cpu size={18} /> LLM & MCP Analytics
        </button>
        <button 
          onClick={() => setActiveTab('rl')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-bold text-sm transition ${
            activeTab === 'rl' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
          }`}
        >
          <LineChart size={18} /> RL Convergence
        </button>
        <button 
          onClick={() => setActiveTab('reflection')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-bold text-sm transition ${
            activeTab === 'reflection' ? 'bg-amber-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
          }`}
        >
          <BrainCircuit size={18} /> Agent Reflection
        </button>
      </div>

      {/* Tab Content Area */}
      <div className="mt-6">
        {activeTab === 'telemetry' && <SystemTelemetry />}
        {activeTab === 'agents' && <AgentMonitor />}
        {activeTab === 'llms' && <LLMMonitor />}
        {activeTab === 'rl' && <RLDashboard />}
        {activeTab === 'reflection' && <ReflectionPanel />}
      </div>

    </div>
  );
}
