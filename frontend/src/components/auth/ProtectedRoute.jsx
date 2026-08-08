import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ShieldAlert } from 'lucide-react';

/**
 * Enterprise RBAC Route Guard
 * Validates authentication status and checks if the user's role exists in allowedRoles.
 * 
 * @param {Array<string>} allowedRoles - Array of roles permitted to access this route
 */
export default function ProtectedRoute({ allowedRoles = [] }) {
  const { user, loading } = useAuth();

  // If AuthContext is still fetching tokens on hard reload, show generic loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-emerald-600 font-bold tracking-widest uppercase">
        Authenticating...
      </div>
    );
  }

  // Not logged in -> Redirect to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Role validation
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-6">
        <ShieldAlert size={64} className="text-red-500 mb-4" />
        <h1 className="text-3xl font-bold text-slate-800 mb-2">403 Forbidden</h1>
        <p className="text-slate-500 text-center max-w-md">
          You do not have the required permissions to view this module. Your current role is <span className="font-bold text-slate-700 capitalize">'{user.role}'</span>.
        </p>
        <button 
          onClick={() => window.history.back()}
          className="mt-6 px-6 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg font-bold transition"
        >
          Go Back
        </button>
      </div>
    );
  }

  // All checks passed, render the nested routes
  return <Outlet />;
}
