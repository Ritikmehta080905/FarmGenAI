import React from 'react';
import { Sprout } from 'lucide-react';

export default function PageLoader() {
  return (
    <div className="fixed inset-0 bg-white z-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-emerald-100 animate-spin border-t-emerald-500"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Sprout className="w-6 h-6 text-emerald-600" />
          </div>
        </div>
        <div className="flex flex-col items-center gap-1">
          <p className="text-slate-800 font-semibold tracking-tight">AgriNegotiator</p>
          <p className="text-slate-400 text-sm animate-pulse">Loading module...</p>
        </div>
      </div>
    </div>
  );
}
