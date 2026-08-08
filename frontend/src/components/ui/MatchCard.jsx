import React from 'react';
import { Target, MapPin, TrendingUp, CheckCircle2, AlertCircle } from 'lucide-react';
import { formatCurrency, formatDistance } from '../../utils/formatters';

export default function MatchCard({ 
  matchScore, 
  farmerName, 
  crop, 
  quantity, 
  price, 
  distance, 
  reasons = [] 
}) {
  const isHighMatch = matchScore >= 90;
  const isMediumMatch = matchScore >= 70 && matchScore < 90;

  return (
    <div className={`bg-white rounded-2xl shadow-sm border p-5 card-hover ${
      isHighMatch ? 'border-emerald-200' : 'border-slate-200'
    }`}>
      
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-bold text-slate-800 text-lg">{farmerName}</h3>
          <p className="text-slate-500 text-sm flex items-center gap-1 mt-0.5">
            <MapPin size={14} /> {formatDistance(distance)} away
          </p>
        </div>
        
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold text-sm ${
          isHighMatch ? 'bg-emerald-100 text-emerald-700' : 
          isMediumMatch ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'
        }`}>
          <Target size={16} />
          {matchScore}% Match
        </div>
      </div>

      {/* Highlights Grid */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
          <p className="text-xs text-slate-500 mb-1">Commodity</p>
          <p className="font-bold text-slate-700">{crop}</p>
          <p className="text-xs text-slate-500">{quantity} kg available</p>
        </div>
        <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-100">
          <p className="text-xs text-emerald-600 mb-1 font-medium">Asking Price</p>
          <p className="font-bold text-emerald-700">{formatCurrency(price)}/kg</p>
          <p className="text-xs text-emerald-600 flex items-center gap-1">
            <TrendingUp size={12} /> vs budget
          </p>
        </div>
      </div>

      {/* AI Reasoning List */}
      <div className="space-y-2 mb-6">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">AI Reasoning</p>
        {reasons.map((reason, idx) => (
          <div key={idx} className="flex items-start gap-2 text-sm text-slate-600">
            {reason.type === 'positive' ? (
              <CheckCircle2 size={16} className="text-emerald-500 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle size={16} className="text-amber-500 shrink-0 mt-0.5" />
            )}
            <span>{reason.text}</span>
          </div>
        ))}
      </div>

      {/* Action */}
      <button className={`w-full py-2.5 rounded-xl font-bold transition-all duration-200 flex items-center justify-center gap-2 active:scale-95 ${
        isHighMatch 
          ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm hover:shadow-md' 
          : 'bg-slate-800 hover:bg-slate-900 text-white'
      }`}>
        Start Negotiation
      </button>

    </div>
  );
}
