import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import RoleRouter from '../components/auth/RoleRouter';

// Layouts
import DashboardLayout from '../layouts/DashboardLayout';

// Lazy Loaded Pages
const Login = lazy(() => import('../pages/auth/Login'));
const Register = lazy(() => import('../pages/auth/Register'));
const FarmerDashboard = lazy(() => import('../pages/FarmerDashboard'));
const BuyerDashboard = lazy(() => import('../pages/BuyerDashboard'));
const WarehouseDashboard = lazy(() => import('../pages/WarehouseDashboard'));
const TransportDashboard = lazy(() => import('../pages/TransportDashboard'));
const ProcessorDashboard = lazy(() => import('../pages/ProcessorDashboard'));
const AdminDashboard = lazy(() => import('../pages/AdminDashboard'));
const NegotiationRoom = lazy(() => import('../pages/NegotiationRoom'));
const DealTracker = lazy(() => import('../pages/DealTracker'));
const AIOperationsCenter = lazy(() => import('../pages/AIOperationsCenter'));
const SettingsDashboard = lazy(() => import('../pages/SettingsDashboard'));
const NotFound = lazy(() => import('../pages/NotFound'));

// New Final Prompt Pages
const LandingPage = lazy(() => import('../pages/public/LandingPage'));
const AboutPage = lazy(() => import('../pages/public/AboutPage'));
const UserProfile = lazy(() => import('../pages/UserProfile'));
const GlobalAnalytics = lazy(() => import('../pages/GlobalAnalytics'));
const TransactionsPage = lazy(() => import('../pages/TransactionsPage'));

/**
 * Enterprise Application Routing Module.
 * Extracted from App.jsx to enforce Clean Architecture and separation of concerns.
 */
export default function AppRoutes() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-slate-50 text-emerald-600 font-bold tracking-widest uppercase">Loading Modules...</div>}>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes Wrapper */}
        <Route element={<DashboardLayout />}>
          
          {/* Master Route Router */}
          <Route path="/dashboard" element={<RoleRouter />} />

          {/* Requested Aliases Mapping to existing tested architecture */}
          <Route path="/farmer/listings" element={<Navigate to="/dashboard/farmer" replace />} />
          <Route path="/farmer/listings/new" element={<Navigate to="/dashboard/farmer" replace />} />
          <Route path="/farmer/negotiations" element={<Navigate to="/dashboard/farmer" replace />} />
          <Route path="/farmer/transactions" element={<Navigate to="/transactions" replace />} />
          
          <Route path="/buyer/requirements" element={<Navigate to="/dashboard/buyer" replace />} />
          <Route path="/buyer/requirements/new" element={<Navigate to="/dashboard/buyer" replace />} />
          <Route path="/buyer/matches" element={<Navigate to="/dashboard/buyer" replace />} />
          <Route path="/buyer/negotiations" element={<Navigate to="/dashboard/buyer" replace />} />
          <Route path="/buyer/transactions" element={<Navigate to="/transactions" replace />} />

          {/* Role-Gated Dashboards */}
          <Route element={<ProtectedRoute allowedRoles={['farmer', 'admin']} />}>
            <Route path="dashboard/farmer" element={<FarmerDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['buyer', 'admin']} />}>
            <Route path="dashboard/buyer" element={<BuyerDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['warehouse', 'admin']} />}>
            <Route path="dashboard/warehouse" element={<WarehouseDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['transport', 'admin']} />}>
            <Route path="dashboard/transport" element={<TransportDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['processor', 'admin']} />}>
            <Route path="dashboard/processor" element={<ProcessorDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
            <Route path="dashboard/admin" element={<AdminDashboard />} />
            <Route path="dashboard/ai-ops" element={<AIOperationsCenter />} />
            <Route path="dashboard/settings" element={<SettingsDashboard />} />
          </Route>

          {/* Shared Features */}
          <Route element={<ProtectedRoute allowedRoles={['farmer', 'buyer', 'warehouse', 'transport', 'processor', 'admin']} />}>
            <Route path="/profile" element={<UserProfile />} />
            <Route path="/analytics" element={<GlobalAnalytics />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            
            {/* New Prompt Aliases */}
            <Route path="/negotiations/:id" element={<NegotiationRoom />} />
            <Route path="/supply-chain/:id" element={<DealTracker />} />
            
            {/* Original Paths */}
            <Route path="/negotiation/:id" element={<NegotiationRoom />} />
            <Route path="/deal/:id/track" element={<DealTracker />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
