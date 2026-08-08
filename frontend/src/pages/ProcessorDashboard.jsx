import { Factory, ArchiveRestore } from 'lucide-react';

export default function ProcessorDashboard() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Processing Plant Portal</h1>
          <p className="text-slate-500 mt-1">Accept highly perishable crops at salvage market prices.</p>
        </div>
      </div>
      
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
        <h2 className="font-bold text-lg text-slate-800 mb-4 flex items-center gap-2">
          <Factory size={18} className="text-emerald-500" /> Pending Salvage Offers
        </h2>
        <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-100 border-dashed">
          <ArchiveRestore size={32} className="mx-auto text-slate-400 mb-3" />
          <p className="text-slate-500">No expiring crop escalations currently sent from AI Planner.</p>
        </div>
      </div>
    </div>
  );
}
