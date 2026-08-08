import React from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { TrendingUp, Users, PackageCheck, AlertTriangle } from 'lucide-react';

// Demo Data
const priceTrendData = [
  { month: 'Jan', tomato: 22, onion: 15, potato: 12 },
  { month: 'Feb', tomato: 18, onion: 16, potato: 14 },
  { month: 'Mar', tomato: 25, onion: 14, potato: 13 },
  { month: 'Apr', tomato: 28, onion: 18, potato: 15 },
  { month: 'May', tomato: 35, onion: 20, potato: 18 },
  { month: 'Jun', tomato: 30, onion: 22, potato: 16 },
];

const successRateData = [
  { name: 'Completed', value: 94 },
  { name: 'Failed', value: 6 }
];

const demandSupplyData = [
  { name: 'Tomato', supply: 4000, demand: 5400 },
  { name: 'Onion', supply: 3000, demand: 3200 },
  { name: 'Potato', supply: 5000, demand: 4800 },
  { name: 'Wheat', supply: 8000, demand: 7500 },
];

const COLORS = ['#10b981', '#f43f5e'];

export default function GlobalAnalytics() {
  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Platform Analytics</h1>
          <p className="text-slate-500">Market trends and negotiation metrics (Demo Mode)</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">Negotiation Success Rate</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">94.2%</p>
          </div>
          <div className="bg-emerald-50 p-3 rounded-lg text-emerald-600">
            <TrendingUp size={24} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">Avg. Negotiation Rounds</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">2.4</p>
          </div>
          <div className="bg-blue-50 p-3 rounded-lg text-blue-600">
            <Users size={24} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">Completed Deals (30d)</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">1,482</p>
          </div>
          <div className="bg-indigo-50 p-3 rounded-lg text-indigo-600">
            <PackageCheck size={24} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">Warehouse Utilization</p>
            <p className="text-2xl font-bold text-amber-600 mt-1">87%</p>
          </div>
          <div className="bg-amber-50 p-3 rounded-lg text-amber-600">
            <AlertTriangle size={24} />
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Price Trends */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-6">Commodity Price Trends (₹/kg)</h3>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceTrendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Legend />
                <Line type="monotone" dataKey="tomato" stroke="#f43f5e" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="onion" stroke="#8b5cf6" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="potato" stroke="#eab308" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Supply vs Demand */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-6">Supply vs Demand Gap (Tons)</h3>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={demandSupplyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  cursor={{ fill: '#f8fafc' }}
                />
                <Legend />
                <Bar dataKey="supply" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="demand" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Success Rate */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center">
          <h3 className="text-lg font-bold text-slate-900 mb-6 self-start">AI Negotiation Success</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={successRateData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {successRateData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Transport Activity */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-6">Transport & Logistics Volume</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={priceTrendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip />
                <Area type="monotone" dataKey="tomato" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
