import React from 'react';
import { Server, Lock, HardDrive, Save } from 'lucide-react';

export default function SystemConfigPanel() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-800">System & Infrastructure Settings</h2>
          <p className="text-sm text-slate-500 mt-1">Manage Redis caching, Security protocols, and Data Retention.</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold text-sm transition">
          <Save size={16} /> Save System Settings
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Security Configuration */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6">
          <h3 className="font-bold text-slate-800 flex items-center gap-2 border-b pb-2"><Lock size={18} className="text-amber-600"/> Security & Auth</h3>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">JWT Expiration (mins)</label>
                <input type="number" defaultValue="60" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Refresh Token (days)</label>
                <input type="number" defaultValue="7" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Maximum Login Attempts</label>
              <input type="number" defaultValue="5" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <p className="text-xs text-slate-500 mt-1">Locks account for 30 minutes after threshold is reached.</p>
            </div>
          </div>
        </div>

        {/* Redis Configuration */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6">
          <h3 className="font-bold text-slate-800 flex items-center gap-2 border-b pb-2"><Server size={18} className="text-red-600"/> Redis Streams & Caching</h3>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Session Cache TTL (hrs)</label>
                <input type="number" defaultValue="24" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Market Data TTL (mins)</label>
                <input type="number" defaultValue="15" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Max Consumer Group Backlog</label>
              <input type="number" defaultValue="10000" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              <p className="text-xs text-slate-500 mt-1">Dead Letter Queue threshold for failed WebSocket messages.</p>
            </div>
          </div>
        </div>

        {/* Storage Configuration */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6 md:col-span-2">
          <h3 className="font-bold text-slate-800 flex items-center gap-2 border-b pb-2"><HardDrive size={18} className="text-blue-600"/> Data Retention & Storage Policy</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Negotiation History (Days)</label>
              <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option>90 Days</option>
                <option>1 Year</option>
                <option>Indefinite (Compliance)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Audit Log Retention</label>
              <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option>3 Years (Standard)</option>
                <option>5 Years (Strict Compliance)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Max Upload File Size (MB)</label>
              <input type="number" defaultValue="10" className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
