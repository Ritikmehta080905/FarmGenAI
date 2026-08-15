import React from 'react';

const colorMap = {
  emerald: {
    icon: 'bg-emerald-50 text-emerald-600 border-emerald-200',
    trend: 'text-emerald-600',
  },
  blue: {
    icon: 'bg-blue-50 text-blue-600 border-blue-200',
    trend: 'text-blue-600',
  },
  purple: {
    icon: 'bg-purple-50 text-purple-600 border-purple-200',
    trend: 'text-purple-600',
  },
  amber: {
    icon: 'bg-amber-50 text-amber-600 border-amber-200',
    trend: 'text-amber-600',
  },
  red: {
    icon: 'bg-red-50 text-red-600 border-red-200',
    trend: 'text-red-600',
  },
};

export default function StatCard({ icon, title, value, trend, color = 'emerald', className = '' }) {
  const c = colorMap[color] || colorMap.emerald;

  return (
    <div className={`bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex items-center gap-4 card-hover animate-slide-up ${className}`}>
      <div className={`p-3 rounded-xl border flex-shrink-0 ${c.icon}`}>
        <span className="w-5 h-5 flex items-center justify-center">{icon}</span>
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-500 truncate">{title}</p>
        <p className="text-2xl font-bold text-slate-800 leading-tight">{value}</p>
        {trend && (
          <p className={`text-xs font-medium mt-0.5 truncate ${c.trend}`}>{trend}</p>
        )}
      </div>
    </div>
  );
}
