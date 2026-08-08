import React from 'react';
import { Bot, Zap, Clock, Activity, Cpu } from 'lucide-react';
import DataTable from '../ui/DataTable';

const mockAgents = [
  { id: 'agt-1', name: 'Coordinator Agent', status: 'ACTIVE', latency: '42ms', memory: '128MB', throughput: '450 req/s', errors: '0' },
  { id: 'agt-2', name: 'Farmer Agent', status: 'ACTIVE', latency: '85ms', memory: '256MB', throughput: '120 req/s', errors: '0' },
  { id: 'agt-3', name: 'Buyer Agent', status: 'ACTIVE', latency: '92ms', memory: '256MB', throughput: '115 req/s', errors: '2' },
  { id: 'agt-4', name: 'Market Intel Agent', status: 'ACTIVE', latency: '210ms', memory: '512MB', throughput: '45 req/s', errors: '0' },
  { id: 'agt-5', name: 'Weather Agent', status: 'IDLE', latency: '15ms', memory: '64MB', throughput: '10 req/s', errors: '0' },
  { id: 'agt-6', name: 'Warehouse Agent', status: 'ACTIVE', latency: '112ms', memory: '128MB', throughput: '80 req/s', errors: '0' },
  { id: 'agt-7', name: 'Transport Agent', status: 'ACTIVE', latency: '145ms', memory: '128MB', throughput: '85 req/s', errors: '0' },
  { id: 'agt-8', name: 'Trust Scoring Agent', status: 'ACTIVE', latency: '35ms', memory: '256MB', throughput: '300 req/s', errors: '0' },
  { id: 'agt-9', name: 'RL Agent', status: 'TRAINING', latency: '850ms', memory: '2.4GB', throughput: '5 req/s', errors: '0' },
  { id: 'agt-10', name: 'Reflection Agent', status: 'ACTIVE', latency: '450ms', memory: '1.2GB', throughput: '15 req/s', errors: '0' },
  { id: 'agt-11', name: 'Validator Agent', status: 'ACTIVE', latency: '25ms', memory: '128MB', throughput: '450 req/s', errors: '0' },
  { id: 'agt-12', name: 'Agreement Agent', status: 'IDLE', latency: '45ms', memory: '64MB', throughput: '2 req/s', errors: '0' },
  { id: 'agt-13', name: 'Recommendation Agent', status: 'ACTIVE', latency: '180ms', memory: '512MB', throughput: '40 req/s', errors: '1' },
];

export default function AgentMonitor() {
  const columns = [
    { header: 'Agent Identity', accessor: 'name', className: 'font-bold text-slate-800' },
    { 
      header: 'Status', 
      accessor: 'status',
      render: (row) => (
        <span className={`px-2 py-1 text-[10px] font-bold tracking-wider rounded uppercase ${
          row.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-700' :
          row.status === 'TRAINING' ? 'bg-purple-100 text-purple-700 animate-pulse' : 'bg-slate-100 text-slate-700'
        }`}>
          {row.status}
        </span>
      )
    },
    { header: 'Avg Latency', accessor: 'latency', className: 'font-mono text-sm text-slate-600' },
    { header: 'Memory Footprint', accessor: 'memory', className: 'font-mono text-sm text-slate-600' },
    { header: 'Throughput', accessor: 'throughput', className: 'font-mono text-sm text-slate-600' },
    { 
      header: 'Errors (1h)', 
      accessor: 'errors', 
      render: (row) => (
        <span className={`font-bold ${parseInt(row.errors) > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
          {row.errors}
        </span>
      ) 
    },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* Fleet KPI */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-800 text-white flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-400"><Bot size={18}/> <span className="font-bold text-sm">Active Fleet</span></div>
          <p className="text-3xl font-black text-emerald-400">13 / 13</p>
          <p className="text-xs text-slate-500">All LangGraph Nodes Online</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Clock size={18}/> <span className="font-bold text-sm">Avg Graph Latency</span></div>
          <p className="text-3xl font-black text-slate-800">1.2s</p>
          <p className="text-xs text-slate-500">Per Negotiation Turn</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Activity size={18}/> <span className="font-bold text-sm">Success Rate</span></div>
          <p className="text-3xl font-black text-emerald-600">99.8%</p>
          <p className="text-xs text-slate-500">Last 10,000 requests</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Cpu size={18}/> <span className="font-bold text-sm">Fleet Memory</span></div>
          <p className="text-3xl font-black text-slate-800">5.8 GB</p>
          <p className="text-xs text-slate-500">Total RAM Allocated</p>
        </div>
      </div>

      {/* Main Table */}
      <div className="h-[600px]">
        <DataTable 
          title="Agent Fleet Telemetry" 
          columns={columns} 
          data={mockAgents} 
        />
      </div>

    </div>
  );
}
