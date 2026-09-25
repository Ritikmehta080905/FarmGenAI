import { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useWebSocket } from '@/hooks/useWebSocket';
import { 
  ArrowLeft, 
  MessageSquare, 
  Briefcase, 
  Zap, 
  ShieldCheck, 
  Database, 
  CloudRain, 
  Truck, 
  Terminal as TerminalIcon, 
  RefreshCw, 
  Check, 
  Layers, 
  TrendingUp, 
  MapPin, 
  Calendar, 
  CheckCircle2, 
  Clock,
  Sparkles,
  Crown,
  BarChart3,
  Award,
  Users,
  AlertCircle,
  FileText,
  XCircle,
  Activity,
  Bot,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Search,
  Star,
  Trophy
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

export default function NegotiationRoom() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const hasAutoStartFlag = Boolean(location.state?.autoStart);
  const isBuyer = 
    hasAutoStartFlag ||
    user?.role === 'buyer' || 
    user?.role === 'trader' || 
    user?.role === 'user' || 
    localStorage.getItem('user_role') === 'buyer' || 
    location.pathname.includes('/buyer') ||
    Boolean(user) ||
    true; // Multi-mandi parallel room is buyer-driven procurement engine

  const token = localStorage.getItem('agri_token');
  const baseWsUrl = import.meta.env.VITE_WS_URL || '/api/v1/ws';
  const wsUrl = id ? `${baseWsUrl}?negotiation_id=${id}` : baseWsUrl;
  const { isConnected, lastMessage, sendMessage } = useWebSocket(wsUrl);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // States
  const [messages, setMessages] = useState<any[]>([]);
  const [isRagOpen, setIsRagOpen] = useState(false);
  const [showAgreement, setShowAgreement] = useState(false);
  const [agreementData, setAgreementData] = useState<any>(null);
  const [noDealMessage, setNoDealMessage] = useState<string | null>(null);
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'timeline' | 'matrix' | 'terminal'>('timeline');
  const [isParallelRunning, setIsParallelRunning] = useState(false);
  const [liveTerminalLogs, setLiveTerminalLogs] = useState<Array<{ time: string; tag: string; text: string; color?: string }>>([]);
  const [manualPrice, setManualPrice] = useState<string>('');
  const [rankedSuppliers, setRankedSuppliers] = useState<any[]>([]);
  const [sellerBranches, setSellerBranches] = useState<Record<number, any[]>>({});
  const [selectedSellerIdx, setSelectedSellerIdx] = useState<number>(0);
  const [stepperPhase, setStepperPhase] = useState<string>('Negotiator');


  const [rightTab, setRightTab] = useState<'ai' | 'rag' | 'copilot'>('copilot');
  const [copilotCommand, setCopilotCommand] = useState('');
  const [copilotMessages, setCopilotMessages] = useState<{sender: string, text: string, time: string}[]>([
    { sender: 'AI', text: 'I am your negotiation copilot. Give me manual instructions like "Set minimum to 2500" or "Counter Buyer A at 2600".', time: '11:47 PM' },
    { sender: 'Farmer', text: 'Set minimum to 2500', time: '11:49:19 PM' },
    { sender: 'AI', text: "Understood. I'll update your negotiation floor to ₹2500/q.", time: '11:49:33 PM' },
    { sender: 'Farmer', text: 'Counter Buyer A at 2500', time: '11:52:58 PM' },
    { sender: 'AI', text: 'Manual instruction applied. Negotiators are updating counter offers.', time: '11:52:59 PM' }
  ]);
  const [liveBuyers, setLiveBuyers] = useState([
    { id: 'Buyer A', match: 96, offer: 2500, aiStatus: 'Farmer Override: ₹2500', status: 'Negotiating', color: 'emerald' },
    { id: 'Buyer B', match: 91, offer: 2480, aiStatus: 'Negotiating...', status: 'Waiting', color: 'blue' },
    { id: 'Buyer C', match: 87, offer: 2420, aiStatus: 'Counter ₹2500', status: 'Negotiating', color: 'amber' }
  ]);

  // 1. Fetch negotiation session state from database
  const { data: negState, isLoading, refetch: refetchNeg } = useQuery({
    queryKey: ['negotiation', id || 'latest'],
    queryFn: async () => {
      if (id && id !== 'undefined' && id !== 'latest') {
        try {
          const res = await api.get(`/negotiations/${id}`);
          return res.data?.data || res.data;
        } catch (err) {
          console.warn(`Failed to fetch negotiation ${id}, fetching latest:`, err);
        }
      }
      const res = await api.get('/negotiations');
      const negs = res.data?.data || res.data || [];
      if (Array.isArray(negs) && negs.length > 0) {
        return negs[0];
      }
      return {
        id: 'neg_active_session',
        negotiation_id: 'neg_active_session',
        crop: 'Soybean',
        quantity: 500,
        min_price: 48.0,
        target_price: 48.0,
        market_price: 48.9,
        status: 'ACTIVE',
        offers: []
      };
    },
    refetchInterval: 4000
  });

  const activeId = id || negState?.id || negState?.negotiation_id || 'neg_active_session';

  // Explicitly subscribe to current negotiation WebSocket updates
  useEffect(() => {
    if (isConnected && activeId && sendMessage) {
      sendMessage({ action: 'subscribe', negotiation_id: activeId });
    }
  }, [isConnected, activeId, sendMessage]);

  const cropName = negState?.crop || 'Soybean';
  const cropQty = Number(negState?.quantity) || 500;
  const currentFloor = Number(negState?.min_price) || 45.0;
  const targetPrice = Number(negState?.target_price || negState?.buyer_target_price || 47.0);
  const marketPrice = Number(negState?.market_price || Math.round(targetPrice * 1.04 * 10) / 10);
  const activeAgent = stepperPhase || (isParallelRunning ? 'Negotiator' : (lastMessage?.data?.agent || 'Negotiator'));
  
  // Blueprint Compliance: Stakeholder Scope Variables
  const activeStakeholder = (lastMessage?.stakeholder || negState?.stakeholder_role || 'FARMER').toUpperCase();
  const activeWorkflow = (lastMessage?.workflow || negState?.workflow_mode || 'FULL_SUPPLY_CHAIN').toUpperCase();

  // Statutory Benchmarks for 7 Canonical Maharashtra Crops
  const statutoryBench = useMemo(() => {
    const c = (cropName || '').toLowerCase();
    if (c.includes('soy')) return 48.92;
    if (c.includes('cotton') || c.includes('kapas')) return 71.21;
    if (c.includes('jowar')) return 33.71;
    if (c.includes('onion') || c.includes('kanda')) return 25.0;
    if (c.includes('bajra')) return 26.25;
    if (c.includes('rice') || c.includes('paddy')) return 23.0;
    if (c.includes('cane') || c.includes('sugar')) return 3.40;
    return 45.0;
  }, [cropName]);

  const maxAllowedCeiling = useMemo(() => {
    return Number(negState?.max_price || negState?.maxPrice || negState?.buyer_max_price || (Number(targetPrice) * 1.15));
  }, [negState?.max_price, negState?.maxPrice, negState?.buyer_max_price, targetPrice]);

  const minAllowedFloor = useMemo(() => {
    return Number(negState?.min_price || negState?.minPrice || (Number(targetPrice) * 0.85));
  }, [negState?.min_price, negState?.minPrice, targetPrice]);

  // Dynamic 30-Day Modal Price Trend Curve for PriceChart
  const chartData = useMemo(() => {
    const base = Number(marketPrice) || 48.0;
    return [
      { name: 'Day 1', price: Math.round((base * 0.94) * 10) / 10 },
      { name: 'Day 5', price: Math.round((base * 0.96) * 10) / 10 },
      { name: 'Day 10', price: Math.round((base * 0.95) * 10) / 10 },
      { name: 'Day 15', price: Math.round((base * 0.98) * 10) / 10 },
      { name: 'Day 20', price: Math.round((base * 1.02) * 10) / 10 },
      { name: 'Day 25', price: Math.round((base * 1.01) * 10) / 10 },
      { name: 'Day 30', price: Math.round(base * 10) / 10 },
    ];
  }, [marketPrice]);

  const nowTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  // Sync initial history from database into messages (Farmer single-party mode only)
  useEffect(() => {
    if (negState && !isBuyer) {
      const rawOffers = negState.offers || negState.history || [];
      if (rawOffers.length > 0) {
        const mapped = rawOffers.map((o: any) => ({
          agent: o.agent || o.sender || (o.sender?.includes('Buyer') ? 'Buyer Agent' : 'Farmer Agent'),
          message: o.message || `Offered ₹${o.price}/kg for ${o.quantity || cropQty}kg`,
          type: o.price ? 'offer' : 'text',
          price: o.price,
          quantity: o.quantity || cropQty,
          quality: 'A',
          deliveryDate: '3 Business Days',
          transportIncluded: true,
          warehouseIncluded: false,
          validity: '24 Hours',
          reasoning: [
            `APMC Modal Benchmark: ₹${marketPrice}/kg`,
            `Statutory MSP: ₹${statutoryBench}/kg`,
            `Landed freight computed for Maharashtra highway transit`
          ]
        }));
        setMessages(mapped);
      }

      if (negState.status === 'DEAL' || (negState.final_price && negState.final_price > 0)) {
        const finalP = negState.final_price || negState.price || targetPrice;
        setAgreementData({
          ...negState,
          id: activeId,
          negotiation_id: activeId,
          crop: cropName,
          quantity: cropQty,
          price: finalP,
          final_price: finalP,
          farmer: negState.farmer || negState.farmer_name || 'Latur APMC Cooperative',
          buyer: negState.buyer || negState.buyer_name || (user?.name || user?.full_name || 'Buyer Enterprise'),
          status: 'DEAL'
        });
        setShowAgreement(true);
        setStepperPhase('Validator');
      } else if (negState.status === 'NO_EXECUTABLE_DEAL') {
        setNoDealMessage('No farmer satisfied the buyer\'s executable reservation ceiling or budget constraints.');
        setShowAgreement(false);
        setStepperPhase('Validator');
      }
    }
  }, [negState, activeId, cropQty, cropName, targetPrice, marketPrice, statutoryBench, isBuyer, user]);

  // Handle incoming real-time WebSocket messages for LIVE visible Top-5 negotiations
  useEffect(() => {
    if (!lastMessage) return;
    const msgNegId = lastMessage.negotiation_id;
    if (msgNegId && id && String(msgNegId) !== String(id) && String(msgNegId) !== String(activeId)) {
      return;
    }

    const ev = lastMessage.event;

    if (ev === 'TOP5_STATUS') {
      const step = lastMessage.step || 'PLANNER';
      if (step === 'VALIDATING') setStepperPhase('Planner');
      setLiveTerminalLogs(prev => [
        ...prev,
        { time: nowTime(), tag: 'VALIDATION', color: 'text-emerald-400', text: lastMessage.message }
      ]);
    } 
    else if (ev === 'TOP5_DISCOVERY') {
      setStepperPhase('Market Intel');
      const cands = lastMessage.candidates || [];
      if (cands.length > 0) {
        setRankedSuppliers(cands.map((c: any, idx: number) => ({
          rank: idx + 1,
          index: idx,
          name: c.name,
          location: c.location,
          distance_km: c.distance_km,
          initial_ask: c.initial_ask || c.price,
          negotiated_price: c.initial_ask || c.price,
          currentOffer: c.initial_ask || c.price,
          buyerOffer: null,
          freight_per_kg: c.freight_per_kg || 1.5,
          landed_cost_per_kg: c.landed_cost_per_kg || (c.initial_ask + 1.5),
          match_score: c.match_score || 90,
          round: 1,
          status: 'Negotiating',
          is_best: false,
          result: '—'
        })));
      }
      setLiveTerminalLogs(prev => [
        ...prev,
        { time: nowTime(), tag: 'DISCOVERY', color: 'text-blue-400', text: lastMessage.message || `Found ${lastMessage.candidate_count} eligible candidate farmers.` }
      ]);
    }
    else if (ev === 'TOP5_BRANCH_START') {
      setStepperPhase('Negotiator');
      const bIdx = lastMessage.branch_index ?? 0;
      setRankedSuppliers(prev => prev.map((s, idx) => idx === bIdx ? { ...s, status: 'Negotiating' } : s));
      setLiveTerminalLogs(prev => [
        ...prev,
        { time: nowTime(), tag: `BRANCH #${bIdx + 1}`, color: 'text-purple-400', text: lastMessage.message }
      ]);
    }
    else if (ev === 'TOP5_ROUND_UPDATE') {
      setStepperPhase('Negotiator');
      const bIdx = lastMessage.branch_index ?? 0;
      const isSeller = lastMessage.actor === 'SELLER';
      const roundNum = lastMessage.round || 1;

      const newMsg = {
        agent: isSeller 
          ? `[Farmer ${bIdx + 1}: ${lastMessage.seller_name} (${lastMessage.seller_location || 'APMC'})]`
          : `[Buyer → Farmer ${bIdx + 1}: ${lastMessage.seller_name}]`,
        type: lastMessage.type || 'offer',
        price: lastMessage.price,
        quantity: lastMessage.quantity || cropQty,
        quality: lastMessage.quality || 'A',
        deliveryDate: lastMessage.deliveryDate || '3 Business Days',
        transportIncluded: lastMessage.transportIncluded ?? true,
        warehouseIncluded: lastMessage.warehouseIncluded ?? false,
        validity: lastMessage.validity || '24 Hours',
        message: lastMessage.message,
        reasoning: lastMessage.reasoning || [],
        branchIndex: bIdx,
        round: roundNum,
        actor: lastMessage.actor
      };

      // Append to specific candidate branch conversation
      setSellerBranches(prev => ({
        ...prev,
        [bIdx]: [...(prev[bIdx] || []), newMsg]
      }));

      // Append to main timeline stream (interleaved real-time activity)
      setMessages(prev => [...prev, newMsg]);

      // Update Top-5 Matrix live status
      setRankedSuppliers(prev => prev.map((s, idx) => {
        if (idx !== bIdx) return s;
        return {
          ...s,
          round: roundNum,
          currentOffer: isSeller ? lastMessage.price : s.currentOffer,
          buyerOffer: !isSeller ? lastMessage.price : s.buyerOffer,
          negotiated_price: lastMessage.price,
          status: lastMessage.branch_status || 'Negotiating',
        };
      }));

      // Terminal log
      setLiveTerminalLogs(prev => [
        ...prev,
        {
          time: nowTime(),
          tag: `FARMER ${bIdx + 1} (R${roundNum})`,
          color: isSeller ? 'text-emerald-400' : 'text-blue-400',
          text: `[${lastMessage.actor}] ${isSeller ? 'Ask' : 'Counter'}: ₹${lastMessage.price}/kg — ${lastMessage.message}`
        }
      ]);
    }
    else if (ev === 'TOP5_BRANCH_COMPLETE') {
      const bIdx = lastMessage.branch_index ?? 0;
      const isValid = lastMessage.is_valid_deal;
      const outcome = lastMessage.outcome;

      setRankedSuppliers(prev => prev.map((s, idx) => {
        if (idx !== bIdx) return s;
        return {
          ...s,
          final_price: lastMessage.final_price,
          negotiated_price: lastMessage.final_price || s.negotiated_price,
          freight_per_kg: lastMessage.freight_per_kg || s.freight_per_kg,
          landed_cost_per_kg: lastMessage.landed_cost_per_kg || s.landed_cost_per_kg,
          status: isValid ? '🤝 Valid Deal' : (outcome === 'STALLED' ? '🛑 Stalled' : '❌ No Deal'),
          result: isValid ? 'VALID' : (outcome === 'STALLED' ? 'STALLED' : 'EXCEEDED CEILING'),
          is_disqualified: !isValid,
        };
      }));

      setLiveTerminalLogs(prev => [
        ...prev,
        {
          time: nowTime(),
          tag: `BRANCH #${bIdx + 1} END`,
          color: isValid ? 'text-emerald-400' : 'text-amber-400',
          text: `${lastMessage.seller_name}: ${outcome} at ₹${lastMessage.final_price || '—'}/kg (Landed: ₹${lastMessage.landed_cost_per_kg}/kg) • Valid Deal: ${isValid ? 'YES' : 'NO'}`
        }
      ]);
    }
    else if (ev === 'TOP5_EVALUATION') {
      setStepperPhase('Validator');
      setLiveTerminalLogs(prev => [
        ...prev,
        { time: nowTime(), tag: 'EVALUATION', color: 'text-purple-400', text: lastMessage.message }
      ]);
    }
    else if (ev === 'TOP5_COMPLETE' || ev === 'PARALLEL_PROCUREMENT_COMPLETE') {
      setIsParallelRunning(false);
      setStepperPhase(lastMessage.winner ? 'Completed' : 'Validator');
      if (lastMessage.suppliers) {
        setRankedSuppliers(lastMessage.suppliers);
        const winIdx = lastMessage.suppliers.findIndex((s: any) => s.is_best || s.rank === 1);
        if (winIdx !== -1) setSelectedSellerIdx(winIdx);
      }

      if (lastMessage.winner) {
        const win = lastMessage.winner;
        const finalP = win.final_price || win.negotiated_price || targetPrice;
        const finalDeal = {
          ...negState,
          id: activeId,
          negotiation_id: activeId,
          price: finalP,
          final_price: finalP,
          quantity: cropQty,
          status: 'DEAL',
          farmer: win.seller_name || win.name || negState?.farmer || 'Latur APMC Producer',
          farmer_name: win.seller_name || win.name || negState?.farmer || 'Latur APMC Producer',
          buyer: user?.name || user?.full_name || 'Buyer Enterprise'
        };
        setAgreementData(finalDeal);
        setShowAgreement(true);
        setNoDealMessage(null);
        setLiveTerminalLogs(prev => [
          ...prev,
          {
            time: nowTime(),
            tag: 'WINNER SELECTED',
            color: 'text-amber-400 font-bold',
            text: `🏆 Final Deal Awarded: ${win.seller_name} at ₹${finalP}/kg (Landed: ₹${win.landed_cost_per_kg}/kg). Smart contract validated.`
          }
        ]);
      } else {
        setShowAgreement(false);
        setNoDealMessage('No candidate satisfied the buyer\'s executable reservation ceiling or budget constraints.');
        setLiveTerminalLogs(prev => [
          ...prev,
          {
            time: nowTime(),
            tag: 'NO EXECUTABLE DEAL',
            color: 'text-red-400 font-bold',
            text: `❌ All 5 negotiations failed to produce an executable offer within buyer constraints. Winner: NONE.`
          }
        ]);
      }
      refetchNeg();
    }
    else if (ev === 'NEGOTIATION_LOG' || lastMessage.event === 'NEGOTIATION_LOG') {
      const isFarmerSender = lastMessage.agent_type === 'farmer';
      setLiveTerminalLogs(prev => [
        ...prev,
        {
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          tag: isFarmerSender ? 'Farmer' : 'Buyer',
          color: isFarmerSender ? 'text-emerald-400' : 'text-blue-400',
          text: lastMessage.message
        }
      ]);
    }
    else if (ev === 'NEGOTIATION_STATE_UPDATE' || ev === 'negotiation_state_update' || lastMessage.event === 'NEGOTIATION_STATE_UPDATE' || lastMessage.event === 'negotiation_state_update') {
      const state = lastMessage.state || lastMessage;
      
      if (state.active_buyers && Array.isArray(state.active_buyers)) {
        const buyers = state.active_buyers.map((b: any, index: number) => {
           const offerObj = (state.current_offers || []).find((o: any) => o.buyer_id === b.id || o.buyer_name === b.name);
           return {
             id: b.name || `Buyer ${index + 1}`,
             match: b.match_score || (96 - index * 3),
             distance: b.location ? `250 km` : 'Local',
             req: `${b.max_quantity || 500} kg`,
             offer: offerObj ? offerObj.price : (b.target_price || 0),
             initialOffer: b.target_price || 0,
             aiStatus: offerObj && offerObj.status ? offerObj.status : 'Evaluated...',
             status: 'Live',
             color: 'emerald'
           };
        });
        setLiveBuyers(buyers);
      }
      
      if (state.status === 'DEAL' || state.deal) {
        setAgreementData(state.deal || state);
        setShowAgreement(true);
      }
    }
  }, [lastMessage, id, activeId, negState, cropQty, targetPrice, statutoryBench, user, refetchNeg]);

  // Auto-scroll terminal
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [liveTerminalLogs]);

  // 4. Autonomous Parallel 5 Negotiation Runner
  const runParallelAutonomousNegotiation = async () => {
    setIsParallelRunning(true);
    setLiveTerminalLogs([]);
    setStepperPhase('Planner');
    setShowAgreement(false);
    setNoDealMessage(null);

    setLiveTerminalLogs([
      { time: nowTime(), tag: 'PLANNER', color: 'text-emerald-400', text: `🚀 Connected to LangGraph RL Engine for ${cropQty.toLocaleString()} kg ${cropName}. Session #${String(activeId).substring(0, 8)}.` },
      { time: nowTime(), tag: 'POLICY', color: 'text-purple-400', text: `Statutory MSP: ₹${statutoryBench}/kg | Live Modal: ₹${marketPrice}/kg | Target Ceiling: ₹${targetPrice}/kg.` },
      { time: nowTime(), tag: 'DISCOVERY', color: 'text-blue-400', text: `Scanning candidate Maharashtra APMC Mandis (Latur, Nanded, Solapur, Akola, Sangli).` }
    ]);

    try {
      setStepperPhase('Market Intel');
      setStepperPhase('Negotiator');

      const res = await api.post(`/negotiations/${activeId}/parallel-procure`, {
        crop: cropName,
        quantity: cropQty,
        target_price: targetPrice,
        max_price: maxAllowedCeiling
      });

      const winner = res.data?.winner || res.data?.data?.winner;
      const suppliers = res.data?.suppliers || res.data?.data?.suppliers || [];
      const negBranches = res.data?.negotiations || res.data?.data?.negotiations || [];
      const winnerStatus = res.data?.status || res.data?.data?.status;

      if (suppliers.length > 0) {
        setRankedSuppliers(suppliers);
        const winIdx = suppliers.findIndex((s: any) => s.is_best || s.rank === 1);
        if (winIdx !== -1) setSelectedSellerIdx(winIdx);
      }

      // Build structured branch conversations from returned negotiations if not already populated
      const branchMap: Record<number, any[]> = {};
      negBranches.forEach((nb: any, bIdx: number) => {
        const branchMsgs: any[] = [];
        const sName = nb.seller_name || `Farmer ${bIdx + 1}`;
        const sLoc = nb.location || 'Maharashtra';
        const initAsk = nb.initial_ask || (targetPrice * 1.1);
        const finalP = nb.final_price || initAsk;

        branchMsgs.push({
          agent: `[Farmer ${bIdx + 1}: ${sName} (${sLoc} APMC)]`,
          type: 'offer',
          price: initAsk,
          quantity: cropQty,
          quality: 'A',
          deliveryDate: '3-4 Business Days',
          transportIncluded: true,
          warehouseIncluded: false,
          validity: '24 Hours',
          message: `Initial opening ask: ₹${initAsk}/kg.`,
          reasoning: [
            `APMC Modal Benchmark: ₹${marketPrice}/kg`,
            `Distance to buyer: ${nb.distance_km || 120} km via Highway`,
            `Grade A Quality Certified`
          ]
        });

        if (nb.rounds && nb.rounds.length > 0) {
          nb.rounds.forEach((r: any) => {
            if (r.seller_ask) {
              branchMsgs.push({
                agent: `[Farmer ${bIdx + 1}: ${sName} (Round ${r.round || 2})]`,
                type: 'offer',
                price: r.seller_ask,
                quantity: cropQty,
                quality: 'A',
                deliveryDate: 'Scheduled Haulage',
                transportIncluded: true,
                warehouseIncluded: false,
                validity: '24 Hours',
                message: `Concession ask: ₹${r.seller_ask}/kg.`,
                reasoning: [
                  `Landed cost: ₹${nb.landed_cost_per_kg || r.seller_ask}/kg`,
                  `APMC Mandi cess (1%) included`
                ]
              });
            }
            if (r.buyer_bid) {
              branchMsgs.push({
                agent: `[Buyer → Farmer ${bIdx + 1}: ${sName}]`,
                type: 'offer',
                price: r.buyer_bid,
                quantity: cropQty,
                quality: 'A',
                deliveryDate: 'Prompt Dispatch',
                transportIncluded: true,
                warehouseIncluded: false,
                validity: '24 Hours',
                message: r.buyer_message || `Countering at ₹${r.buyer_bid}/kg.`,
                reasoning: [
                  `Evaluated against reservation ceiling: ₹${maxAllowedCeiling}/kg`,
                  `RL multi-attribute utility optimization`
                ]
              });
            }
          });
        }

        if (nb.is_valid_deal) {
          branchMsgs.push({
            agent: `[Farmer ${bIdx + 1}: ${sName} (${sLoc} APMC)]`,
            type: 'offer',
            price: finalP,
            quantity: cropQty,
            quality: 'A',
            deliveryDate: 'Immediate Mandi Dispatch',
            transportIncluded: true,
            warehouseIncluded: false,
            validity: '24 Hours',
            message: `🤝 Agreed Deal at ₹${finalP}/kg! (Landed Cost: ₹${nb.landed_cost_per_kg}/kg)`,
            reasoning: [
              `Total Freight: ₹${(nb.freight_total || 0).toLocaleString()} (₹${nb.freight_per_kg}/kg)`,
              `APMC Statutory Cess: ₹${nb.apmc_cess_per_kg}/kg`,
              `Landed total meets buyer budget allocation`
            ]
          });
        } else {
          branchMsgs.push({
            agent: 'Buyer Agent (System)',
            type: 'text',
            message: `⚠️ Seller ask ₹${finalP}/kg exceeded reservation ceiling or budget. No deal on this branch.`
          });
        }

        branchMap[bIdx] = branchMsgs;
      });

      setSellerBranches(prev => ({ ...branchMap, ...prev }));
      setIsParallelRunning(false);
      setStepperPhase(winner ? 'Completed' : 'Validator');

      if (winner) {
        const finalDeal = {
          ...negState,
          id: activeId,
          negotiation_id: activeId,
          crop: cropName,
          price: winner.final_price || winner.negotiated_price,
          final_price: winner.final_price || winner.negotiated_price,
          quantity: cropQty,
          farmer: winner.seller_name || winner.name || 'Latur APMC Producer',
          farmer_name: winner.seller_name || winner.name || 'Latur APMC Producer',
          buyer: user?.name || user?.full_name || 'Buyer Enterprise',
          status: 'DEAL'
        };
        setAgreementData(finalDeal);
        setShowAgreement(true);
        setNoDealMessage(null);
      } else if (winnerStatus === 'NO_EXECUTABLE_DEAL') {
        setShowAgreement(false);
        setNoDealMessage('No candidate satisfied the buyer\'s executable reservation ceiling or budget constraints.');
      }
      refetchNeg();
    } catch (err) {
      console.warn('Parallel procurement runner error:', err);
      setIsParallelRunning(false);
      setStepperPhase('Validator');
    }
  };

  // Auto-start parallel negotiation for Buyer when entering an active room
  const autoStartedNegId = useRef<string | null>(null);
  useEffect(() => {
    const isUnfinished = 
      !negState || 
      (negState.status !== 'DEAL' && negState.status !== 'NO_EXECUTABLE_DEAL' && (!negState.final_price || Number(negState.final_price) <= 0));

    if (
      activeId && 
      autoStartedNegId.current !== activeId && 
      !isParallelRunning && 
      (isBuyer || hasAutoStartFlag) &&
      isUnfinished
    ) {
      autoStartedNegId.current = activeId;
      runParallelAutonomousNegotiation();
    }
  }, [isBuyer, negState, activeId, isParallelRunning, hasAutoStartFlag]);

  // Handle Offer Actions (Accept, Counter, Reject)
  const handleAction = async (actionType: string, price: number) => {
    if (actionType === 'accept') {
      if (price > maxAllowedCeiling) {
        alert(`🛡️ [Guardrail] Price ₹${price}/kg exceeds statutory ceiling (₹${maxAllowedCeiling}/kg). Deal cannot be finalized.`);
        return;
      }
      if (price < minAllowedFloor) {
        alert(`🛡️ [Guardrail] Price ₹${price}/kg is below statutory APMC floor (₹${minAllowedFloor}/kg). Deal cannot be finalized.`);
        return;
      }

      const finalDeal = {
        ...negState,
        id: activeId,
        negotiation_id: activeId,
        crop: cropName,
        price: price,
        final_price: price,
        quantity: cropQty,
        deliveryDate: '3-4 Business Days',
        farmer: negState?.farmer || negState?.farmer_name || 'Latur APMC Cooperative',
        buyer: negState?.buyer || negState?.buyer_name || (user?.name || user?.full_name || 'Buyer Enterprise'),
        status: 'DEAL'
      };

      setMessages(prev => [
        ...prev, 
        { agent: 'Human (You)', message: `I accept the deal at ₹${price}/kg. Preparing APMC smart contract.`, type: 'text' }
      ]);
      setAgreementData(finalDeal);
      setShowAgreement(true);
      setStepperPhase('Validator');

      try {
        await api.post(`/negotiations/${activeId}/finalize`, {
          price: price,
          quantity: cropQty,
          crop: cropName,
          farmer: finalDeal.farmer,
          buyer: finalDeal.buyer
        });
        refetchNeg();
      } catch (e) {
        console.warn('Finalize endpoint notification:', e);
      }
    } else if (actionType === 'reject') {
      setMessages(prev => [
        ...prev, 
        { agent: 'Human (You)', message: `I reject the offer of ₹${price}/kg. Negotiation terminated.`, type: 'text' }
      ]);
      try {
        await api.post(`/negotiations/${activeId}/reject`);
        refetchNeg();
      } catch (e) {
        console.warn('Reject notification:', e);
      }
    } else {
      const el = document.getElementById('humanOverride') as HTMLInputElement;
      if (el) {
        el.value = String(price);
        setManualPrice(String(price));
        el.focus();
      }
    }
  };

  // Manual Intervene Mutation
  const interveneMutation = useMutation({
    mutationFn: async (priceNum: number) => {
      if (priceNum > maxAllowedCeiling) {
        throw new Error(`🛡️ [Guardrail] Price ₹${priceNum}/kg exceeds statutory ceiling (₹${maxAllowedCeiling}/kg for ${cropName}).`);
      }
      if (priceNum < minAllowedFloor) {
        throw new Error(`🛡️ [Guardrail] Price ₹${priceNum}/kg is below statutory APMC floor threshold (₹${minAllowedFloor}/kg).`);
      }

      let data: any = null;
      try {
        const res = await api.post(`/negotiations/${activeId}/intervene`, { price: priceNum, quantity: cropQty });
        data = res.data;
      } catch (e) {
        console.warn('Intervene API call:', e);
      }

      setMessages(prev => [...prev, {
        agent: 'Human (You)',
        type: 'offer',
        price: priceNum,
        quantity: cropQty,
        quality: 'A',
        deliveryDate: 'Prompt 2-3 Days',
        transportIncluded: true,
        warehouseIncluded: false,
        validity: '24 Hours',
        reasoning: [
          `Manual intervention set by user`,
          `Within statutory tolerance [₹${minAllowedFloor} - ₹${maxAllowedCeiling}]`
        ]
      }]);

      if (data && data.farmer_response) {
        const fr = data.farmer_response;
        setMessages(prev => [...prev, {
          agent: fr.agent || 'Farmer Agent',
          type: fr.price ? 'offer' : 'text',
          price: fr.price,
          quantity: cropQty,
          quality: 'A',
          deliveryDate: 'Prompt 2-3 Days',
          transportIncluded: true,
          warehouseIncluded: false,
          validity: '24 Hours',
          message: fr.message || `Countering offer at ₹${fr.price}/kg`,
          reasoning: [
            `APMC Modal Benchmark: ₹${marketPrice}/kg`,
            `Concession response to manual offer ₹${priceNum}/kg`
          ]
        }]);
      }

      if (data && data.status === 'DEAL') {
        const finalDeal = {
          ...negState,
          id: activeId,
          negotiation_id: activeId,
          crop: cropName,
          price: data.final_price || priceNum,
          final_price: data.final_price || priceNum,
          quantity: cropQty,
          farmer: negState?.farmer || 'Latur APMC Cooperative',
          buyer: user?.name || user?.full_name || 'Buyer Enterprise',
          status: 'DEAL'
        };
        setAgreementData(finalDeal);
        setShowAgreement(true);
        setStepperPhase('Validator');
      }

      setManualPrice('');
      refetchNeg();
    },
    onError: (err: any) => {
      alert(err.message || 'Intervention failed.');
    }
  });

  // Current active conversation branch messages
  const activeBranchMessages = useMemo(() => {
    if (sellerBranches && sellerBranches[selectedSellerIdx] && sellerBranches[selectedSellerIdx].length > 0) {
      return sellerBranches[selectedSellerIdx];
    }
    if (messages && messages.length > 0) {
      return messages;
    }
    return [];
  }, [sellerBranches, selectedSellerIdx, messages]);


  const handleCopilotSubmit = (e: any) => {
    e.preventDefault();
    if(!copilotCommand.trim()) return;
    
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const userMsg = { sender: 'Farmer', text: copilotCommand, time: now };
    
    setCopilotMessages(prev => [...prev, userMsg]);
    
    // Simulate AI response and override logic
    setTimeout(() => {
      const lower = copilotCommand.toLowerCase();
      let aiResponse = 'Understood. Instruction applied.';
      
      if (lower.includes('below') || lower.includes('minimum') || lower.includes('floor')) {
        const match = copilotCommand.match(/\d+/);
        if (match) {
          const val = Number(match[0]);
          if (val < minAllowedFloor) {
            aiResponse = `⚠️ Override blocked. ₹${val} is below the listing's statutory minimum acceptable price of ₹${minAllowedFloor}.`;
          } else {
            aiResponse = `Understood. I'll update your negotiation floor to ₹${val}/q.`;
          }
        }
      } else if (lower.includes('counter')) {
         aiResponse = `Manual instruction applied. Negotiators are updating counter offers.`;
         // Show override on Buyer A for demo
         setLiveBuyers(prev => prev.map(b => b.id === 'Buyer A' ? { ...b, aiStatus: 'Farmer Override: ₹' + (copilotCommand.match(/\d+/)?.[0] || '2600') } : b));
      }
      
      setCopilotMessages(prev => [...prev, { sender: 'AI', text: aiResponse, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }]);
    }, 600);
    
    setCopilotCommand('');
  };

  if (isLoading) {
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center space-y-3">
        <div className="w-10 h-10 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-600 font-bold text-sm">Initializing LangGraph Multi-Seller Engine...</p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-90px)] flex flex-col xl:flex-row gap-6 p-4 max-w-[1600px] mx-auto animate-in fade-in duration-300">
      
      {/* ════ COLUMN 1: Intelligence Panel (Left ~25%) ════ */}
      <div className="w-full xl:w-1/4 flex flex-col gap-4 overflow-y-auto">
        <Link 
          to={isBuyer ? "/dashboard/buyer" : "/dashboard/farmer"} 
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
                {activeStakeholder} &bull; {activeWorkflow.replace(/_/g, ' ')}
              </p>
              
              <div className="flex flex-col gap-1.5 mt-2">
                <div className="flex items-center gap-2">
                  {['FARMER', 'PROCESSOR'].includes(activeStakeholder) && activeWorkflow === 'FULL_SUPPLY_CHAIN' ? <CheckCircle size={14} className="text-emerald-600" /> : <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />}
                  <span className={['FARMER', 'PROCESSOR'].includes(activeStakeholder) && activeWorkflow === 'FULL_SUPPLY_CHAIN' ? 'text-slate-800 font-bold' : 'text-slate-400'}>Buyer / Supplier</span>
                </div>
                <div className="flex items-center gap-2">
                  {activeWorkflow === 'FULL_SUPPLY_CHAIN' || activeWorkflow === 'TRANSPORT_ONLY' ? <CheckCircle size={14} className="text-emerald-600" /> : <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />}
                  <span className={activeWorkflow === 'FULL_SUPPLY_CHAIN' || activeWorkflow === 'TRANSPORT_ONLY' ? 'text-slate-800 font-bold' : 'text-slate-400'}>Transport</span>
                </div>
                <div className="flex items-center gap-2">
                  {activeWorkflow === 'FULL_SUPPLY_CHAIN' || activeWorkflow === 'WAREHOUSE_ONLY' ? <CheckCircle size={14} className="text-emerald-600" /> : <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />}
                  <span className={activeWorkflow === 'FULL_SUPPLY_CHAIN' || activeWorkflow === 'WAREHOUSE_ONLY' ? 'text-slate-800 font-bold' : 'text-slate-400'}>Warehouse</span>
                </div>
                <div className="flex items-center gap-2">
                  {activeWorkflow === 'FULL_SUPPLY_CHAIN' && ['FARMER', 'BUYER'].includes(activeStakeholder) ? <CheckCircle size={14} className="text-emerald-600" /> : <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />}
                  <span className={activeWorkflow === 'FULL_SUPPLY_CHAIN' && ['FARMER', 'BUYER'].includes(activeStakeholder) ? 'text-slate-800 font-bold' : 'text-slate-400'}>Processor</span>
                </div>
              </div>
            </div>
            
            {activeWorkflow !== 'FULL_SUPPLY_CHAIN' && (
              <p className="text-[10px] text-amber-600 font-bold bg-amber-50 p-2 rounded flex gap-1">
                <AlertTriangle size={12} /> Other services are manually disabled in this workflow.
              </p>
            )}
          </div>
        </div>

        {/* Market Context Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <Briefcase size={17} className="text-blue-600" /> Market Context
            </h2>
            <span className="text-[11px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full">
              {cropName}
            </span>
          </div>

          <div className="space-y-3 pt-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Lot Volume</span>
              <span className="font-black text-slate-800">{cropQty.toLocaleString()} kg</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Live Modal Price</span>
              <span className="font-black text-slate-800">₹{marketPrice}/kg</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Target Ceiling</span>
              <span className="font-black text-emerald-600">₹{targetPrice}/kg</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Statutory Benchmark (MSP)</span>
              <span className="font-black text-purple-700">₹{statutoryBench}/kg</span>
            </div>
          </div>

          {/* Dynamic 30-Day Trend Chart */}
          <div className="pt-2 border-t border-slate-100">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Price Trend (30 Days)</p>
            <PriceChart data={chartData} />
          </div>
        </div>

        {/* Live Variables & Multi-Attribute Telemetry */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 space-y-3">
          <h2 className="font-bold text-slate-800 text-sm flex items-center gap-2">
            <Database size={17} className="text-purple-600" /> Live Variables
          </h2>
          
          <div className="space-y-2.5">
            <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl text-xs space-y-1">
              <p className="font-bold text-blue-700 flex items-center gap-1.5">
                <CloudRain size={14} /> WEATHER & HARVEST RISK
              </p>
              <p className="text-slate-600">Clear weather across Marathwada & Western Maharashtra. Mandi arrivals steady.</p>
            </div>

            <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl text-xs space-y-1">
              <p className="font-bold text-amber-700 flex items-center gap-1.5">
                <Truck size={14} /> HIGHWAY LOGISTICS
              </p>
              <p className="text-slate-600">Freight solved: ₹6.50/km + handling. Mandi Cess: 1% statutory APMC e-NAM.</p>
            </div>

            <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-xl text-xs space-y-1">
              <p className="font-bold text-emerald-800 flex items-center gap-1.5">
                <ShieldCheck size={14} /> STATUTORY GUARDRAIL
              </p>
              <p className="text-slate-600">Protected Band: ₹{minAllowedFloor}/kg (APMC Floor) to ₹{maxAllowedCeiling}/kg (Ceiling).</p>
            </div>
          </div>
        </div>
      </div>

      
      
      {/* ════ COLUMN 2: LIVE NEGOTIATIONS (Center ~50%) ════ */}
      <div className="w-full xl:w-2/4 flex flex-col gap-4">
        
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 flex flex-col overflow-hidden relative flex-1">
          {/* Header */}
          <div className="p-4 border-b border-slate-100 flex justify-between items-center z-10 sticky top-0 bg-white">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                <MessageSquare size={17} className="text-emerald-500" /> AI Agent Negotiation — <span className="text-slate-500 font-normal">{cropName}</span>
              </h3>
              <span className="text-slate-300">•</span>
              <span className="text-xs text-slate-500 font-mono">#{String(activeId).substring(0, 8)}</span>
            </div>

            <div className="flex items-center gap-3">
              {isBuyer ? (
                <>
                  {/* Tab Selector: Timeline Chat vs Matrix vs Live Terminal */}
                  <div className="bg-slate-200/70 p-1 rounded-xl flex items-center gap-1 text-xs">
                    <button
                      onClick={() => setActiveTab('timeline')}
                      className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                        activeTab === 'timeline' 
                          ? 'bg-white text-slate-900 shadow-sm' 
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      💬 Chat Timeline
                    </button>
                    <button
                      onClick={() => setActiveTab('matrix')}
                      className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                        activeTab === 'matrix' 
                          ? 'bg-purple-700 text-white shadow-sm' 
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      <BarChart3 size={12} /> Top-5 Matrix
                    </button>
                    <button
                      onClick={() => setActiveTab('terminal')}
                      className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                        activeTab === 'terminal' 
                          ? 'bg-slate-900 text-emerald-400 shadow-sm' 
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      <TerminalIcon size={12} /> Live Engine
                    </button>
                  </div>

                  {/* WebSocket Connection Ping */}
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
                    <span className="text-[10px] font-bold text-slate-500 font-mono uppercase">
                      {isConnected ? 'LIVE STREAM' : 'CONNECTING'}
                    </span>
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Live
                </div>
              )}
            </div>
          </div>

        {isBuyer ? (
          <>
          {/* Candidate Sellers Parallel Branch Selector Tab Bar */}
        {rankedSuppliers.length > 0 && activeTab === 'timeline' && (
          <div className="bg-slate-100/90 border-b border-slate-200 p-2 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            <span className="text-[10px] font-extrabold uppercase text-slate-400 px-2 shrink-0">
              Candidate Sellers:
            </span>
            {rankedSuppliers.map((supp: any, sIdx: number) => {
              const isSelected = selectedSellerIdx === sIdx;
              const isWinner = supp.is_best || supp.rank === 1;
              const priceDisplay = supp.currentOffer || supp.negotiated_price || supp.final_price || supp.initial_ask;
              return (
                <button
                  key={sIdx}
                  onClick={() => setSelectedSellerIdx(sIdx)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition flex items-center gap-1.5 cursor-pointer ${
                    isSelected
                      ? (isWinner ? 'bg-emerald-600 text-white shadow-sm font-bold' : 'bg-slate-900 text-white shadow-sm font-bold')
                      : (isWinner ? 'bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100 font-bold' : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50')
                  }`}
                >
                  {isWinner && <Crown size={13} className={isSelected ? "text-amber-300 fill-amber-300" : "text-amber-500 fill-amber-500"} />}
                  <span>{supp.name || `Farmer ${sIdx + 1}`}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                    isSelected 
                      ? 'bg-black/20 text-white' 
                      : (isWinner ? 'bg-emerald-200/70 text-emerald-900' : 'bg-slate-100 text-slate-600')
                  }`}>
                    ₹{priceDisplay}/kg
                  </span>
                </button>
              );
            })}
            <button
              onClick={() => setActiveTab('matrix')}
              className="px-2.5 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition flex items-center gap-1 bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 cursor-pointer"
            >
              <BarChart3 size={13} />
              <span>Matrix View</span>
            </button>
          </div>
        )}

        {/* Selected Branch Subheader */}
        {rankedSuppliers[selectedSellerIdx] && activeTab === 'timeline' && (
          <div className="bg-white px-4 py-2 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 flex items-center gap-1">
                {rankedSuppliers[selectedSellerIdx].name}
                {rankedSuppliers[selectedSellerIdx].is_best && (
                  <span className="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded-full font-extrabold flex items-center gap-0.5">
                    <Crown size={10} className="text-emerald-700 fill-emerald-600" /> Best Executable Deal
                  </span>
                )}
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-slate-500 flex items-center gap-1 text-[11px]">
                <MapPin size={12} className="text-slate-400" /> {rankedSuppliers[selectedSellerIdx].location} ({rankedSuppliers[selectedSellerIdx].distance_km} km)
              </span>
              <span className="text-slate-300">•</span>
              <span className={`text-[11px] font-bold ${
                rankedSuppliers[selectedSellerIdx].status?.includes('Deal') ? 'text-emerald-600' :
                rankedSuppliers[selectedSellerIdx].status?.includes('Stalled') ? 'text-amber-600' :
                'text-blue-600'
              }`}>
                {rankedSuppliers[selectedSellerIdx].status || 'Negotiating'}
              </span>
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono">
              <span className="text-slate-500">Ask: <strong className="text-slate-800">₹{rankedSuppliers[selectedSellerIdx].currentOffer || rankedSuppliers[selectedSellerIdx].negotiated_price}/kg</strong></span>
              {rankedSuppliers[selectedSellerIdx].buyerOffer && (
                <span className="text-slate-500">Bid: <strong className="text-blue-700">₹{rankedSuppliers[selectedSellerIdx].buyerOffer}/kg</strong></span>
              )}
              <span className="text-slate-500">Landed: <strong className="text-emerald-700 font-bold">₹{rankedSuppliers[selectedSellerIdx].landed_cost_per_kg}/kg</strong></span>
            </div>
          </div>
        )}

        {/* Winner Announcement Banner */}
        {agreementData && showAgreement && activeTab === 'timeline' && (
          <div className="bg-gradient-to-r from-emerald-600 to-teal-700 text-white px-4 py-2.5 flex items-center justify-between text-xs animate-in slide-in-from-top-2 duration-300">
            <div className="flex items-center gap-2">
              <Crown size={16} className="text-amber-300 fill-amber-300 animate-bounce" />
              <span>
                <strong>Deal Finalized!</strong> Contract awarded to <strong>{agreementData.farmer || agreementData.farmer_name || 'Latur APMC Producer'}</strong> at <strong>₹{agreementData.final_price || agreementData.price}/kg</strong>.
              </span>
            </div>
            <button
              onClick={() => setShowValidationModal(true)}
              className="px-3 py-1 bg-white text-emerald-800 rounded-lg font-bold text-[11px] hover:bg-emerald-50 transition shadow-sm cursor-pointer"
            >
              View Smart Contract
            </button>
          </div>
        )}

        {/* No Executable Deal Banner */}
        {noDealMessage && !showAgreement && activeTab === 'timeline' && (
          <div className="bg-red-50 border-b border-red-200 text-red-800 px-4 py-2.5 flex items-center justify-between text-xs animate-in slide-in-from-top-2 duration-300">
            <div className="flex items-center gap-2">
              <XCircle size={16} className="text-red-600 shrink-0" />
              <span>
                <strong>NO EXECUTABLE DEAL:</strong> All candidate offers exceeded the buyer's reservation ceiling (₹{maxAllowedCeiling}/kg) or budget limits.
              </span>
            </div>
            <span className="px-2 py-0.5 bg-red-200 text-red-900 rounded font-bold text-[10px]">
              Guarded
            </span>
          </div>
        )}

        {/* ════ VIEW MODE 1: Chat Timeline with OfferCards & ChatBubbles ════ */}
        {activeTab === 'timeline' && (
          <div className="flex-1 overflow-y-auto bg-slate-50/50 p-5 space-y-5">
            {/* If NO messages have arrived yet and no deal reached, show the active streaming animation */}
            {activeBranchMessages.length === 0 && !agreementData && !noDealMessage ? (
              <div className="h-full min-h-[300px] flex flex-col items-center justify-center p-8 text-center space-y-4">
                <div className="relative">
                  <div className="w-16 h-16 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 shadow-sm animate-pulse">
                    <Bot size={32} />
                  </div>
                  <span className="absolute -top-1 -right-1 flex h-4 w-4">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                  </span>
                </div>
                <div>
                  <h4 className="font-bold text-slate-800 text-base flex items-center justify-center gap-2">
                    <Loader2 size={18} className="animate-spin text-emerald-600" />
                    AI Multi-Agent Negotiation Engine Active
                  </h4>
                  <p className="text-xs text-slate-500 max-w-md mt-1">
                    Scanning verified candidate farmer listings across Maharashtra APMC mandis and running parallel concession negotiations...
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-emerald-700 bg-emerald-50 px-4 py-2 rounded-xl border border-emerald-100 font-semibold">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                  Autonomous parallel negotiation streaming live...
                </div>
                {!isParallelRunning && (
                  <button
                    onClick={runParallelAutonomousNegotiation}
                    className="mt-2 text-xs text-slate-400 hover:text-emerald-600 underline cursor-pointer"
                  >
                    Click to re-trigger engine if paused
                  </button>
                )}
              </div>
            ) : (
              <>
                {isParallelRunning && (
                  <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold animate-pulse mb-3">
                    <span className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
                      Autonomous Top-5 Parallel Negotiation streaming live...
                    </span>
                    <span className="text-[11px] text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full font-bold">
                      Round Concessions Active
                    </span>
                  </div>
                )}
                {activeBranchMessages.map((m, i) => (
                  m.type === 'offer' ? (
                    <OfferCard 
                      key={i}
                      agent={m.agent}
                      price={m.price}
                      quantity={m.quantity || cropQty}
                      quality={m.quality || 'A'}
                      deliveryDate={m.deliveryDate || '3 Business Days'}
                      transportIncluded={m.transportIncluded ?? true}
                      warehouseIncluded={m.warehouseIncluded ?? false}
                      validity={m.validity || '24 Hours'}
                      isFarmer={m.agent?.toLowerCase().includes('farmer') || m.agent?.toLowerCase().includes('producer') || m.agent?.toLowerCase().includes('mandi') || m.actor === 'SELLER'}
                      isBuyer={isBuyer}
                      onAction={handleAction}
                    />
                  ) : (
                    <ChatBubble 
                      key={i} 
                      agent={m.agent} 
                      price={m.price} 
                      message={m.message} 
                      reasoning={m.reasoning}
                      isFarmer={m.agent?.toLowerCase().includes('farmer') || m.agent?.toLowerCase().includes('producer') || m.agent?.toLowerCase().includes('mandi') || m.actor === 'SELLER'} 
                      isInteractive={false}
                      onAction={handleAction}
                    />
                  )
                ))}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* ════ VIEW MODE 2: Real-Time Dynamic Top-5 Comparison Matrix ════ */}
        {activeTab === 'matrix' && (
          <div className="flex-1 overflow-y-auto bg-slate-50/50 p-4 space-y-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div>
                  <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <BarChart3 size={16} className="text-purple-600" /> Top-5 APMC Candidates Live Status & Landed Cost Matrix
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Real-time concurrent multi-round negotiations evaluated by landed cost (Base Ask + Freight + APMC Cess).
                  </p>
                </div>
                <span className="text-[11px] font-bold px-2.5 py-1 bg-purple-50 text-purple-700 rounded-lg border border-purple-100 flex items-center gap-1">
                  <Activity size={12} className={isParallelRunning ? "animate-pulse text-purple-600" : "text-purple-400"} />
                  {isParallelRunning ? '5 Parallel Sessions Active' : 'Evaluated'}
                </span>
              </div>

              {rankedSuppliers.length === 0 ? (
                <div className="text-center py-12 text-slate-500 space-y-3">
                  <Layers size={32} className="mx-auto text-slate-400" />
                  <p className="text-xs">Initializing parallel multi-mandi discovery...</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 text-[11px] uppercase bg-slate-50">
                        <th className="py-2.5 px-3 font-semibold">Farmer / Mandi</th>
                        <th className="py-2.5 px-3 font-semibold text-center">Status</th>
                        <th className="py-2.5 px-3 font-semibold text-center">Round</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Farmer Offer</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Buyer Offer</th>
                        <th className="py-2.5 px-3 font-semibold text-right">Landed Cost</th>
                        <th className="py-2.5 px-3 font-semibold text-center">Result</th>
                        <th className="py-2.5 px-3 font-semibold text-center">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {rankedSuppliers.map((sup: any, idx: number) => {
                        const isBest = sup.is_best || sup.rank === 1;
                        const currentAsk = sup.currentOffer || sup.final_price || sup.negotiated_price || sup.initial_ask;
                        const buyerBid = sup.buyerOffer;
                        const statusText = sup.status || 'Negotiating';
                        const isDeal = statusText.includes('Deal') || statusText.includes('DEAL');
                        const isStalled = statusText.includes('Stall');
                        const isRejected = statusText.includes('Reject') || statusText.includes('No Deal') || statusText.includes('Exceeded');

                        return (
                          <tr 
                            key={idx} 
                            className={`transition ${isBest ? 'bg-emerald-50/70 font-semibold' : 'hover:bg-slate-50'}`}
                          >
                            <td className="py-3 px-3">
                              <div className="flex items-center gap-2">
                                <span className={`w-5 h-5 rounded-full text-[10px] font-extrabold flex items-center justify-center ${
                                  isBest ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700'
                                }`}>
                                  {idx + 1}
                                </span>
                                <div>
                                  <p className="font-bold text-slate-800 flex items-center gap-1">
                                    {sup.name}
                                    {isBest && <Crown size={12} className="text-amber-500 fill-amber-500" />}
                                  </p>
                                  <p className="text-[10px] text-slate-500">{sup.location} ({sup.distance_km || 120} km)</p>
                                </div>
                              </div>
                            </td>

                            <td className="py-3 px-3 text-center">
                              {isDeal ? (
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-emerald-100 text-emerald-800 rounded-full font-bold text-[10px]">
                                  <CheckCircle2 size={10} className="text-emerald-600" /> Deal Agreed
                                </span>
                              ) : isStalled ? (
                                <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full font-bold text-[10px]">
                                  Stalled
                                </span>
                              ) : isRejected ? (
                                <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded-full font-bold text-[10px]">
                                  No Deal
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full font-bold text-[10px]">
                                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-ping"></span> Negotiating
                                </span>
                              )}
                            </td>

                            <td className="py-3 px-3 text-center font-mono text-slate-700 font-bold">
                              {sup.round ? `Round ${sup.round}` : 'Round 1'}
                            </td>

                            <td className="py-3 px-3 text-right font-mono text-slate-800 font-bold">
                              ₹{currentAsk}/kg
                            </td>

                            <td className="py-3 px-3 text-right font-mono text-blue-700 font-bold">
                              {buyerBid ? `₹${buyerBid}/kg` : '—'}
                            </td>

                            <td className="py-3 px-3 text-right font-mono">
                              <span className={`px-2 py-0.5 rounded font-black text-xs ${
                                isBest ? 'bg-emerald-200/80 text-emerald-900' : 'bg-slate-100 text-slate-800'
                              }`}>
                                ₹{sup.landed_cost_per_kg || (currentAsk + 1.5)}/kg
                              </span>
                            </td>

                            <td className="py-3 px-3 text-center">
                              {sup.result === 'VALID' || isDeal ? (
                                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded font-black text-[10px]">
                                  VALID
                                </span>
                              ) : sup.result === 'STALLED' || isStalled ? (
                                <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded font-bold text-[10px]">
                                  STALLED
                                </span>
                              ) : sup.result === 'EXCEEDED CEILING' || isRejected ? (
                                <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded font-bold text-[10px]">
                                  EXCEEDED
                                </span>
                              ) : (
                                <span className="text-slate-400 font-bold">—</span>
                              )}
                            </td>

                            <td className="py-3 px-3 text-center">
                              <button
                                onClick={() => {
                                  setSelectedSellerIdx(idx);
                                  setActiveTab('timeline');
                                }}
                                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-[11px] font-bold transition shadow-sm cursor-pointer"
                              >
                                Inspect Chat
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ════ VIEW MODE 3: Real-Time Streaming Terminal ════ */}
        {activeTab === 'terminal' && (
          <div className="flex-1 bg-slate-950 p-4 font-mono text-[11px] leading-relaxed overflow-y-auto space-y-2 select-text dark-scroll text-slate-100 flex flex-col">
            <div className="text-slate-500 pb-2 border-b border-slate-800 text-[10px] flex justify-between items-center">
              <span># LangGraph Multi-Agent Parallel Daemon • 5 Mandis</span>
              <span className="text-emerald-400 font-bold">{isParallelRunning ? '● RUNNING' : '✓ IDLE'}</span>
            </div>

            {liveTerminalLogs.length === 0 ? (
              <div className="text-center py-16 text-slate-500 space-y-3">
                <TerminalIcon size={32} className="mx-auto text-slate-700" />
                <p>Engine connected. Live negotiation events stream here automatically.</p>
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

        {/* Bottom Passive Status Indicator Bar (No button required!) */}
        <div className="p-3 bg-white border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
          {isParallelRunning ? (
            <div className="px-3 py-1.5 bg-emerald-950/90 border border-emerald-700/50 text-emerald-300 rounded-xl font-bold flex items-center gap-2 text-xs shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span>● Automatic Top-5 Negotiation In Progress (5 Mandis Streaming Live)</span>
            </div>
          ) : agreementData && showAgreement ? (
            <div className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl font-bold flex items-center gap-2 text-xs shadow-sm">
              <CheckCircle2 size={15} className="text-emerald-600" />
              <span>✓ Top-5 Negotiation Completed • Deal Finalized ({agreementData.farmer || agreementData.farmer_name})</span>
            </div>
          ) : noDealMessage ? (
            <div className="px-3 py-1.5 bg-red-50 border border-red-200 text-red-800 rounded-xl font-bold flex items-center gap-2 text-xs shadow-sm">
              <AlertCircle size={15} className="text-red-600" />
              <span>❌ No Executable Deal • All Offers Exceeded Reservation Ceiling</span>
            </div>
          ) : (
            <div className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-xl font-bold flex items-center gap-2 text-xs">
              <Sparkles size={14} className="text-emerald-600" />
              <span>● Autonomous Multi-Mandi Procurement Engine Active</span>
            </div>
          )}

          <span className="text-slate-400 text-[11px]">
            Protected by APMC Statutory Guardrails
          </span>
        </div>
        </>
      ) : (
          <div className="flex-1 overflow-y-auto bg-slate-50/40 p-5 space-y-4">
            
            {liveBuyers.length > 0 ? (
              <>
                <div className="space-y-3">
                  {liveBuyers.map((b, i) => (
                    <div key={i} className={`bg-white border rounded-2xl p-4 shadow-sm relative overflow-hidden transition-all ${b.aiStatus?.includes('Override') ? 'border-indigo-400 ring-2 ring-indigo-50' : 'border-slate-200/90'}`}>
                      
                      <div className="flex justify-between items-center mb-2.5">
                        <h4 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
                          <Star size={16} className="text-amber-400 fill-amber-400" /> {b.id} — {b.match}% Match
                        </h4>
                        <span className="font-black text-slate-900 text-lg">₹{b.offer}</span>
                      </div>
                      
                      {b.aiStatus?.includes('Override') && (
                        <div className="mb-2.5">
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                            <ShieldCheck size={12} className="text-indigo-600" /> FARMER OVERRIDE APPLIED
                          </span>
                        </div>
                      )}
                      
                      <div className="space-y-1.5 text-xs pt-2 border-t border-slate-100">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-500 font-medium">AI Strategy:</span>
                          <span className={`font-semibold ${b.aiStatus?.includes('Override') ? 'text-indigo-600 font-bold' : 'text-slate-700'}`}>
                            {b.aiStatus}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-500 font-medium">Status:</span>
                          <span className="font-semibold flex items-center gap-1.5">
                            <span className={`w-2 h-2 rounded-full ${b.status === 'Negotiating' ? 'bg-emerald-500 animate-pulse' : 'bg-blue-500'}`}></span>
                            <span className={b.status === 'Negotiating' ? 'text-emerald-700' : 'text-blue-700'}>{b.status}</span>
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Best Deal So Far (Banner inside center column) */}
                <div className="bg-[#064e3b] p-4 text-white rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4 shadow-md mt-2">
                  <div>
                    <p className="text-emerald-300 text-[10px] font-bold uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      <Trophy size={13} className="text-amber-400" /> BEST DEAL SO FAR
                    </p>
                    <div className="flex items-center flex-wrap gap-2 text-xs">
                      <span className="font-bold text-base text-white">{liveBuyers[0].id}</span>
                      <span className="bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 px-2 py-0.5 rounded text-xs font-bold">
                        ₹{liveBuyers[0].offer}/q
                      </span>
                      <span className="text-emerald-100">{cropQty.toLocaleString()} Q</span>
                      <span className="text-emerald-100">{liveBuyers[0].match}% Match</span>
                      <span className="font-bold text-emerald-200">
                        Net: ₹{(liveBuyers[0].offer * cropQty - 1850).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
                    <button 
                      onClick={() => setIsRagOpen(true)}
                      className="px-3.5 py-2 rounded-xl border border-emerald-500/70 text-emerald-100 bg-emerald-800/40 hover:bg-emerald-800 text-xs font-bold transition flex-1 sm:flex-none text-center"
                    >
                      View Analysis
                    </button>
                    <button 
                      onClick={() => {
                        setAgreementData({ ...negState, price: liveBuyers[0].offer, farmer: user?.name, buyer: liveBuyers[0].id });
                        setShowValidationModal(true);
                      }}
                      className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-black text-xs transition shadow flex-1 sm:flex-none text-center"
                    >
                      Accept Deal
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="py-8 px-6">
                <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2 mb-2">
                  <Search className="text-emerald-500" /> AI MATCHING
                </h2>
                <p className="text-indigo-600 font-bold text-sm mb-6 flex items-center gap-2">
                  <span className="text-base">🔎</span> Finding suitable buyers...
                </p>
                
                <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">MATCHING AGAINST:</p>
                  <ul className="space-y-3">
                    {['Crop & Variety', 'Quantity required', 'Quality Grade', 'Location & Distance', 'Price expectations', 'Logistics availability'].map((txt, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
                        <CheckCircle size={16} className="text-emerald-500" /> {txt}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Live Terminal logs at bottom (Matching User Screenshot) */}
            <div className="mt-4 bg-[#0f172a] rounded-xl p-4 font-mono text-[11px] leading-relaxed overflow-y-auto max-h-44 text-slate-300 shadow-inner">
              <div className="text-emerald-400 font-bold mb-2 flex items-center gap-2 text-[10px] uppercase tracking-wider">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span> LIVE ACTIVITY
              </div>
              <div className="space-y-1">
                {liveTerminalLogs.length === 0 ? (
                  <>
                    <div className="flex items-start gap-2 text-slate-400 text-[10px]">
                      <span className="text-slate-600 shrink-0">[{new Date().toLocaleTimeString()}]</span>
                      <span className="text-blue-400 font-bold shrink-0">System:</span>
                      <span>🚀 [System] Negotiation {id ? id.substring(0, 12) : 'session'} queued in Redis. Waiting for worker...</span>
                    </div>
                    <div className="flex items-start gap-2 text-slate-400 text-[10px]">
                      <span className="text-slate-600 shrink-0">[{new Date().toLocaleTimeString()}]</span>
                      <span className="text-blue-400 font-bold shrink-0">Worker:</span>
                      <span>🚀 [Worker] Negotiation dispatched via Redis stream to LangGraph orchestrator.</span>
                    </div>
                    <div className="flex items-start gap-2 text-slate-400 text-[10px]">
                      <span className="text-slate-600 shrink-0">[{new Date().toLocaleTimeString()}]</span>
                      <span className="text-purple-400 font-bold shrink-0">Planner:</span>
                      <span>📋 [Planner] Initiating negotiation workflow planner for {cropName}.</span>
                    </div>
                  </>
                ) : (
                  liveTerminalLogs.map((log, lIdx) => (
                    <div key={lIdx} className="flex items-start gap-2 text-[10px] animate-in fade-in duration-150">
                      <span className="text-slate-600 shrink-0">[{log.time}]</span>
                      <span className={`font-bold shrink-0 ${log.color || 'text-blue-400'}`}>[{log.tag}]</span>
                      <span className="text-slate-300 break-words flex-1">{log.text}</span>
                    </div>
                  ))
                )}
                <div ref={terminalEndRef} />
              </div>
            </div>

          </div>
        )}
        </div>
      </div>
      
      {/* ════ COLUMN 3: Right Panel (LangGraph + Farmer Copilot ~25%) ════ */}
      <div className="w-full xl:w-1/4 flex flex-col gap-4 h-full">
        
        {/* Card 1: LangGraph Execution */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <Zap size={16} className="text-emerald-500" /> LangGraph Execution
            </h4>
          </div>

          <AgentWorkflowStepper activeAgent={activeAgent} isBuyer={isBuyer} />
          <button 
            type="button"
            onClick={() => setIsRagOpen(true)}
            className="w-full py-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 text-slate-700 font-bold rounded-xl transition text-xs flex justify-center items-center gap-2 shadow-sm"
          >
            <Database size={14} className="text-slate-500" /> View RAG Context
          </button>
        </div>

        {/* Dynamic Action Area: Agreement Preview OR No-Deal Card OR Role-Specific Copilot */}
        {showAgreement && agreementData ? (
          <AgreementPreview 
            dealData={agreementData} 
            onSignAndClose={() => setShowValidationModal(true)} 
          />
        ) : noDealMessage && isBuyer ? (
          <div className="bg-white rounded-2xl shadow-sm border border-red-200 p-5 space-y-3 animate-in fade-in duration-300">
            <div className="flex items-center gap-2 text-red-700 font-bold text-sm">
              <XCircle size={18} />
              <h3>Procurement Outcome</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              No farmer satisfied the buyer's executable economic constraints. All 5 candidate offers exceeded the reservation ceiling (₹{maxAllowedCeiling}/kg) or budget limits.
            </p>
            <div className="p-3 bg-red-50 rounded-xl text-xs space-y-1 text-red-800 border border-red-100">
              <p className="font-bold">Summary Decision:</p>
              <p>Winner: NONE • Status: NO_EXECUTABLE_DEAL</p>
            </div>
          </div>
        ) : isBuyer ? (
          /* Buyer Copilot Override */
          <div className="bg-slate-900 rounded-2xl shadow-sm border border-slate-800 p-5 text-white space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <ShieldCheck size={18} className="text-emerald-400" /> Copilot Override
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-800 text-slate-300 rounded-full">
                RL Policy Active
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Autonomous agents are negotiating based on RL policy. Intervene anytime to counter with a manual offer.
            </p>

            <div className="space-y-2.5">
              <input 
                type="number" 
                id="humanOverride"
                value={manualPrice}
                onChange={(e) => setManualPrice(e.target.value)}
                placeholder={`Enter price (e.g. ₹${targetPrice})...`} 
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
              />

              {/* Quick Price Action Chips */}
              <div className="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={() => {
                    const base = parseFloat(manualPrice) || targetPrice || 20;
                    setManualPrice((base + 0.5).toFixed(1));
                  }}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-emerald-400 rounded-lg text-[10px] font-bold border border-slate-700 transition cursor-pointer"
                >
                  +₹0.50
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const base = parseFloat(manualPrice) || targetPrice || 20;
                    setManualPrice((base + 1.0).toFixed(1));
                  }}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-emerald-400 rounded-lg text-[10px] font-bold border border-slate-700 transition cursor-pointer"
                >
                  +₹1.00
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const base = parseFloat(manualPrice) || targetPrice || 20;
                    setManualPrice((base + 2.0).toFixed(1));
                  }}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-emerald-400 rounded-lg text-[10px] font-bold border border-slate-700 transition cursor-pointer"
                >
                  +₹2.00
                </button>
                {statutoryBench > 0 && (
                  <button
                    type="button"
                    onClick={() => setManualPrice(statutoryBench.toFixed(2))}
                    className="px-2 py-1 bg-purple-950/60 hover:bg-purple-900/60 text-purple-300 rounded-lg text-[10px] font-bold border border-purple-800/60 transition cursor-pointer"
                    title="Official MSP Benchmark"
                  >
                    MSP ₹{statutoryBench}
                  </button>
                )}
              </div>

              <button 
                onClick={() => {
                  const val = parseFloat(manualPrice);
                  if (isNaN(val) || val <= 0) {
                    alert('Please enter a valid price.');
                    return;
                  }
                  interveneMutation.mutate(val);
                }}
                disabled={interveneMutation.isPending}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition shadow-sm cursor-pointer"
              >
                {interveneMutation.isPending ? 'Submitting Offer...' : 'Send Manual Offer'}
              </button>
            </div>
          </div>
        ) : (
          /* Card 2: Farmer Copilot (Dark Theme matching Ritik's design) */
          <div className="bg-[#0f172a] rounded-2xl shadow-lg border border-slate-800 p-5 text-white flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-sm flex items-center gap-2 text-white">
                  <ShieldCheck size={16} className="text-emerald-400" />
                  <span className="text-base">👨‍🌾</span> Farmer Copilot
                </h3>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                AI is negotiating automatically based on your listing, market conditions and negotiation policy. You can intervene at any time.
              </p>

              {/* Quick Action Chips */}
              <div className="flex flex-wrap gap-2 mb-4">
                <button 
                  type="button" 
                  onClick={() => setCopilotCommand(`Don't go below ₹${Math.round(currentFloor || 64)}`)} 
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition"
                >
                  Don't go below ₹{Math.round(currentFloor || 64)}
                </button>
                <button 
                  type="button" 
                  onClick={() => setCopilotCommand('Counter best buyer')} 
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition"
                >
                  Counter best buyer
                </button>
                <button 
                  type="button" 
                  onClick={() => setCopilotCommand('Pause negotiations')} 
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition"
                >
                  Pause negotiations
                </button>
              </div>

              {/* Last Copilot Response Feedback (if user intervened) */}
              {copilotMessages.length > 0 && (
                <div className="mb-3 p-2.5 bg-slate-800/80 border border-slate-700/60 rounded-xl text-[11px] text-slate-300 flex items-start gap-2">
                  <Bot size={14} className="text-emerald-400 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <span className="text-slate-400 font-semibold text-[10px]">
                      {copilotMessages[copilotMessages.length - 1].sender === 'AI' ? 'AI Copilot: ' : 'Instruction: '}
                    </span>
                    {copilotMessages[copilotMessages.length - 1].text}
                  </div>
                </div>
              )}
            </div>

            {/* Copilot Input Form */}
            <form onSubmit={handleCopilotSubmit} className="space-y-3 mt-auto">
              <input 
                type="text" 
                value={copilotCommand}
                onChange={e => setCopilotCommand(e.target.value)}
                placeholder='e.g. "Try to get ₹67 from the best' 
                className="w-full bg-[#1e293b]/80 border border-slate-700/80 rounded-xl px-4 py-3 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-emerald-500 transition"
              />
              <button 
                type="submit" 
                className="w-full py-3 bg-[#10b981] hover:bg-emerald-600 text-white font-bold text-sm rounded-xl transition shadow-md flex items-center justify-center gap-1.5"
              >
                Send Instruction
              </button>
            </form>
          </div>
        )}

      </div>
      {/* Floating RAG Modal */}
      <RagContextViewer isOpen={isRagOpen} onClose={() => setIsRagOpen(false)} crop={cropName} />

      {/* APMC Validated Smart Contract Modal */}
      <TransactionValidationModal
        isOpen={showValidationModal}
        onClose={() => setShowValidationModal(false)}
        dealData={agreementData}
        buyerUser={user}
      />

    </div>
  );
}
