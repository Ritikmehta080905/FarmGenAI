import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Clock } from 'lucide-react';

export default function SessionExpiredDialog() {
  const { sessionExpired, logout } = useAuth();

  if (!sessionExpired) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center animate-in zoom-in-95 duration-300">
        <div className="mx-auto w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-6">
          <Clock className="text-amber-600 w-8 h-8" />
        </div>
        
        <h2 className="text-2xl font-bold text-slate-800 mb-2">Session Expired</h2>
        <p className="text-slate-600 mb-8">
          For your security, you have been automatically logged out due to inactivity. Please log in again to continue.
        </p>

        <button 
          onClick={logout}
          className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl transition"
        >
          Return to Login
        </button>
      </div>
    </div>
  );
}
