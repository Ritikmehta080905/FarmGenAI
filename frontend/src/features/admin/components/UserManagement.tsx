import React, { useState } from 'react';
import { Users, Search, Edit2, Ban, RefreshCw, Download } from 'lucide-react';
import DataTable from '@/components/ui/DataTable';

const mockUsers = [
  { id: 'USR-101', name: 'Ramesh Patil', role: 'FARMER', status: 'ACTIVE', lastLogin: '2026-08-07 10:45 AM', deals: 12 },
  { id: 'USR-102', name: 'AgroFresh Corp', role: 'BUYER', status: 'ACTIVE', lastLogin: '2026-08-07 09:12 AM', deals: 45 },
  { id: 'USR-103', name: 'Nashik Cold Storage', role: 'WAREHOUSE', status: 'SUSPENDED', lastLogin: '2026-08-01 14:22 PM', deals: 104 },
  { id: 'USR-104', name: 'Swift Logistics', role: 'TRANSPORT', status: 'ACTIVE', lastLogin: '2026-08-07 11:05 AM', deals: 89 },
  { id: 'USR-105', name: 'Admin Root', role: 'ADMIN', status: 'ACTIVE', lastLogin: '2026-08-07 08:00 AM', deals: 0 },
];

export default function UserManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  
  const columns = [
    { header: 'User ID', accessor: 'id', className: 'font-mono text-xs text-slate-500' },
    { header: 'Name / Organization', accessor: 'name', className: 'font-bold text-slate-800' },
    { 
      header: 'Role', 
      accessor: 'role',
      render: (row) => (
        <span className={`px-2 py-1 text-[10px] font-bold tracking-wider rounded uppercase ${
          row.role === 'ADMIN' ? 'bg-purple-100 text-purple-700' :
          row.role === 'FARMER' ? 'bg-emerald-100 text-emerald-700' :
          row.role === 'BUYER' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-700'
        }`}>
          {row.role}
        </span>
      )
    },
    { 
      header: 'Status', 
      accessor: 'status',
      render: (row) => (
        <span className={`px-2 py-1 text-[10px] font-bold tracking-wider rounded uppercase ${
          row.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          {row.status}
        </span>
      )
    },
    { header: 'Last Login', accessor: 'lastLogin', className: 'text-sm text-slate-500' },
    { header: 'Total Deals', accessor: 'deals', className: 'text-sm font-medium text-slate-700' },
    {
      header: 'Actions',
      accessor: 'actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button className="p-1.5 text-blue-600 hover:bg-blue-50 rounded" title="Edit User"><Edit2 size={16}/></button>
          <button className="p-1.5 text-amber-600 hover:bg-amber-50 rounded" title="Reset Password"><RefreshCw size={16}/></button>
          <button className="p-1.5 text-red-600 hover:bg-red-50 rounded" title="Suspend User"><Ban size={16}/></button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
        <div className="relative w-full sm:w-96">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search users by name, ID, or role..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 text-sm"
          />
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 border rounded-lg transition w-full sm:w-auto justify-center">
            <Download size={16} /> Export CSV
          </button>
          <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition w-full sm:w-auto justify-center">
            <Users size={16} /> Add User
          </button>
        </div>
      </div>

      {/* Main Table */}
      <div className="h-[600px]">
        <DataTable 
          title="Platform User Directory" 
          columns={columns} 
          data={mockUsers} 
        />
      </div>
    </div>
  );
}
