import React from 'react';
import { Server, Database, Activity, Cpu } from 'lucide-react';
import DataTable from '@/components/ui/DataTable';

const mockTelemetryLogs = [
  { id: '1', service: 'LangGraph Orchestrator', metric: 'Node Execution Latency', value: '142ms', status: 'Healthy' },
  { id: '2', service: 'ChromaDB (Vector)', metric: 'Query Latency (Top-K=5)', value: '88ms', status: 'Healthy' },
  { id: '3', service: 'Redis Streams', metric: 'Throughput', value: '4,500 msg/s', status: 'Healthy' },
  { id: '4', service: 'Ollama LLM (Llama3)', metric: 'Generation Speed', value: '42 tokens/s', status: 'Warning' },
  { id: '5', service: 'FastAPI Backend', metric: 'Active WebSocket Conns', value: '1,204', status: 'Healthy' },
];

export default function SystemTelemetry() {
  const columns = [
    { header: 'Microservice', accessor: 'service', className: 'font-medium text-slate-800' },
    { header: 'Metric Monitored', accessor: 'metric', className: 'text-slate-600' },
    { header: 'Current Value', accessor: 'value', className: 'font-mono text-sm' },
    { 
      header: 'Health Status', 
      accessor: 'status',
      render: (row) => (
        <span className={`px-2.5 py-1 text-[10px] uppercase font-bold tracking-wider rounded-md ${
          row.status === 'Healthy' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700 animate-pulse'
        }`}>
          {row.status}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Server size={18}/> <span className="font-bold">FastAPI Node</span></div>
          <p className="text-3xl font-black text-slate-800">99.9%</p>
          <p className="text-xs text-emerald-600">Uptime (30 days)</p>
        </div>
        
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Database size={18}/> <span className="font-bold">ChromaDB</span></div>
          <p className="text-3xl font-black text-slate-800">1.2M</p>
          <p className="text-xs text-slate-500">Indexed Embeddings</p>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Activity size={18}/> <span className="font-bold">Redis Cluster</span></div>
          <p className="text-3xl font-black text-slate-800">4.2GB</p>
          <p className="text-xs text-slate-500">Memory Utilization</p>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500"><Cpu size={18}/> <span className="font-bold">LLM Inference</span></div>
          <p className="text-3xl font-black text-slate-800">62%</p>
          <p className="text-xs text-amber-600">GPU Utilization</p>
        </div>
      </div>

      {/* Telemetry Data Grid */}
      <div className="h-[400px]">
        <DataTable 
          title="Real-Time System Telemetry" 
          columns={columns} 
          data={mockTelemetryLogs} 
        />
      </div>
      
    </div>
  );
}
