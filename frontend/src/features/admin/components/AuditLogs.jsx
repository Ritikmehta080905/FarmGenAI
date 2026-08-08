import React, { useState } from 'react';
import { Search, Filter, ShieldAlert, Download } from 'lucide-react';
import DataTable from '@/components/ui/DataTable';

const mockAuditLogs = [
  { id: 'LOG-001', timestamp: '2026-08-07 11:42:01', actor: 'Root System', action: 'SCALE_UP', resource: 'WebSocket Pool', status: 'SUCCESS' },
  { id: 'LOG-002', timestamp: '2026-08-07 11:38:22', actor: 'RL Agent', action: 'POLICY_UPDATE', resource: 'Model v2.4.1', status: 'SUCCESS' },
  { id: 'LOG-003', timestamp: '2026-08-07 10:15:05', actor: 'Admin Root', action: 'SUSPEND_USER', resource: 'USR-103', status: 'SUCCESS' },
  { id: 'LOG-004', timestamp: '2026-08-07 09:12:44', actor: 'Auth Service', action: 'FAILED_LOGIN', resource: 'admin@farmgen.ai', status: 'FAILURE' },
  { id: 'LOG-005', timestamp: '2026-08-07 08:30:12', actor: 'Escrow Service', action: 'FUNDS_LOCKED', resource: 'Deal #NEG-99C12', status: 'SUCCESS' },
];

export default function AuditLogs() {
  const [searchTerm, setSearchTerm] = useState('');

  const columns = [
    { header: 'Log ID', accessor: 'id', className: 'font-mono text-[10px] text-slate-400 w-24' },
    { header: 'Timestamp', accessor: 'timestamp', className: 'font-mono text-xs text-slate-600' },
    { header: 'Actor / Identity', accessor: 'actor', className: 'font-bold text-slate-800' },
    { 
      header: 'Event Action', 
      accessor: 'action',
      render: (row) => (
        <span className={`px-2 py-1 text-[10px] font-bold tracking-wider rounded uppercase ${
          row.action.includes('FAILED') || row.action.includes('SUSPEND') ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'
        }`}>
          {row.action}
        </span>
      )
    },
    { header: 'Target Resource', accessor: 'resource', className: 'text-sm text-slate-600 font-medium' },
    { 
      header: 'Status', 
      accessor: 'status',
      render: (row) => (
        <span className={`flex items-center gap-1.5 text-xs font-bold ${
          row.status === 'SUCCESS' ? 'text-emerald-600' : 'text-red-600'
        }`}>
          <div className={`w-1.5 h-1.5 rounded-full ${row.status === 'SUCCESS' ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
          {row.status}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900 p-4 rounded-2xl shadow-sm border border-slate-800">
        <div className="flex items-center gap-3">
           <ShieldAlert className="text-red-500" />
           <span className="text-white font-bold tracking-wide">Immutable Audit Trail</span>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative w-full sm:w-64">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search logs..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-red-500 text-sm text-white placeholder-slate-500"
            />
          </div>
          <button className="p-2 text-slate-400 hover:text-white bg-slate-800 rounded-lg transition" title="Advanced Filters">
            <Filter size={18} />
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-bold text-slate-300 hover:text-white bg-slate-800 border border-slate-700 hover:border-slate-500 rounded-lg transition">
            <Download size={14} /> Export
          </button>
        </div>
      </div>

      {/* Main Table */}
      <div className="h-[600px]">
        <DataTable 
          title="System Event Registry" 
          columns={columns} 
          data={mockAuditLogs} 
        />
      </div>

    </div>
  );
}
