import React from 'react';
import { Landmark, ShieldCheck, Lock, Unlock } from 'lucide-react';
import { formatCurrency } from '@/utils/formatters';

export default function PaymentCard({ status, amount, farmer, buyer }) {
  const isReleased = status === 'PAYMENT_RELEASED';
  
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex flex-col h-full">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            <Landmark className={isReleased ? "text-emerald-500" : "text-amber-500"} /> 
            Smart Escrow Vault
          </h3>
          <p className="text-sm text-slate-500 mt-1">Funds are secured cryptographically.</p>
        </div>
        <div className={`px-3 py-1 rounded-xl text-xs font-bold flex items-center gap-1.5 ${
          isReleased ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700 animate-pulse'
        }`}>
          {isReleased ? <Unlock size={14} /> : <Lock size={14} />}
          {isReleased ? 'FUNDS RELEASED' : 'FUNDS LOCKED'}
        </div>
      </div>
      
      <div className="flex-1 flex flex-col justify-center items-center text-center bg-slate-50 rounded-xl border border-slate-100 p-6">
        <p className="text-sm font-medium text-slate-500 mb-2">Total Deal Value</p>
        <p className="text-4xl font-black text-slate-800 mb-4">{formatCurrency(amount)}</p>
        
        <div className="flex items-center gap-4 w-full max-w-xs">
          <div className="flex-1 text-right">
            <p className="text-xs font-bold text-slate-400 uppercase">From</p>
            <p className="font-medium text-sm text-slate-700 truncate">{buyer}</p>
          </div>
          <div className="w-8 flex justify-center">
            <ShieldCheck size={24} className={isReleased ? "text-emerald-500" : "text-amber-500"} />
          </div>
          <div className="flex-1 text-left">
            <p className="text-xs font-bold text-slate-400 uppercase">To</p>
            <p className="font-medium text-sm text-slate-700 truncate">{farmer}</p>
          </div>
        </div>
      </div>

      <div className="mt-4">
        {isReleased ? (
          <button className="w-full py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-bold rounded-xl transition shadow-sm">
            Download Invoice PDF
          </button>
        ) : (
          <p className="text-xs text-center text-slate-500">Funds will automatically transfer to Seller wallet upon successful delivery confirmation.</p>
        )}
      </div>
    </div>
  );
}
