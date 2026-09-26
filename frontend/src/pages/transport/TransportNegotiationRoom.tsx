import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, MessageSquare, Briefcase, Zap, ShieldCheck, Database, 
  CloudRain, Truck, Terminal as TerminalIcon, RefreshCw, CheckCircle, 
  AlertTriangle, MapPin, Play 
} from 'lucide-react';
import ChatBubble from '@/features/negotiation/components/ChatBubble';
import OfferCard from '@/features/negotiation/components/OfferCard';
import AgreementPreview from '@/features/negotiation/components/AgreementPreview';
import AgentWorkflowStepper from '@/features/negotiation/components/AgentWorkflowStepper';
import RagContextViewer from '@/features/negotiation/components/RagContextViewer';
import PriceChart from '@/features/negotiation/components/PriceChart';
import TransactionValidationModal from '@/components/negotiation/TransactionValidationModal';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';

export default function TransportNegotiationRoom() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const payload = location.state?.payload;
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState<any>(null);
  
  const [activeTab, setActiveTab] = useState<'timeline' | 'terminal'>('timeline');
  const [activeThreadIdx, setActiveThreadIdx] = useState<number>(0);
  const [isParallelRunning, setIsParallelRunning] = useState(false);
  const [liveTerminalLogs, setLiveTerminalLogs] = useState<Array<{ time: string; tag: string; text: string; color?: string }>>([]);
  
  const [isRagOpen, setIsRagOpen] = useState(false);
  const [showAgreement, setShowAgreement] = useState(false);
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [visibleMessagesCount, setVisibleMessagesCount] = useState<number>(0);

  useEffect(() => {
    if (!payload) {
      navigate('/dashboard/transport');
      return;
    }
    handleParallelNegotiation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [payload]);

  const handleParallelNegotiation = async () => {
    setLoading(true);
    setIsParallelRunning(true);
    const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    setLiveTerminalLogs([
      { time: now(), tag: 'CLUSTER', color: 'text-emerald-400', text: `🚀 Initializing LangGraph Transport Orchestrator...` },
      { time: now(), tag: 'POLICY', color: 'text-purple-400', text: `Floor Price: ₹${payload?.floor_price}/trip | Distance: Highway routing.` },
      { time: now(), tag: 'DISCOVERY', color: 'text-blue-400', text: `Scanning candidate vehicles in Maharashtra...` }
    ]);

    try {
      const res = await api.post('/transport/parallel-negotiate', payload);
      setResults(res.data);
      
      const winnerIdx = res.data.all_negotiations?.findIndex((n:any) => n.vehicle.vehicle_name === res.data.winner?.vehicle?.vehicle_name) || 0;
      setActiveThreadIdx(Math.max(0, winnerIdx));
      
      setLiveTerminalLogs(prev => [
        ...prev,
        { time: now(), tag: 'NEGOTIATION', color: 'text-amber-400', text: `Running parallel negotiations across 7 transport threads...` },
        { time: now(), tag: 'WINNER', color: 'text-emerald-400', text: `Winner selected: ${res.data.winner?.vehicle?.vehicle_name} at ₹${res.data.winner?.agreed_price || res.data.winner?.pricing_rules?.target_price}` }
      ]);
      
    } catch (e) {
      console.warn('Transport Negotiation Error', e);
      setLiveTerminalLogs(prev => [
        ...prev,
        { time: now(), tag: 'ERROR', color: 'text-red-500', text: `Failed to complete negotiation.` }
      ]);
    } finally {
      setLoading(false);
      setIsParallelRunning(false);
      setShowAgreement(true);
    }
  };

  const activeNeg = results?.all_negotiations?.[activeThreadIdx];
  const finalPrice = activeNeg?.agreed_price || activeNeg?.pricing_rules?.target_price || payload?.floor_price || 0;
  const isWinner = results?.winner?.vehicle?.vehicle_name === activeNeg?.vehicle?.vehicle_name;

  // Chart data for freight trends
  const chartData = useMemo(() => {
    const base = Number(finalPrice) || 5000;
    return [
      { name: 'Day 1', price: Math.round(base * 0.94) },
      { name: 'Day 5', price: Math.round(base * 0.96) },
      { name: 'Day 10', price: Math.round(base * 0.95) },
      { name: 'Day 15', price: Math.round(base * 0.98) },
      { name: 'Day 20', price: Math.round(base * 1.02) },
      { name: 'Day 25', price: Math.round(base * 1.01) },
      { name: 'Day 30', price: Math.round(base) },
    ];
  }, [finalPrice]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeThreadIdx, results, activeTab, visibleMessagesCount]);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [liveTerminalLogs, activeTab]);

  useEffect(() => {
    setVisibleMessagesCount(0);
    const transcript = activeNeg?.transcript;
    if (transcript && transcript.length > 0) {
      let count = 0;
      const interval = setInterval(() => {
        count++;
        setVisibleMessagesCount(count);
        if (count >= transcript.length) {
          clearInterval(interval);
        }
      }, 1500); // Reveal one message pair every 1.5 seconds
      return () => clearInterval(interval);
    } else {
      setVisibleMessagesCount(0);
    }
  }, [activeThreadIdx, activeNeg?.transcript]);

  if (loading && !results) {
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center space-y-3">
        <div className="w-10 h-10 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-600 font-bold text-sm">Initializing LangGraph Transport Engine...</p>
      </div>
    );
  }

  const dealDataForModal = {
    id: activeNeg?.vehicle?.vehicle_id || 'TRN-123',
    negotiation_id: activeNeg?.vehicle?.vehicle_id || 'TRN-123',
    crop: payload?.crop || 'Produce',
    quantity: payload?.quantity_kg || 0,
    price: finalPrice,
    final_price: finalPrice,
    buyer: user?.name || user?.full_name || 'Buyer Enterprise',
    farmer: activeNeg?.vehicle?.vehicle_name || 'Transporter',
    farmer_name: activeNeg?.vehicle?.vehicle_name || 'Transporter',
    status: activeNeg?.status || 'DEAL'
  };

  return (
    <div className="h-[calc(100vh-90px)] flex flex-col xl:flex-row gap-6 p-4 max-w-[1600px] mx-auto animate-in fade-in duration-300">
      
      {/* ════ COLUMN 1: Intelligence Panel (Left ~25%) ════ */}
      <div className="w-full xl:w-1/4 flex flex-col gap-4 overflow-y-auto">
        <Link 
          to="/dashboard/transport" 
          className="inline-flex items-center text-sm font-semibold text-slate-500 hover:text-emerald-700 transition"
        >
          <ArrowLeft size={16} className="mr-1" /> Exit Workspace
        </Link>
        
        {/* Stakeholder Scope Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <ShieldCheck size={17} className="text-indigo-600" /> AI Coordination Scope
            </h2>
          </div>
          
          <div className="space-y-3 pt-1">
            <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl text-xs space-y-1">
              <p className="font-bold text-indigo-700 uppercase tracking-wider mb-2">
                TRANSPORTER &bull; TRANSPORT ONLY
              </p>
              
              <div className="flex flex-col gap-1.5 mt-2">
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />
                  <span className="text-slate-400">Buyer / Supplier</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-emerald-600" />
                  <span className="text-slate-800 font-bold">Transport</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />
                  <span className="text-slate-400">Warehouse</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />
                  <span className="text-slate-400">Processor</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Market Context Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <Briefcase size={17} className="text-blue-600" /> Logistics Context
            </h2>
            <span className="text-[11px] font-bold px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
              {payload?.crop || 'Freight'}
            </span>
          </div>

          <div className="space-y-3 pt-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Lot Volume</span>
              <span className="font-black text-slate-800">{payload?.quantity_kg?.toLocaleString()} kg</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Route</span>
              <span className="font-black text-slate-800 truncate max-w-[120px] text-right" title={`${payload?.pickup_location} → ${payload?.delivery_location}`}>{payload?.pickup_location} → {payload?.delivery_location}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">AI Suggested Floor</span>
              <span className="font-black text-purple-700">₹{payload?.floor_price}</span>
            </div>
          </div>

          {/* Dynamic 30-Day Trend Chart */}
          <div className="pt-2 border-t border-slate-100">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Freight Trend (30 Days)</p>
            <PriceChart data={chartData} isTransport={true} />
          </div>
        </div>

        {/* Parallel Threads Switcher (acting like Live Variables) */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 space-y-3">
          <h2 className="font-bold text-slate-800 text-sm flex items-center gap-2">
            <Database size={17} className="text-purple-600" /> Parallel Threads
          </h2>
          <div className="space-y-2">
            {results?.all_negotiations?.map((neg: any, idx: number) => {
              const isWin = results?.winner?.vehicle?.vehicle_name === neg.vehicle.vehicle_name;
              return (
                <button
                  key={idx}
                  onClick={() => setActiveThreadIdx(idx)}
                  className={`w-full text-left p-2.5 rounded-xl border text-xs transition flex flex-col gap-1 ${activeThreadIdx === idx ? 'bg-indigo-50 border-indigo-200' : 'bg-slate-50 border-slate-100 hover:bg-slate-100'}`}
                >
                  <div className="flex justify-between font-bold">
                    <span className={`truncate max-w-[140px] ${activeThreadIdx === idx ? 'text-indigo-800' : 'text-slate-700'}`}>{neg.vehicle.vehicle_name}</span>
                    {isWin && <CheckCircle size={14} className="text-emerald-500 shrink-0" />}
                  </div>
                  <span className="text-[10px] text-slate-500 truncate">{neg.status} • ₹{neg.agreed_price || neg.pricing_rules?.target_price}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ════ COLUMN 2: The Timeline / Chat Stream (Center ~50%) ════ */}
      <div className="w-full xl:w-2/4 bg-white rounded-2xl shadow-sm border border-slate-200/80 flex flex-col overflow-hidden relative">
        
        {/* Header Bar with Tabs & WebSocket Pulse */}
        <div className="p-3.5 border-b border-slate-100 bg-slate-50 flex flex-wrap justify-between items-center z-10 sticky top-0 gap-2">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <MessageSquare size={17} className="text-emerald-600" /> AI Agent Negotiation
            </h3>
            <span className="text-slate-300">•</span>
            <span className="text-xs text-slate-500 font-mono">#{activeNeg?.vehicle?.vehicle_id?.substring(0,8) || 'TRN-123'}</span>
          </div>

          <div className="flex items-center gap-3">
            {/* Tab Selector */}
            <div className="bg-slate-200/70 p-1 rounded-xl flex items-center gap-1 text-xs">
              <button
                onClick={() => setActiveTab('timeline')}
                className={`px-2.5 py-1 rounded-lg font-bold transition ${
                  activeTab === 'timeline' 
                    ? 'bg-white text-slate-900 shadow-sm' 
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                💬 Chat Timeline
              </button>
              <button
                onClick={() => setActiveTab('terminal')}
                className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                  activeTab === 'terminal' 
                    ? 'bg-slate-900 text-emerald-400 shadow-sm' 
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <TerminalIcon size={12} /> Live Terminal
              </button>
            </div>

            {/* WebSocket Connection Ping */}
            <div className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${isParallelRunning ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500 animate-pulse'}`}></span>
              <span className="text-[10px] font-bold text-slate-500 font-mono uppercase">
                {isParallelRunning ? 'RUNNING' : 'LIVE'}
              </span>
            </div>
          </div>
        </div>

        {/* View Mode 1: Chat Timeline */}
        {activeTab === 'timeline' ? (
          <div className="flex-1 overflow-y-auto bg-slate-50/50 p-5 space-y-5">
            {isWinner && (
              <div className="bg-emerald-100/50 border border-emerald-200 rounded-xl p-3 text-center mb-4">
                <span className="text-emerald-800 font-bold text-xs uppercase tracking-wider">Top AI Recommendation Selected</span>
              </div>
            )}
            
            {activeNeg?.transcript?.slice(0, visibleMessagesCount).map((t: any, tIdx: number) => (
              <React.Fragment key={tIdx}>
                {/* Stakeholder Agent */}
                <OfferCard 
                  agent="Farmer / Buyer Agent"
                  price={t.stakeholder_offer}
                  quantity={payload.quantity_kg}
                  quality="Standard"
                  deliveryDate="Immediate"
                  transportIncluded={true}
                  warehouseIncluded={false}
                  validity="24 Hours"
                  isFarmer={false}
                  isTransport={true}
                />
                <ChatBubble 
                  agent="Farmer / Buyer Agent"
                  price={t.stakeholder_offer}
                  message={t.stakeholder_message || `I need a transport vehicle for ${payload.quantity_kg}kg of ${payload.crop}. My target freight budget is ₹${t.stakeholder_offer}. Can we close this deal?`}
                  isFarmer={false}
                  isSystem={false}
                  isInteractive={false}
                  reasoning={t.stakeholder_reasoning || [`Round ${t.round}`]}
                />

                {/* Transporter Agent */}
                <div className="animate-in slide-in-from-right-4 duration-500 delay-500 fill-mode-both">
                  <OfferCard 
                    agent="Transporter Agent (You)"
                    price={t.transporter_counter}
                    quantity={payload.quantity_kg}
                    quality="Standard"
                    deliveryDate="Immediate"
                    transportIncluded={true}
                    warehouseIncluded={false}
                    validity="24 Hours"
                    isFarmer={true}
                    isTransport={true}
                  />
                  <ChatBubble 
                    agent="Transporter Agent (You)"
                    price={t.transporter_counter}
                    message={t.message}
                    isFarmer={true}
                    isSystem={false}
                    isInteractive={false}
                    reasoning={t.transporter_reasoning || (t.status === 'ACCEPTED' ? [`Final Deal Accepted at ₹${t.stakeholder_offer}`, `Round ${t.round}`] : [`Round ${t.round}`])}
                  />
                </div>
              </React.Fragment>
            ))}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          /* View Mode 2: Real-Time Streaming Terminal */
          <div className="flex-1 bg-slate-950 p-4 font-mono text-[11px] leading-relaxed overflow-y-auto space-y-2 select-text dark-scroll text-slate-100 flex flex-col">
            <div className="text-slate-500 pb-2 border-b border-slate-800 text-[10px]">
              # LangGraph Multi-Agent Negotiation Daemon • Transport Network<br />
              # Target: {payload?.pickup_location} → {payload?.delivery_location} • Floor: ₹{payload?.floor_price}
            </div>

            {liveTerminalLogs.length === 0 ? (
              <div className="text-center py-16 text-slate-500 space-y-3">
                <TerminalIcon size={32} className="mx-auto text-slate-700" />
                <p>Terminal idle.</p>
              </div>
            ) : (
              liveTerminalLogs.map((log, lIdx) => (
                <div key={lIdx} className="flex items-start gap-2 animate-in fade-in duration-150">
                  <span className="text-slate-600 shrink-0">[{log.time}]</span>
                  <span className={`font-bold shrink-0 ${log.color || 'text-slate-300'}`}>[{log.tag}]</span>
                  <span className="text-slate-200 break-words flex-1">{log.text}</span>
                </div>
              ))
            )}
            <div ref={terminalEndRef} />
          </div>
        )}

        {/* Bottom Fast Action Bar */}
        <div className="p-3 bg-white border-t border-slate-100 flex items-center justify-between text-xs">
          <button
            onClick={handleParallelNegotiation}
            disabled={isParallelRunning}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-bold transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw size={13} className={isParallelRunning ? "animate-spin text-emerald-400" : "text-emerald-400"} />
            <span>{isParallelRunning ? 'Negotiating Transport...' : '⚡ Auto-Parallel Negotiation'}</span>
          </button>
          <span className="text-slate-400 text-[11px]">
            Powered by LangGraph
          </span>
        </div>
      </div>
      
      {/* ════ COLUMN 3: Action Panel & Workflow (Right ~25%) ════ */}
      <div className="w-full xl:w-1/4 flex flex-col gap-6 overflow-y-auto">
        
        {/* LangGraph Execution Stepper */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 space-y-4">
          <h2 className="font-bold text-slate-800 text-sm flex items-center gap-2">
            <Zap size={17} className="text-emerald-500" /> LangGraph Execution
          </h2>
          <AgentWorkflowStepper activeAgent={isParallelRunning ? 'Negotiator' : 'Deal Finalized'} />
          
          <button 
            onClick={() => setIsRagOpen(true)}
            className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition text-xs flex justify-center items-center gap-2 cursor-pointer"
          >
            <Database size={15} className="text-emerald-600" /> View RAG Context
          </button>
        </div>

        {/* Dynamic Action Area */}
        {showAgreement ? (
          <AgreementPreview 
            dealData={dealDataForModal} 
            onSignAndClose={() => setShowValidationModal(true)} 
            isTransport={true}
          />
        ) : (
          <div className="bg-slate-900 rounded-2xl shadow-sm border border-slate-800 p-5 text-white space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <ShieldCheck size={18} className="text-emerald-400" /> Copilot Override
              </h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Negotiation running...
            </p>
          </div>
        )}
      </div>
      
      {/* Floating RAG Modal */}
      <RagContextViewer isOpen={isRagOpen} onClose={() => setIsRagOpen(false)} crop={payload?.crop || 'Produce'} preloadedData={activeNeg?.rag_results || null} query={activeNeg?.rag_query || 'market prices'} />

      {/* APMC Validated Smart Contract Modal */}
      <TransactionValidationModal
        isOpen={showValidationModal}
        onClose={() => setShowValidationModal(false)}
        dealData={dealDataForModal}
        buyerUser={user}
        isTransport={true}
      />

    </div>
  );
}
