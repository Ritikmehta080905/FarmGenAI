import React from 'react';
import { Link } from 'react-router-dom';
import { KeyRound } from 'lucide-react';

export default function ResetPassword() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center">
            <KeyRound size={32} />
          </div>
        </div>
        <h2 className="text-2xl font-bold text-center text-slate-800 mb-2">Create New Password</h2>
        <p className="text-slate-500 text-center mb-8 text-sm">
          Your new password must be different from previous used passwords.
        </p>

        <form className="space-y-4">
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">New Password</label>
            <input 
              type="password" 
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">Confirm Password</label>
            <input 
              type="password" 
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button 
            type="submit" 
            className="w-full py-3 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-bold transition"
          >
            Reset Password
          </button>
        </form>
      </div>
    </div>
  );
}
