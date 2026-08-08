import React, { useState } from 'react';
import { ShieldAlert, Users, Activity, TrendingUp, Cpu, Server, ClipboardList } from 'lucide-react';
import StatCard from '../components/ui/StatCard';
import ChartCard from '../components/ui/ChartCard';
import PriceChart from '../components/ui/PriceChart';
import UserManagement from '../components/admin/UserManagement';
import AuditLogs from '../components/admin/AuditLogs';

// Mock Data for Overview Tab
const userGrowthData = [
  { name: 'Jan', value: 400 },
  { name: 'Feb', value: 550 },
  { name: 'Mar', value: 800 },
  { name: 'Apr', value: 1100 },
  { name: 'May', value: 1245 },
];

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <ShieldAlert className="text-red-600" /> Enterprise Admin Console
          </h1>
          <p className="text-slate-500 mt-1">Platform monitoring, dispute resolution, user management, and compliance logs.</p>
        </div>
        <div className="flex items-center gap-4 w-full md:w-auto">
          <div className="px-4 py-2 bg-slate-50 border rounded-lg text-sm font-medium text-slate-600 flex items-center gap-2 w-full justify-center">
            <Activity size={16} className="text-emerald-500 animate-pulse" /> 
            System Status: Healthy
          </div>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="flex flex-wrap sm:flex-nowrap bg-white rounded-xl shadow-sm border border-slate-100 p-1 gap-1">
        <button 
          onClick={() => setActiveTab('overview')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-sm transition ${
            activeTab === 'overview' ? 'bg-red-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
          }`}
        >
          <Activity size={18} /> Platform Overview
        </button>
        <button 
          onClick={() => setActiveTab('users')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-sm transition ${
            activeTab === 'users' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
          }`}
        >
          <Users size={18} /> User Management
        </button>
        <button 
          onClick={() => setActiveTab('audit')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-sm transition ${
            activeTab === 'audit' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
          }`}
        >
          <ClipboardList size={18} /> Audit Logs
        </button>
      </div>

      {/* Tab Content Area */}
      <div className="mt-6">
        
        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
            {/* KPI Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard icon={<Users />} title="Active Users" value="1,245" trend="+12 today" color="blue" />
              <StatCard icon={<TrendingUp />} title="Total Negotiations" value="482" trend="34 active right now" color="emerald" />
              <StatCard icon={<Server />} title="Redis Streams" value="8,402" trend="msg/sec throughput" color="purple" />
              <StatCard icon={<Cpu />} title="RL Agent Memory" value="2.4 GB" trend="stable" color="amber" />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="h-[350px]">
                <ChartCard 
                  title="User Growth" 
                  subtitle="Registered farmers and buyers over 5 months"
                  data={userGrowthData} 
                  color="#3b82f6" 
                  height={260}
                />
              </div>
              
              <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex flex-col h-[350px]">
                <h2 className="font-bold text-lg text-slate-800 mb-2 flex items-center gap-2">
                   Platform Price Index (30 Days)
                </h2>
                <p className="text-sm text-slate-500 mb-4">Aggregated moving average for top commodities.</p>
                <div className="flex-1">
                  <PriceChart />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: USER MANAGEMENT */}
        {activeTab === 'users' && <UserManagement />}

        {/* TAB 3: AUDIT LOGS */}
        {activeTab === 'audit' && <AuditLogs />}

      </div>

    </div>
  );
}
