import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';

export default function ForgotPassword() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center">
            <ShieldCheck size={32} />
          </div>
        </div>
        <h2 className="text-2xl font-bold text-center text-slate-800 mb-2">Reset Password</h2>
        <p className="text-slate-500 text-center mb-8 text-sm">
          Enter your registered email address or phone number and we'll send you instructions to reset your password.
        </p>

        <form className="space-y-4">
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">Email or Phone</label>
            <input 
              type="text" 
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
              placeholder="e.g. farmer@agri.com"
            />
          </div>

          <button 
            type="submit" 
            className="w-full py-3 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-bold transition"
          >
            Send Reset Link
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login" className="text-emerald-600 font-bold hover:underline">
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}
