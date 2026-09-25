import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import RoleRouter from '@/components/auth/RoleRouter';
import PageLoader from '@/components/ui/PageLoader';

// Layouts
import FarmerLayout from '@/layouts/FarmerLayout';
import BuyerLayout from '@/layouts/BuyerLayout';
import WarehouseLayout from '@/layouts/WarehouseLayout';
import TransportLayout from '@/layouts/TransportLayout';
import ProcessorLayout from '@/layouts/ProcessorLayout';
import AdminLayout from '@/layouts/AdminLayout';

// ── Auth Pages ────────────────────────────────────────────
const Login = lazy(() => import('@/pages/auth/Login'));
const Register = lazy(() => import('@/pages/auth/Register'));

// ── Public Pages ──────────────────────────────────────────
const LandingPage = lazy(() => import('@/pages/public/LandingPage'));
const AboutPage = lazy(() => import('@/pages/public/AboutPage'));

// ── Role Dashboards ───────────────────────────────────────
const FarmerDashboard = lazy(() => import('@/pages/farmer/FarmerDashboard'));
const BuyerDashboard = lazy(() => import('@/pages/buyer/BuyerDashboard'));
const WarehouseDashboard = lazy(() => import('@/pages/warehouse/WarehouseDashboard'));
const TransportDashboard = lazy(() => import('@/pages/transport/TransportDashboard'));
const VehicleList = lazy(() => import('@/pages/transport/VehicleList'));
const VehicleDetail = lazy(() => import('@/pages/transport/VehicleDetail'));
const ProcessorDashboard = lazy(() => import('@/pages/processor/ProcessorDashboard'));
const AdminDashboard = lazy(() => import('@/pages/admin/AdminDashboard'));
const AIOperationsCenter = lazy(() => import('@/pages/admin/AIOperationsCenter'));
const SettingsDashboard = lazy(() => import('@/pages/admin/SettingsDashboard'));

// ── Shared Pages ──────────────────────────────────────────
const NegotiationRoom = lazy(() => import('@/pages/negotiation/NegotiationRoom'));
const DealTracker = lazy(() => import('@/pages/logistics/DealTracker'));
const GlobalAnalytics = lazy(() => import('@/pages/analytics/GlobalAnalytics'));
const UserProfile = lazy(() => import('@/pages/profile/UserProfile'));
const TransactionsPage = lazy(() => import('@/pages/transactions/TransactionsPage'));

// ── Error Pages ───────────────────────────────────────────
const NotFound = lazy(() => import('@/pages/errors/NotFoundPage'));

/**
 * Enterprise Application Routing Module.
 * Extracted from App.jsx to enforce Clean Architecture and separation of concerns.
 */
export default function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Master Route Router */}
          <Route path="/dashboard" element={<RoleRouter />} />

          {/* Alias Routes — locked to matching role */}
          <Route element={<FarmerLayout />}>
            <Route element={<ProtectedRoute allowedRoles={['farmer', 'admin']} />}>
              <Route path="/farmer/listings" element={<Navigate to="/dashboard/farmer" replace />} />
              <Route path="/farmer/listings/new" element={<Navigate to="/dashboard/farmer" replace />} />
              <Route path="/farmer/negotiations" element={<Navigate to="/dashboard/farmer" replace />} />
              <Route path="/farmer/transactions" element={<Navigate to="/transactions" replace />} />
            </Route>
          </Route>

          <Route element={<BuyerLayout />}>
            <Route element={<ProtectedRoute allowedRoles={['buyer', 'admin']} />}>
              <Route path="/buyer/requirements" element={<Navigate to="/dashboard/buyer" replace />} />
              <Route path="/buyer/requirements/new" element={<Navigate to="/dashboard/buyer" replace />} />
              <Route path="/buyer/matches" element={<Navigate to="/dashboard/buyer" replace />} />
              <Route path="/buyer/negotiations" element={<Navigate to="/dashboard/buyer" replace />} />
              <Route path="/buyer/transactions" element={<Navigate to="/transactions" replace />} />
            </Route>
          </Route>

          {/* ── Agent Dashboards — HARD LOCKED to matching role only ──────────── */}
          {/* Farmer */}
          <Route element={<FarmerLayout />}>
            <Route element={<ProtectedRoute allowedRoles={['farmer', 'admin']} />}>
              <Route path="/dashboard/farmer" element={<FarmerDashboard />} />
              <Route path="/profile" element={<UserProfile />} />
              <Route path="/analytics" element={<GlobalAnalytics />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/negotiations/:id" element={<NegotiationRoom />} />
              <Route path="/supply-chain/:id" element={<DealTracker />} />
              <Route path="/negotiation/:id" element={<NegotiationRoom />} />
              <Route path="/deal/:id/track" element={<DealTracker />} />
            </Route>
          </Route>

          {/* Buyer */}
          <Route element={<BuyerLayout />}>
            <Route element={<ProtectedRoute allowedRoles={['buyer', 'admin']} />}>
              <Route path="/dashboard/buyer" element={<BuyerDashboard />} />
              <Route path="/profile" element={<UserProfile />} />
              <Route path="/analytics" element={<GlobalAnalytics />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/negotiations/:id" element={<NegotiationRoom />} />
              <Route path="/supply-chain/:id" element={<DealTracker />} />
              <Route path="/negotiation/:id" element={<NegotiationRoom />} />
              <Route path="/deal/:id/track" element={<DealTracker />} />
            </Route>
          </Route>

          {/* Warehouse */}
          <Route element={<WarehouseLayout />}>
            <Route element={<ProtectedRoute allowedRoles={['warehouse', 'admin']} />}>
              <Route path="/dashboard/warehouse" element={<WarehouseDashboard />} />
              <Route path="/profile" element={<UserProfile />} />
              <Route path="/analytics" element={<GlobalAnalytics />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/negotiations/:id" element={<NegotiationRoom />} />
              <Route path="/supply-chain/:id" element={<DealTracker />} />
            </Route>
          </Route>

          {/* Transport */}
          <Route element={<TransportLayout />}>
            <Route element={<ProtectedRoute allowedRoles={['transport', 'admin']} />}>
              <Route path="/dashboard/transport" element={<TransportDashboard />} />
              <Route path="/profile" element={<UserProfile />} />
              <Route path="/analytics" element={<GlobalAnalytics />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/supply-chain/:id" element={<DealTracker />} />
              <Route path="/deal/:id/track" element={<DealTracker />} />
            </Route>
          </Route>

          {/* Processor */}
          <Route element={<ProcessorLayout />}>
            <Route element={<ProtectedRoute allowedRoles={['processor', 'admin']} />}>
              <Route path="/dashboard/processor" element={<ProcessorDashboard />} />
              <Route path="/profile" element={<UserProfile />} />
              <Route path="/analytics" element={<GlobalAnalytics />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/negotiations/:id" element={<NegotiationRoom />} />
              <Route path="/negotiation/:id" element={<NegotiationRoom />} />
            </Route>
          </Route>

          {/* Admin-only pages */}
          <Route element={<AdminLayout />}>
            <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
              <Route path="/dashboard/ai-ops" element={<AIOperationsCenter />} />
              <Route path="/dashboard/admin" element={<AdminDashboard />} />
              <Route path="/dashboard/settings" element={<SettingsDashboard />} />
              <Route path="/profile" element={<UserProfile />} />
              <Route path="/analytics" element={<GlobalAnalytics />} />
              <Route path="/transactions" element={<TransactionsPage />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
