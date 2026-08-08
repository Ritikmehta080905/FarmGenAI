import React, { useState, useEffect, useRef } from 'react';
import { 
  Sprout, 
  User, 
  TrendingUp, 
  MapPin, 
  DollarSign, 
  Boxes, 
  Activity, 
  FileText, 
  Cpu, 
  ArrowRight, 
  LogOut, 
  Lock, 
  UserCheck, 
  RefreshCw, 
  Plus, 
  Eye, 
  Scale, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  Truck,
  Building,
  RotateCcw,
  Loader2
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

const BASE_URL = 'http://127.0.0.1:8000';
const WS_URL = 'ws://127.0.0.1:8000/ws/negotiation';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // Auth form states
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('farmer');
  const [fullname, setFullname] = useState('');
  const [authError, setAuthError] = useState('');
  const [authSuccess, setAuthSuccess] = useState('');

  // App core states
  const [listings, setListings] = useState([]);
  const [negotiations, setNegotiations] = useState([]);
  const [p2pNodes, setP2pNodes] = useState({});
  const [publicLedger, setPublicLedger] = useState([]);
  const [simulationResult, setSimulationResult] = useState(null);

  // Form inputs
  const [crop, setCrop] = useState('Tomato');
  const [quantity, setQuantity] = useState(500);
  const [minPrice, setMinPrice] = useState(25);
  const [shelfLife, setShelfLife] = useState(5);
  const [farmerLocation, setFarmerLocation] = useState('Nashik');

  // Simulation inputs
  const [simFarmerMin, setSimFarmerMin] = useState(18);
  const [simBuyerTarget, setSimBuyerTarget] = useState(20);
  const [simMaxRounds, setSimMaxRounds] = useState(5);

  // Websocket active connection & logs
  const [activeNegotiationId, setActiveNegotiationId] = useState(null);
  const [liveLogs, setLiveLogs] = useState([]);
  const [priceSeries, setPriceSeries] = useState([]);
  const [selectedNegotiation, setSelectedNegotiation] = useState(null);
  
  const wsRef = useRef(null);

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  useEffect(() => {
    if (currentUser) {
      fetchDashboardData();
      const interval = setInterval(fetchDashboardData, 10000);
      return () => clearInterval(interval);
    }
  }, [currentUser]);

  // Connect WebSocket for active negotiations
  useEffect(() => {
    if (!token) return;
    
    const ws = new WebSocket(`${WS_URL}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WS Connection established');
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      console.log('WS Event received:', msg);

      if (msg.event === 'NEGOTIATION_STARTED') {
        setLiveLogs([`🚀 Negotiation initialized. State Graph execution started...`]);
        setActiveNegotiationId(msg.negotiation_id);
      }
      
      if (msg.negotiation_id && (msg.negotiation_id === activeNegotiationId || !activeNegotiationId)) {
        if (msg.event === 'NEGOTIATION_LOG') {
          setLiveLogs(prev => [...prev, msg.message]);
          if (msg.offer) {
            setPriceSeries(prev => [...prev, {
              round: prev.length + 1,
              price: msg.offer,
              agent: msg.agent_type === 'farmer' ? 'Farmer Ask' : 'Buyer Bid'
            }]);
          }
        }
        if (msg.event === 'NEGOTIATION_FINISHED') {
          setLiveLogs(prev => [...prev, `🏁 NEGOTIATION COMPLETED with status: ${msg.status}`, `Summary: ${msg.summary}`]);
          fetchDashboardData();
        }
      }
    };

    ws.onclose = () => {
      console.log('WS Connection closed');
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [token, activeNegotiationId]);

  const fetchUserProfile = async () => {
    try {
      // Decode JWT roughly to show user info
      // Safely decode JWT payload handling Base64Url padding
      let base64Url = token.split('.')[1];
      let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      let padded = base64.padEnd(base64.length + (4 - base64.length % 4) % 4, '=');
      const payload = JSON.parse(atob(padded));
      setCurrentUser({
        username: payload.sub,
        role: payload.role || 'farmer',
        fullName: payload.full_name || payload.sub
      });
    } catch (e) {
      handleLogout();
    }
  };

  const fetchDashboardData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // 1. Get negotiations list
      const negRes = await fetch(`${BASE_URL}/api/negotiations?role=${currentUser?.role || ''}`, { headers });
      if (negRes.ok) {
        const data = await negRes.json();
        setNegotiations(data.negotiations || []);
      }

      // 2. Get P2P node maps
      const nodeRes = await fetch(`${BASE_URL}/api/nodes`, { headers });
      if (nodeRes.ok) {
        const data = await nodeRes.json();
        setP2pNodes(data || {});
      }

      // 3. Get Public Ledger
      const ledgerRes = await fetch(`${BASE_URL}/api/ledger`, { headers });
      if (ledgerRes.ok) {
        const data = await ledgerRes.json();
        setPublicLedger(data.ledger || []);
      }
    } catch (e) {
      console.error("Dashboard refresh failed:", e);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    setIsLoading(true);
    try {
      // Ensure email format for backend validation
      const email = username.includes('@') ? username : `${username}@agri.ai`;
      const res = await fetch(`${BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
      } else {
        const data = await res.json();
        let errMsg = data.detail || 'Login failed. Please check credentials.';
        if (Array.isArray(errMsg)) {
          errMsg = errMsg.map(e => e.msg || JSON.stringify(e)).join(', ');
        }
        setAuthError(errMsg);
      }
    } catch (e) {
      setAuthError('Unable to connect to backend server.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    setIsLoading(true);
    try {
      // Ensure email format for backend validation
      const email = username.includes('@') ? username : `${username}@agri.ai`;
      const res = await fetch(`${BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: fullname, 
          email: email, 
          password: password, 
          role: role,
          location: 'Nashik',
          language: 'Marathi'
        })
      });

      if (res.ok) {
        setAuthSuccess('Registration successful! Please log in.');
        setIsLogin(true);
      } else {
        const data = await res.json();
        let errMsg = data.detail || 'Registration failed.';
        if (Array.isArray(errMsg)) {
          errMsg = errMsg.map(e => e.msg || JSON.stringify(e)).join(', ');
        }
        setAuthError(errMsg);
      }
    } catch (e) {
      setAuthError('Connection error.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    setCurrentUser(null);
    setActiveTab('dashboard');
  };

  const triggerNegotiation = async (e) => {
    e.preventDefault();
    setLiveLogs(['📡 Initiating LangGraph workflow planner...', 'Pending matching engine selection...']);
    setPriceSeries([]);
    
    try {
      const res = await fetch(`${BASE_URL}/start-negotiation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          farmer_name: currentUser?.fullName,
          crop,
          quantity: Number(quantity),
          min_price: Number(minPrice),
          shelf_life: Number(shelfLife),
          location: farmerLocation,
          quality: "A",
          language: "English"
        })
      });

      if (res.ok) {
        const data = await res.json();
        setActiveNegotiationId(data.negotiation_id);
      } else {
        const err = await res.json();
        alert(err.detail || 'Failed to start negotiation');
      }
    } catch (e) {
      console.error(e);
      alert('Error triggering negotiation: ' + (e.message || e));
    }
  };

  const runSimulation = async (e) => {
    e.preventDefault();
    setSimulationResult(null);
    try {
      const res = await fetch(`${BASE_URL}/run-simulation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          crop: 'Tomato',
          quantity: 1000,
          farmer_min_price: Number(simFarmerMin),
          buyer_target_price: Number(simBuyerTarget),
          max_rounds: Number(simMaxRounds)
        })
      });

      if (res.ok) {
        const data = await res.json();
        setSimulationResult(data);
      } else {
        alert('Simulation failed.');
      }
    } catch (e) {
      alert('Error running simulation.');
    }
  };

  const signDeal = async (negId, roleToSign) => {
    try {
      const res = await fetch(`${BASE_URL}/api/negotiation/${negId}/approve?role=${roleToSign}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchDashboardData();
        alert('Successfully signed document!');
      } else {
        alert('Consensus signature failed.');
      }
    } catch (e) {
      alert('Error signing negotiation.');
    }
  };

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-4">
        <div className="w-full max-w-md overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-xl transition-all duration-300">
          <div className="flex flex-col items-center gap-2 pb-6 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-500 to-green-400 text-slate-950 shadow-lg shadow-emerald-500/20">
              <Sprout size={32} className="animate-pulse" />
            </div>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-white">AgriNegotiator Platform</h2>
            <p className="text-sm text-slate-400">Maharashtra decentralized multi-agent bargaining network</p>
          </div>

          <div className="flex border-b border-slate-800 pb-4 mb-6">
            <button 
              onClick={() => { setIsLogin(true); setAuthError(''); }}
              className={`flex-1 py-2 text-center text-sm font-semibold transition-all ${isLogin ? 'border-b-2 border-emerald-500 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Sign In
            </button>
            <button 
              onClick={() => { setIsLogin(false); setAuthError(''); }}
              className={`flex-1 py-2 text-center text-sm font-semibold transition-all ${!isLogin ? 'border-b-2 border-emerald-500 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Create Node
            </button>
          </div>

          {authError && (
            <div className="mb-4 rounded-lg bg-red-950/50 border border-red-500/30 p-3 text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle size={16} className="text-red-400 shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          {authSuccess && (
            <div className="mb-4 rounded-lg bg-emerald-950/50 border border-emerald-500/30 p-3 text-xs text-emerald-300 flex items-center gap-2">
              <CheckCircle size={16} className="text-emerald-400 shrink-0" />
              <span>{authSuccess}</span>
            </div>
          )}

          {isLogin ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Username / Node ID</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500"><User size={16} /></span>
                  <input 
                    type="text" 
                    value={username} 
                    onChange={e => setUsername(e.target.value)}
                    required
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 pl-10 pr-4 text-sm text-slate-200 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500" 
                    placeholder="farmer_nashik_01" 
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Passkey</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500"><Lock size={16} /></span>
                  <input 
                    type="password" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)}
                    required
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 pl-10 pr-4 text-sm text-slate-200 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500" 
                    placeholder="••••••••" 
                  />
                </div>
              </div>

              <button 
                type="submit" 
                disabled={isLoading}
                className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/10 hover:from-emerald-500 hover:to-emerald-400 transition-all active:scale-95 disabled:opacity-70"
              >
                {isLoading ? <Loader2 size={16} className="animate-spin" /> : <>Launch Stakeholder Node <ArrowRight size={16} /></>}
              </button>
            </form>
          ) : (
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Stakeholder Name</label>
                <input 
                  type="text" 
                  value={fullname} 
                  onChange={e => setFullname(e.target.value)}
                  required
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-4 text-sm text-slate-200 outline-none focus:border-emerald-500" 
                  placeholder="Ramesh Patil" 
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Username / Identifier</label>
                <input 
                  type="text" 
                  value={username} 
                  onChange={e => setUsername(e.target.value)}
                  required
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-4 text-sm text-slate-200 outline-none focus:border-emerald-500" 
                  placeholder="ramesh_patil" 
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Role Type</label>
                <select 
                  value={role} 
                  onChange={e => setRole(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-4 text-sm text-slate-200 outline-none focus:border-emerald-500"
                >
                  <option value="farmer">Farmer Stakeholder</option>
                  <option value="buyer">Commercial Buyer</option>
                  <option value="admin">System Auditor</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Create Passkey</label>
                <input 
                  type="password" 
                  value={password} 
                  onChange={e => setPassword(e.target.value)}
                  required
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-4 text-sm text-slate-200 outline-none focus:border-emerald-500" 
                  placeholder="••••••••" 
                />
              </div>

              <button 
                type="submit" 
                disabled={isLoading}
                className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/10 hover:from-emerald-500 hover:to-emerald-400 transition-all active:scale-95 disabled:opacity-70"
              >
                {isLoading ? <Loader2 size={16} className="animate-spin" /> : <>Register & Verify Node <UserCheck size={16} /></>}
              </button>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4 sticky top-0 z-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-green-400 text-slate-950">
            <Sprout size={24} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">AgriNegotiator</h1>
            <p className="text-xxs text-emerald-400 font-semibold tracking-wider uppercase">LangGraph Decentralized Platform</p>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          <button 
            onClick={() => setActiveTab('dashboard')} 
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'dashboard' ? 'bg-slate-800 text-white font-semibold shadow-inner' : 'text-slate-400 hover:text-white'}`}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('simulation')} 
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'simulation' ? 'bg-slate-800 text-white font-semibold shadow-inner' : 'text-slate-400 hover:text-white'}`}
          >
            Agent Simulation
          </button>
          <button 
            onClick={() => setActiveTab('ledger')} 
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'ledger' ? 'bg-slate-800 text-white font-semibold shadow-inner' : 'text-slate-400 hover:text-white'}`}
          >
            P2P Consensus Ledger
          </button>
        </nav>

        <div className="flex items-center gap-4">
          <div className="hidden lg:flex flex-col items-end">
            <span className="text-sm font-semibold text-slate-200">{currentUser?.fullName}</span>
            <span className="text-xxs font-bold text-emerald-400 uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-500/20">{currentUser?.role}</span>
          </div>
          <button 
            onClick={handleLogout}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 text-slate-400 hover:text-red-400 hover:border-red-500/30 transition-all"
            title="Log Out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      {/* Main Content Layout */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        
        {/* Mobile Navigation bar */}
        <div className="flex md:hidden border border-slate-800 bg-slate-900 rounded-xl p-1 gap-1">
          <button onClick={() => setActiveTab('dashboard')} className={`flex-1 py-2 text-center text-xs font-semibold rounded-lg ${activeTab === 'dashboard' ? 'bg-slate-800 text-white' : 'text-slate-400'}`}>Dashboard</button>
          <button onClick={() => setActiveTab('simulation')} className={`flex-1 py-2 text-center text-xs font-semibold rounded-lg ${activeTab === 'simulation' ? 'bg-slate-800 text-white' : 'text-slate-400'}`}>Simulation</button>
          <button onClick={() => setActiveTab('ledger')} className={`flex-1 py-2 text-center text-xs font-semibold rounded-lg ${activeTab === 'ledger' ? 'bg-slate-800 text-white' : 'text-slate-400'}`}>Ledger</button>
        </div>

        {activeTab === 'dashboard' && (
          <div className="flex flex-col gap-6">
            {/* Left/Middle dashboard content */}
            <div className="space-y-6">
              
              {/* Farmer listing actions */}
              {currentUser?.role === 'farmer' && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl">
                  <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800/80">
                    <Plus className="text-emerald-500" size={20} />
                    <h3 className="text-lg font-bold text-white">Create New Crop Listing</h3>
                  </div>

                  <form onSubmit={triggerNegotiation} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Crop Type</label>
                        <select value={crop} onChange={e => setCrop(e.target.value)} className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-3 text-sm text-slate-200 outline-none focus:border-emerald-500">
                          <option value="Tomato">🍅 Tomato (Tomato)</option>
                          <option value="Onion">🧅 Onion (Kanda)</option>
                          <option value="Soybean">🌱 Soybean</option>
                          <option value="Cotton">🎴 Cotton</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Quantity (Kg)</label>
                        <input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2 px-3 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Reserve Price (₹/Kg)</label>
                        <input type="number" value={minPrice} onChange={e => setMinPrice(e.target.value)} className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2 px-3 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Shelf Life (Days)</label>
                        <input type="number" value={shelfLife} onChange={e => setShelfLife(e.target.value)} className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2 px-3 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Local Mandi Location</label>
                        <select value={farmerLocation} onChange={e => setFarmerLocation(e.target.value)} className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-3 text-sm text-slate-200 outline-none focus:border-emerald-500">
                          <option value="Nashik">Nashik</option>
                          <option value="Pune">Pune</option>
                          <option value="Mumbai">Mumbai</option>
                          <option value="Nagpur">Nagpur</option>
                          <option value="Satara">Satara</option>
                        </select>
                      </div>
                    </div>

                    <button type="submit" className="w-full mt-2 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-bold rounded-xl transition-all shadow-lg shadow-emerald-500/20 active:scale-95 flex items-center justify-center gap-2">
                      Start LangGraph Bargaining <Cpu size={18} />
                    </button>
                  </form>
                </div>
              )}
            </div>

            {/* Live stream logs & graph side-by-side — FIRST so no scrolling needed */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* WebSocket Live bargaining status */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl flex flex-col">
                <div className="flex items-center gap-2 pb-3 mb-4 border-b border-slate-800/80">
                  <Cpu className="text-emerald-500" size={20} />
                  <h3 className="text-lg font-bold text-white">Live State Graph Logs</h3>
                </div>

                <div className="bg-slate-950 rounded-xl border border-slate-850 p-4 font-mono text-xs text-emerald-400 h-64 overflow-y-auto space-y-1.5 flex flex-col-reverse flex-1">
                  {liveLogs.length === 0 ? (
                    <div className="text-slate-600 text-center my-auto">
                      Start or select a negotiation to view telemetry streams.
                    </div>
                  ) : (
                    [...liveLogs].reverse().map((log, index) => (
                      <div key={index} className="leading-relaxed border-l-2 border-emerald-500/30 pl-2">
                        {log}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Bargaining Chart */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl flex flex-col">
                <div className="flex items-center gap-2 pb-3 mb-4 border-b border-slate-800/80">
                  <Activity className="text-emerald-500" size={20} />
                  <h3 className="text-lg font-bold text-white">Bargaining Chart</h3>
                </div>
                
                <div className="bg-slate-950 rounded-xl border border-slate-850 p-4 flex-1 flex flex-col justify-center min-h-[16rem]">
                  {priceSeries.length > 0 ? (
                    <div className="h-full w-full min-h-[200px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={priceSeries}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="round" stroke="#64748b" fontSize={10} />
                          <YAxis stroke="#64748b" fontSize={10} />
                          <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} />
                          <Line type="monotone" dataKey="price" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 4 }} activeDot={{ r: 6 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="text-slate-600 text-center flex flex-col items-center justify-center space-y-3">
                      <TrendingUp size={32} className="text-slate-700" />
                      <p className="text-sm">Graph will populate when counter-offers begin.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

              {/* Active Negotiations — compact scrollable list BELOW the graph */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl">
                <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <Activity className="text-emerald-500" size={20} />
                    <h3 className="text-lg font-bold text-white">Active Negotiations & Contracts</h3>
                    <span className="text-xs text-slate-500 ml-2">({negotiations.length})</span>
                  </div>
                  <button onClick={fetchDashboardData} className="text-slate-400 hover:text-white transition-all"><RefreshCw size={16} /></button>
                </div>

                {negotiations.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 text-sm">
                    No active negotiations found for this stakeholder node.
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1" style={{scrollbarWidth: 'thin'}}>
                    {negotiations.map(neg => (
                      <div key={neg.negotiation_id} className="rounded-xl border border-slate-800/80 bg-slate-950/60 px-4 py-3 transition-all hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-900/20 group flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 min-w-0">
                          <span className={`text-xxs font-bold px-2 py-0.5 rounded whitespace-nowrap ${
                            neg.status === 'DEAL' ? 'bg-emerald-950 border border-emerald-500/30 text-emerald-400' :
                            neg.status === 'RUNNING' || neg.status === 'NEGOTIATING' ? 'bg-amber-950 border border-amber-500/30 text-amber-400 animate-pulse' :
                            neg.status.startsWith('ESCALATED') ? 'bg-indigo-950 border border-indigo-500/30 text-indigo-400' :
                            'bg-red-950 border border-red-500/30 text-red-400'
                          }`}>{neg.status}</span>
                          <div className="min-w-0">
                            <span className="text-sm font-bold text-white truncate block">{neg.crop || '—'} · {neg.quantity || '—'} Kg</span>
                            <span className="text-xs text-slate-500 truncate block">{neg.negotiation_id.slice(0,12)}… | {neg.final_price ? `₹${neg.final_price}/Kg` : `Reserve ₹${neg.min_price || 18}/Kg`}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button 
                            onClick={() => { setSelectedNegotiation(neg); setActiveNegotiationId(neg.negotiation_id); setLiveLogs(neg.logs || []); }} 
                            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-semibold transition-all flex items-center gap-1 text-xs"
                          >
                            <Eye size={12} /> Logs
                          </button>
                          {neg.status === 'PENDING_APPROVAL' && (
                            !neg.signatures?.[currentUser?.role] ? (
                              <button 
                                onClick={() => signDeal(neg.negotiation_id, currentUser?.role)}
                                className="px-3 py-1 bg-gradient-to-r from-emerald-600 to-emerald-500 text-slate-950 font-bold rounded-lg transition-all text-xs"
                              >
                                Sign
                              </button>
                            ) : (
                              <span className="text-emerald-400 font-semibold flex items-center gap-1 text-xs"><CheckCircle size={12} /> Signed</span>
                            )
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            <div className="space-y-6">
              {/* Discovered Stakeholder Nodes */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl">
                <h3 className="text-lg font-bold text-white pb-3 mb-4 border-b border-slate-800/80 flex items-center gap-2">
                  <Boxes className="text-emerald-500" size={20} />
                  Discovered Peer Nodes
                </h3>

                <div className="space-y-3">
                  {Object.keys(p2pNodes).map(nodeId => {
                    const node = p2pNodes[nodeId];
                    return (
                      <div key={nodeId} className="flex items-center justify-between p-2 rounded-xl bg-slate-950/60 border border-slate-850">
                        <div className="flex flex-col">
                          <span className="text-xs font-semibold text-slate-200">{nodeId}</span>
                          <span className="text-xxs font-bold text-slate-500 capitalize">{node.role} node</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xxs font-semibold bg-emerald-950 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">★ {node.trust_score || 4.2}</span>
                          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'simulation' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl h-fit">
              <h3 className="text-lg font-bold text-white pb-3 mb-4 border-b border-slate-800/80 flex items-center gap-2">
                <Cpu className="text-emerald-500" size={20} />
                Run Multi-Agent Simulation
              </h3>

              <form onSubmit={runSimulation} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Farmer Min Price (₹/Kg)</label>
                  <input type="number" value={simFarmerMin} onChange={e => setSimFarmerMin(Number(e.target.value))} className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-3 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Buyer Target Price (₹/Kg)</label>
                  <input type="number" value={simBuyerTarget} onChange={e => setSimBuyerTarget(Number(e.target.value))} className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-3 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Max Negotiation Rounds</label>
                  <input type="number" value={simMaxRounds} onChange={e => setSimMaxRounds(Number(e.target.value))} className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 px-3 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                </div>

                <button type="submit" className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-emerald-500/10 flex items-center justify-center gap-2">
                  Launch Simulation Run <RotateCcw size={16} />
                </button>
              </form>
            </div>

            <div className="lg:col-span-2 space-y-6">
              {simulationResult ? (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-2">
                    <h3 className="text-lg font-bold text-white">Simulation Metrics Output</h3>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      simulationResult.status === 'DEAL' ? 'bg-emerald-950 border border-emerald-500/20 text-emerald-400' : 'bg-red-950 border border-red-500/20 text-red-400'
                    }`}>{simulationResult.status}</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-850">
                      <span className="block text-xxs font-semibold text-slate-500 uppercase tracking-wider">Final Price</span>
                      <span className="text-xl font-bold text-white">₹{simulationResult.final_price || 'N/A'}</span>
                    </div>

                    <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-850">
                      <span className="block text-xxs font-semibold text-slate-500 uppercase tracking-wider">Rounds Taken</span>
                      <span className="text-xl font-bold text-white">{simulationResult.rounds_taken}</span>
                    </div>

                    <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-850">
                      <span className="block text-xxs font-semibold text-slate-500 uppercase tracking-wider">Storage Used</span>
                      <span className="text-xl font-bold text-white">{simulationResult.storage_escalated ? 'Yes' : 'No'}</span>
                    </div>

                    <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-850">
                      <span className="block text-xxs font-semibold text-slate-500 uppercase tracking-wider">Zero Waste</span>
                      <span className="text-xl font-bold text-white">{simulationResult.status === 'ESCALATED_COMPOST' ? 'Yes' : 'No'}</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-slate-300">Bargaining Round Iterations</h4>
                    <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 h-64 overflow-y-auto font-mono text-xs text-slate-400 space-y-2">
                      {simulationResult.logs.map((log, index) => (
                        <div key={index} className="leading-relaxed border-l-2 border-emerald-500/20 pl-2">
                          {log}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-850 bg-slate-900/10 p-12 text-center text-slate-500 text-sm">
                  Configure simulation parameters and press run to test multi-agent dynamics.
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'ledger' && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl space-y-6">
            <div className="flex items-center gap-2 pb-3 mb-2 border-b border-slate-800/80">
              <FileText className="text-emerald-500" size={20} />
              <h3 className="text-lg font-bold text-white">Public P2P Signed Deals Ledger</h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-400">
                <thead className="bg-slate-950 text-xs font-bold text-slate-300 uppercase tracking-wider">
                  <tr>
                    <th className="p-4 rounded-l-xl">Negotiation ID</th>
                    <th className="p-4">Farmer Stakeholder</th>
                    <th className="p-4">Buyer Entity</th>
                    <th className="p-4">Finalized Price</th>
                    <th className="p-4">Logistics Transit Plan</th>
                    <th className="p-4 rounded-r-xl">Committed Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {publicLedger.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-slate-500">No consensus contracts registered in the peer ledger yet.</td>
                    </tr>
                  ) : (
                    publicLedger.map((entry, index) => (
                      <tr key={index} className="hover:bg-slate-900/40 transition-all">
                        <td className="p-4 font-mono text-xs text-emerald-400">{entry.neg_id?.slice(0, 12)}...</td>
                        <td className="p-4 font-semibold text-slate-200">{entry.farmer}</td>
                        <td className="p-4 text-slate-300">{entry.buyer}</td>
                        <td className="p-4 font-bold text-emerald-400">₹{entry.final_price}/Kg</td>
                        <td className="p-4 text-slate-400">{entry.logistics}</td>
                        <td className="p-4 text-xxs text-slate-500">{entry.timestamp}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-800 bg-slate-900/30 py-6 text-center text-xs text-slate-500 mt-auto">
        &copy; 2026 AgriNegotiator Platform. Powered by stateful LangGraph + Multi-Agent Consensus.
      </footer>
    </div>
  );
}
