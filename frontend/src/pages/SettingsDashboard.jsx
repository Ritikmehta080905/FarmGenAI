import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Settings, Sliders, Server, ShieldAlert, BookOpen, ToggleRight, ArrowLeft } from 'lucide-react';
import FeatureFlags from '../components/settings/FeatureFlags';
import AIConfigPanel from '../components/settings/AIConfigPanel';
import SystemConfigPanel from '../components/settings/SystemConfigPanel';

export default function SettingsDashboard() {
  const [activeTab, setActiveTab] = useState('flags');

  const menuItems = [
    { id: 'flags', label: 'Feature Flags', icon: <ToggleRight size={18} /> },
    { id: 'ai', label: 'AI Hyperparameters', icon: <Sliders size={18} /> },
    { id: 'system', label: 'System & Security', icon: <Server size={18} /> },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <Link to="/" className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-purple-600 mb-2 transition">
          <ArrowLeft size={16} className="mr-1" /> Back to Dashboard
        </Link>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Settings className="text-blue-600" /> Enterprise Configuration Center
        </h1>
        <p className="text-slate-500 mt-1">Configure global platform behavior, AI routing rules, and security policies without deploying code.</p>
      </div>

      {/* Main Layout: Left Sidebar + Right Content */}
      <div className="flex flex-col md:flex-row gap-6">
        
        {/* Sidebar Navigation */}
        <div className="w-full md:w-64 shrink-0 space-y-2">
          {menuItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-bold transition text-sm ${
                activeTab === item.id 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-100 hover:border-slate-200'
              }`}
            >
              {item.icon} {item.label}
            </button>
          ))}
          
          <div className="mt-8 pt-8 border-t border-slate-200 space-y-2">
            <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl font-bold text-sm bg-white text-slate-600 border border-slate-100 opacity-50 cursor-not-allowed">
              <BookOpen size={18} /> Localization (WIP)
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl font-bold text-sm bg-white text-slate-600 border border-slate-100 opacity-50 cursor-not-allowed">
              <ShieldAlert size={18} /> Import / Export
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 bg-white p-6 md:p-8 rounded-2xl shadow-sm border border-slate-100">
          {activeTab === 'flags' && <FeatureFlags />}
          {activeTab === 'ai' && <AIConfigPanel />}
          {activeTab === 'system' && <SystemConfigPanel />}
        </div>

      </div>

    </div>
  );
}
