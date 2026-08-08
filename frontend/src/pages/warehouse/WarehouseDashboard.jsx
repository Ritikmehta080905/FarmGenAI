import React from 'react';
import { Warehouse, PackageSearch, Activity, MapPin } from 'lucide-react';
import StatCard from '@/components/ui/StatCard';
import ChartCard from '@/components/ui/ChartCard';
import DataTable from '@/components/ui/DataTable';

const occupancyData = [
  { name: 'Week 1', value: 45 },
  { name: 'Week 2', value: 55 },
  { name: 'Week 3', value: 68 },
  { name: 'Week 4', value: 85 },
];

const mockReservations = [
  { id: '1', farmer: 'Ramesh Patil', crop: 'Onions', capacity: '10 MT', duration: '2 Months', status: 'Active' },
  { id: '2', farmer: 'Anand Rao', crop: 'Wheat', capacity: '25 MT', duration: '6 Months', status: 'Pending' },
];

export default function WarehouseDashboard() {
  const tableColumns = [
    { header: 'Client', accessor: 'farmer', className: 'font-medium text-slate-800' },
    { header: 'Commodity', accessor: 'crop', className: 'text-slate-600' },
    { header: 'Required Capacity', accessor: 'capacity', className: 'text-slate-600' },
    { header: 'Duration', accessor: 'duration', className: 'text-slate-600' },
    { 
      header: 'Status', 
      accessor: 'status',
      render: (row) => (
        <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
          row.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
        }`}>
          {row.status}
        </span>
      )
    },
    { 
      header: 'Action', 
      accessor: 'actions',
      render: () => <button className="text-blue-600 font-medium hover:underline text-sm">Manage</button>
    }
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Warehouse className="text-purple-600" /> Cold Storage Management
          </h1>
          <p className="text-slate-500 mt-1">Monitor capacity, manage reservations, and track inventory health.</p>
        </div>
        <button className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl transition shadow-sm">
          Update Capacity
        </button>
      </div>
      
      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={<PackageSearch />} title="Occupancy Rate" value="85%" trend="Critically high" color="purple" />
        <StatCard icon={<Activity />} title="Storage Temp" value="4.2°C" trend="Stable (target 4.0°C)" color="emerald" />
        <StatCard icon={<MapPin />} title="Active Reservations" value="12" trend="+3 this week" color="blue" />
        <StatCard icon={<Warehouse />} title="Available Space" value="15 MT" trend="Out of 100 MT total" color="amber" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 h-[350px]">
          <ChartCard 
            title="Occupancy Trend" 
            subtitle="Capacity utilization over the last 4 weeks"
            data={occupancyData} 
            color="#9333ea" 
            height={260}
          />
        </div>
        <div className="lg:col-span-2 h-[350px]">
          <DataTable 
            title="Pending Storage Requests" 
            columns={tableColumns} 
            data={mockReservations} 
          />
        </div>
      </div>

    </div>
  );
}
