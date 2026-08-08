import { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Bell, LogOut, Sprout, Menu, X } from 'lucide-react';

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row relative">
      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed md:static inset-y-0 left-0 w-64 bg-emerald-900 text-white flex flex-col z-30 transition-transform duration-300 ease-in-out ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        <div className="p-6 flex items-center justify-between md:justify-start gap-3">
          <Sprout size={28} className="text-emerald-400" />
          <h1 className="text-xl font-bold tracking-tight">AgriNegotiator</h1>
          <button className="md:hidden text-emerald-300 hover:text-white" onClick={() => setIsMobileMenuOpen(false)}>
            <X size={24} />
          </button>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <Link to="/" className="block px-4 py-3 rounded-lg bg-emerald-800/50 hover:bg-emerald-800 transition">
            Dashboard
          </Link>
          <Link to="/negotiations" className="block px-4 py-3 rounded-lg hover:bg-emerald-800 transition">
            Active Deals
          </Link>
          <Link to="/market" className="block px-4 py-3 rounded-lg hover:bg-emerald-800 transition">
            Market Intel
          </Link>
        </nav>
        
        <div className="p-4 border-t border-emerald-800 mt-auto">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-10 h-10 rounded-full bg-emerald-700 flex items-center justify-center font-bold">
              {user?.name?.charAt(0) || 'U'}
            </div>
            <div>
              <p className="text-sm font-medium">{user?.name || 'User'}</p>
              <p className="text-xs text-emerald-300">{user?.role || 'FARMER'}</p>
            </div>
          </div>
          <button 
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-emerald-100 hover:text-white bg-emerald-800/50 hover:bg-red-500/80 rounded-lg transition"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-screen overflow-hidden w-full">
        <header className="h-16 bg-white border-b flex items-center justify-between px-6 shadow-sm z-10">
          <button 
            className="md:hidden p-2 -ml-2 rounded-lg hover:bg-slate-100 text-slate-600"
            onClick={() => setIsMobileMenuOpen(true)}
          >
            <Menu size={24} />
          </button>
          
          <div className="ml-auto">
            <button className="p-2 rounded-full hover:bg-slate-100 relative">
              <Bell size={20} className="text-slate-600" />
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span>
            </button>
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-6">
          {/* This is where the specific page components will be injected */}
          <Outlet />
        </div>
      </main>
    </div>
  );
}
