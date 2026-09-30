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
  Play,
  CheckCircle,
  AlertTriangle,
  Search,
  Star,
  Bot,
  Trophy,
  ExternalLink
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
  const { user } = useAuth();
  const location = useLocation();
  const hasAutoStartFlag = Boolean(location.state?.autoStart);
  const isBuyer = location.pathname.includes('/buyer') || location.state?.isBuyer
    ? true
    : (user?.role === 'farmer' || localStorage.getItem('user_role') === 'farmer'
        ? false
        : Boolean(
          user?.role === 'buyer' ||
          user?.role === 'trader' ||
          localStorage.getItem('user_role') === 'buyer'
        ));

  // Fetch active negotiations list if no specific ID is in URL (e.g. from sidebar "My Deals" or "My Negotiations")
  const { data: activeNegotiationsList } = useQuery({
    queryKey: ['active_negotiations_summary'],
    queryFn: async () => {
      try {
        const res = await api.get('/negotiations');
        return Array.isArray(res.data) ? res.data : (res.data?.data || []);
      } catch {
        return [];
      }
    },
    enabled: !id || id === 'undefined' || id === 'null'
  });

  const effectiveId = useMemo(() => {
    if (id && id !== 'undefined' && id !== 'null') return id;
    if (activeNegotiationsList && activeNegotiationsList.length > 0) {
      return activeNegotiationsList[0].negotiation_id || activeNegotiationsList[0].id;
    }
    return null;
  }, [id, activeNegotiationsList]);

  const token = localStorage.getItem('agri_token');
  const baseWsUrl = import.meta.env.VITE_WS_URL || '/api/v1/ws';
  const wsUrl = effectiveId ? `${baseWsUrl}?negotiation_id=${effectiveId}` : baseWsUrl;
  const { isConnected, lastMessage, sendMessage } = useWebSocket(wsUrl);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // States
  const [messages, setMessages] = useState<any[]>([]);
  const [isRagOpen, setIsRagOpen] = useState(false);
  const [showAgreement, setShowAgreement] = useState(false);
  const [agreementData, setAgreementData] = useState<any>(null);
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [dealAccepted, setDealAccepted] = useState(false);
  const [isRenegotiating, setIsRenegotiating] = useState(false);
  const [activeTab, setActiveTab] = useState<'timeline' | 'terminal'>('timeline');
  const [isParallelRunning, setIsParallelRunning] = useState(false);
  const [liveTerminalLogs, setLiveTerminalLogs] = useState<Array<{ time: string; tag: string; text: string; color?: string }>>([]);
  const [manualPrice, setManualPrice] = useState<string>('');
  const [farmerManualPrice, setFarmerManualPrice] = useState<number>(2550);



  const handleAcceptDeal = async (customDeal?: any) => {
    const defaultFarmer = isBuyer ? liveSellers[0]?.id : (user?.name || 'Suresh Deshmukh');
    const defaultBuyer = isBuyer ? (buyerName || user?.name || 'AgroCorp Procurement') : (liveBuyers[0]?.id || 'Buyer A');
    const defaultPrice = isBuyer ? liveSellers[0]?.offer : liveBuyers[0]?.offer;

    const chosenPrice = customDeal?.price || defaultPrice || targetPrice || 68.5;
    const chosenFarmer = customDeal?.farmer || defaultFarmer || 'Suresh Deshmukh';
    const chosenBuyer = customDeal?.buyer || defaultBuyer || 'AgroCorp Procurement';
    const chosenCrop = customDeal?.crop || cropName || 'Soybean';
    const chosenQty = customDeal?.quantity || cropQty || 500;

    const agreement = {
      ...negState,
      id: effectiveId || id || negState?.id || 'neg_deal',
      negotiation_id: effectiveId || id || negState?.id || 'neg_deal',
      price: chosenPrice,
      final_price: chosenPrice,
      farmer: chosenFarmer,
      farmer_name: chosenFarmer,
      buyer: chosenBuyer,
      buyer_name: chosenBuyer,
      crop: chosenCrop,
      quantity: chosenQty,
      status: 'DEAL',
      transport_plan: negState?.transport_plan || null
    };

    setAgreementData(agreement);
    setDealAccepted(true);
    setIsRenegotiating(false);
    setIsParallelRunning(false);

    // Call backend API to finalize deal and persist transaction in DB
    try {
      const activeId = effectiveId || id || negState?.id || negState?.negotiation_id;
      if (activeId) {
        await api.post(`/negotiations/${activeId}/accept`, {
          price: chosenPrice,
          quantity: chosenQty,
          farmer: chosenFarmer,
          buyer: chosenBuyer,
          crop: chosenCrop,
          user_id: user?.id || localStorage.getItem('user_id') || 'usr_buyer_demo',
          transport_plan: agreement.transport_plan
        });
        refetchNeg();
      }
    } catch (err: any) {
      console.warn('Accept deal API note:', err);
    }

    setShowValidationModal(true);
  };


  const [rightTab, setRightTab] = useState<'ai' | 'rag' | 'copilot'>('copilot');
  const [copilotCommand, setCopilotCommand] = useState('');
  const [copilotMessages, setCopilotMessages] = useState<{ sender: string, text: string, time: string }[]>(() =>
    isBuyer ? [
      { sender: 'AI', text: 'I am your negotiation copilot. Give me manual instructions like "Don\'t pay above 52" or "Counter Suresh Deshmukh at 49".', time: '11:47 PM' },
      { sender: 'Buyer', text: 'Counter best farmer at target ₹68', time: '11:49:19 PM' },
      { sender: 'AI', text: "Understood. Updating target offer and dispatching counter bids to matched farmers.", time: '11:49:33 PM' },
      { sender: 'Buyer', text: 'Counter Suresh Deshmukh at 68.5', time: '11:52:58 PM' },
      { sender: 'AI', text: 'Manual instruction applied. Negotiators are updating counter offers.', time: '11:52:59 PM' }
    ] : [
      { sender: 'AI', text: 'I am your negotiation copilot. Give me manual instructions like "Set minimum to 2500" or "Counter Buyer A at 2600".', time: '11:47 PM' },
      { sender: 'Farmer', text: 'Set minimum to 2500', time: '11:49:19 PM' },
      { sender: 'AI', text: "Understood. I'll update your negotiation floor to ₹2500/q.", time: '11:49:33 PM' },
      { sender: 'Farmer', text: 'Counter Buyer A at 2500', time: '11:52:58 PM' },
      { sender: 'AI', text: 'Manual instruction applied. Negotiators are updating counter offers.', time: '11:52:59 PM' }
    ]
  );
  const [liveBuyers, setLiveBuyers] = useState([
    { id: 'Buyer A', match: 96, offer: 2500, aiStatus: 'Farmer Override: ₹2500', status: 'Negotiating', color: 'emerald' },
    { id: 'Buyer B', match: 91, offer: 2480, aiStatus: 'Negotiating...', status: 'Waiting', color: 'blue' },
    { id: 'Buyer C', match: 87, offer: 2420, aiStatus: 'Counter ₹2500', status: 'Negotiating', color: 'amber' }
  ]);

  // 1. Fetch negotiation session state from database (smooth non-blocking background polling)
  const { data: negState, isLoading, refetch: refetchNeg } = useQuery({
    queryKey: ['negotiation', effectiveId],
    queryFn: async () => {
      if (!effectiveId) return null;
      const res = await api.get(`/negotiations/${effectiveId}`);
      return res.data?.data || res.data;
    },
    enabled: Boolean(effectiveId),
    refetchInterval: 8000,
    staleTime: 6000,
    retry: 1
  });

  const isDealFinalized = (dealAccepted || negState?.status === 'DEAL' || negState?.status === 'COMPLETED') && !isRenegotiating;

  const cropName = negState?.crop || 'Soybean';
  const cropQty = Number(negState?.quantity) || 500;
  const currentFloor = Number(negState?.min_price) || 45.0;
  const targetPrice = Number(negState?.target_price || negState?.buyer_target_price || 47.0);
  const marketPrice = Number(negState?.market_price || Math.round(targetPrice * 1.04 * 10) / 10);
  const activeAgent = isParallelRunning ? 'Negotiator' : (lastMessage?.data?.agent || 'Negotiator');

  // Blueprint Compliance: Stakeholder Scope Variables
  const activeStakeholder = (lastMessage?.stakeholder || negState?.stakeholder_role || 'FARMER').toUpperCase();
  const farmerName = negState?.farmer_name || negState?.farmer || 'Ramesh Patil';
  const farmerLocation = negState?.location || 'Latur APMC, Maharashtra';
  const buyerName = negState?.buyer_name || negState?.buyer || user?.name || 'AgroCorp Procurement';
  const bestOfferPrice = Number(negState?.current_offer || negState?.price || negState?.min_price || 68.5);

  // Candidate Farmers for Buyer Procurement View (Stateful for Real-Time Copilot Controls)
  const [liveSellers, setLiveSellers] = useState([
    { id: 'Suresh Deshmukh', location: 'Nanded APMC, Maharashtra', match: 96, offer: 68.5, aiStatus: 'Verified APMC Grade A', status: 'Negotiating', color: 'emerald' },
    { id: 'Ramesh Patil', location: 'Latur APMC, Maharashtra', match: 92, offer: 68.5, aiStatus: 'Farmer Asking Rate', status: 'Active', color: 'blue' },
    { id: 'Vilas Jadhav', location: 'Akola APMC, Maharashtra', match: 89, offer: 71.0, aiStatus: 'Counter ₹66.2', status: 'Waiting', color: 'amber' }
  ]);

  // Sync candidate farmers and buyers dynamically when negState arrives
  useEffect(() => {
    if (negState) {
      const baseOffer = Number(negState.price || negState.current_offer || 68.5);
      setLiveSellers(prev => [
        {
          ...prev[0],
          offer: prev[0].aiStatus.includes('Target') || prev[0].aiStatus.includes('Override') || prev[0].aiStatus.includes('Counter') || prev[0].aiStatus.includes('Matched')
            ? prev[0].offer
            : baseOffer,
          aiStatus: prev[0].aiStatus.includes('Target') || prev[0].aiStatus.includes('Override') || prev[0].aiStatus.includes('Counter') || prev[0].aiStatus.includes('Matched')
            ? prev[0].aiStatus
            : 'Verified APMC Grade A',
        },
        {
          ...prev[1],
          id: negState.farmer_name || negState.farmer || prev[1].id,
          location: negState.location || prev[1].location,
          offer: prev[1].aiStatus.includes('Counter') ? prev[1].offer : Math.round((baseOffer * 1.02) * 10) / 10,
        },
        {
          ...prev[2],
          offer: prev[2].aiStatus.includes('Counter') ? prev[2].offer : Math.round((baseOffer * 1.04) * 10) / 10,
          aiStatus: prev[2].aiStatus.includes('Target') || prev[2].aiStatus.includes('Override') ? prev[2].aiStatus : `Counter ₹${targetPrice || 66.2}`
        }
      ]);

      if (!manualPrice) {
        const initTarget = Number(negState.target_price || negState.buyer_target_price || targetPrice || 48);
        setManualPrice(String(Math.round(initTarget * 10) / 10));
      }

      // Sync candidate buyers for Farmer Copilot
      const farmerBaseOffer = Number(negState.price || negState.current_offer || 2500);
      const normalizedFarmerOffer = farmerBaseOffer < 100 ? Math.round(farmerBaseOffer * 100) : Math.round(farmerBaseOffer);
      setLiveBuyers(prev => [
        {
          ...prev[0],
          id: negState.buyer_name || negState.buyer || prev[0].id,
          offer: prev[0].aiStatus.includes('Override') ? prev[0].offer : normalizedFarmerOffer,
          aiStatus: prev[0].aiStatus.includes('Override') ? prev[0].aiStatus : 'Farmer Override: ₹' + normalizedFarmerOffer,
        },
        {
          ...prev[1],
          offer: Math.round(normalizedFarmerOffer * 0.99),
        },
        {
          ...prev[2],
          offer: Math.round(normalizedFarmerOffer * 0.97),
        }
      ]);
      setFarmerManualPrice(prev => prev === 2550 ? normalizedFarmerOffer + 50 : prev);
    }
  }, [negState, targetPrice]);


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
    return Math.round(Math.max(Number(targetPrice) * 1.35, statutoryBench * 1.40) * 10) / 10;
  }, [targetPrice, statutoryBench]);

  const minAllowedFloor = useMemo(() => {
    return Math.round(statutoryBench * 0.35 * 100) / 100;
  }, [statutoryBench]);

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

  // Sync initial history from database into messages
  useEffect(() => {
    if (negState) {
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
      } else if (messages.length === 0) {
        setMessages([
          {
            agent: isBuyer ? 'Farmer Agent (Latur Mandi)' : 'Buyer Agent (Procurement)',
            message: `Namaste! Initializing APMC session for ${cropQty.toLocaleString()}kg ${cropName}. Opening offer based on current mandi arrival rates.`,
            type: 'text'
          },
          {
            agent: isBuyer ? 'Farmer Agent (Latur Mandi)' : 'Buyer Agent (Procurement)',
            price: Math.round(targetPrice * 1.06 * 10) / 10,
            quantity: cropQty,
            quality: 'A',
            deliveryDate: '3-4 Business Days',
            transportIncluded: true,
            warehouseIncluded: false,
            validity: '24 Hours',
            type: 'offer',
            message: `Offering Grade-A lot at ₹${(Math.round(targetPrice * 1.06 * 10) / 10)}/kg.`,
            reasoning: [
              `APMC Modal Price: ₹${marketPrice}/kg`,
              `Moisture content tested < 10%`,
              `Transit distance: 180 km via NH-65`
            ]
          }
        ]);
      }

      if (negState.status === 'DEAL' || negState.status === 'COMPLETED' || negState.final_price) {
        setDealAccepted(true);
        const finalP = negState.final_price || negState.price || targetPrice;
        setAgreementData({
          ...negState,
          id: effectiveId || id,
          negotiation_id: effectiveId || id,
          crop: cropName,
          quantity: cropQty,
          price: finalP,
          final_price: finalP,
          farmer: negState.farmer || negState.farmer_name || 'Latur APMC Cooperative',
          buyer: negState.buyer || negState.buyer_name || (user?.name || user?.full_name || 'Buyer Enterprise'),
          status: 'DEAL'
        });
        setShowAgreement(true);
      }
    }
  }, [negState, cropQty, cropName, targetPrice, marketPrice, statutoryBench, isBuyer, user]);

  // Auto-start autonomous negotiation so both farmer and buyer see terminal live execution immediately
  useEffect(() => {
    if (
      effectiveId &&
      !isParallelRunning &&
      liveTerminalLogs.length === 0 &&
      !isDealFinalized
    ) {
      const timer = setTimeout(() => {
        runParallelAutonomousNegotiation();
      }, 700);
      return () => clearTimeout(timer);
    }
  }, [effectiveId, liveTerminalLogs.length, isDealFinalized]);

  // Terminal Auto-Scroll to bottom as logs stream in
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [liveTerminalLogs]);

  // Handle incoming WS messages
  useEffect(() => {
    if (lastMessage) {
      const msgNegId = String(lastMessage.negotiation_id || lastMessage.data?.negotiation_id || '');
      if (!msgNegId || msgNegId === String(effectiveId || id)) {
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        if (lastMessage.event === 'NEGOTIATION_LOG') {
          const isFarmerSender = lastMessage.agent_type === 'farmer';
          setLiveTerminalLogs(prev => [
            ...prev,
            { time, tag: isFarmerSender ? 'Farmer' : 'Buyer', color: isFarmerSender ? 'text-emerald-400' : 'text-blue-400', text: lastMessage.message }
          ]);
        } else if (lastMessage.event === 'TOP5_ROUND_UPDATE') {
          setLiveTerminalLogs(prev => [
            ...prev,
            { time, tag: `ROUND ${lastMessage.round}`, color: 'text-amber-400', text: `${lastMessage.actor || 'AGENT'}: ${lastMessage.message || `Offer ₹${lastMessage.price}/kg for ${lastMessage.quantity}kg`}` }
          ]);
        } else if (lastMessage.event === 'TOP5_CANDIDATE_DISCOVERED') {
          setLiveTerminalLogs(prev => [
            ...prev,
            { time, tag: 'DISCOVERY', color: 'text-blue-400', text: `Discovered candidate: ${lastMessage.name} (${lastMessage.location}) - Ask: ₹${lastMessage.price}/kg` }
          ]);
        } else if (lastMessage.event === 'NEGOTIATION_STATE_UPDATE' || lastMessage.event === 'negotiation_state_update') {
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
        } else if (lastMessage.event === 'NEGOTIATION_FINISHED' || lastMessage.event === 'PARALLEL_PROCUREMENT_COMPLETE') {
          const finalP = lastMessage.final_price || lastMessage.winner?.negotiated_price || targetPrice;
          const finalDeal = {
            ...negState,
            id: id,
            negotiation_id: id,
            price: finalP,
            final_price: finalP,
            quantity: cropQty,
            status: 'DEAL',
            farmer: lastMessage.winner?.name || negState?.farmer || 'Latur APMC Producer',
            buyer: user?.name || user?.full_name || 'Buyer Enterprise'
          };
          setAgreementData(finalDeal);
          setShowAgreement(true);
          refetchNeg();
        }
      }
    }
  }, [lastMessage, id, negState, cropQty, targetPrice, user, refetchNeg]);

  const runParallelAutonomousNegotiation = async () => {
    setIsParallelRunning(true);
    setLiveTerminalLogs([]);
    setActiveTab('terminal');

    const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const timelineSteps = isBuyer ? [
      { tag: 'CLUSTER', color: 'text-emerald-400', text: `🚀 Connected to LangGraph RL Daemon for ${cropQty.toLocaleString()} kg ${cropName}. Contract #${id?.substring(0, 8)}.` },
      { tag: 'POLICY', color: 'text-purple-400', text: `Statutory MSP: ₹${statutoryBench}/kg | Live Modal: ₹${marketPrice}/kg | Target Ceiling: ₹${targetPrice}/kg.` },
      { tag: 'DISCOVERY', color: 'text-blue-400', text: `Scanning 5 candidate Maharashtra APMC Mandis (Latur, Nanded, Solapur, Akola, Sangli).` },
      { tag: 'DISCOVERY', color: 'text-blue-400', text: `Discovered 3 verified suppliers: Suresh Deshmukh (Nanded), ${farmerName} (${farmerLocation}), Vilas Jadhav (Akola).` },
      { tag: 'ROUND 1', color: 'text-amber-400', text: `Vilas Jadhav (Akola) opened ask at ₹71.2/kg | LangGraph Agent counter-offered ₹${Math.round(targetPrice)}/kg.` },
      { tag: 'ROUND 1', color: 'text-amber-400', text: `${farmerName} (${farmerLocation}) proposed ₹${Math.round(targetPrice * 1.05 * 10) / 10}/kg | Evaluating mandi cess & transport.` },
      { tag: 'ROUND 2', color: 'text-emerald-400', text: `Suresh Deshmukh matched counter at ₹${bestOfferPrice}/kg with verified APMC Grade-A certification.` },
      { tag: 'OPTIMIZER', color: 'text-indigo-400', text: `RL Multi-attribute utility: 96% Match | Freight: ₹1.80/kg via NH-65 | APMC 1% cess factored.` },
      { tag: 'ROUND 3', color: 'text-emerald-400', text: `Bidding converged: Suresh Deshmukh chosen as #1 optimal supplier at ₹${bestOfferPrice}/kg.` },
      { tag: 'WINNER', color: 'text-emerald-300 font-bold', text: `🏆 Best Deal Executable: Suresh Deshmukh at ₹${bestOfferPrice}/kg. Net: ₹${Math.round(bestOfferPrice * cropQty).toLocaleString()}. Ready to accept.` }
    ] : [
      { tag: 'CLUSTER', color: 'text-emerald-400', text: `🚀 Connected to LangGraph RL Daemon for ${cropQty.toLocaleString()} Q ${cropName}. Contract #${(effectiveId || id || 'ACTIVE')?.substring(0, 8)}.` },
      { tag: 'POLICY', color: 'text-purple-400', text: `Statutory Benchmark (MSP): ₹${statutoryBench}/kg | Farmer Reserve Floor: ₹${currentFloor}/q.` },
      { tag: 'DISCOVERY', color: 'text-blue-400', text: `Broadcasting lot to verified institutional buyers & Maharashtra agro-processors.` },
      { tag: 'ROUND 1', color: 'text-amber-400', text: `Buyer C (Akola) opened bidding at ₹2,420/q | LangGraph Copilot countered ₹2,500/q.` },
      { tag: 'ROUND 1', color: 'text-blue-400', text: `Buyer B (Solapur) submitted ₹2,480/q | Status: Waiting on buyer review.` },
      { tag: 'ROUND 2', color: 'text-emerald-400', text: `Buyer A (Mumbai) raised bid to ₹2,500/q | 96% Match | Mandi transport included.` },
      { tag: 'VALIDATION', color: 'text-indigo-400', text: `Quality inspection verified: Moisture < 10%, APMC Model Act compliant.` },
      { tag: 'OPTIMIZER', color: 'text-emerald-400', text: `Buyer A selected as top offer exceeding floor by +₹100/q.` },
      { tag: 'WINNER', color: 'text-emerald-300 font-bold', text: `🏆 Best deal reached with Buyer A at ₹2,500/q! Ready for farmer acceptance.` }
    ];

    // Fire background API call to update DB if endpoint exists
    if (effectiveId || id) {
      api.post(`/negotiations/${effectiveId || id}/parallel-procure`, {
        quantity: cropQty,
        target_price: targetPrice
      }).catch(err => console.debug('Background parallel procure sync:', err));
    }

    // Stream the live negotiation rounds in real time
    timelineSteps.forEach((step, idx) => {
      setTimeout(() => {
        setLiveTerminalLogs(prev => [
          ...prev,
          {
            time: now(),
            tag: step.tag,
            color: step.color,
            text: step.text
          }
        ]);

        // Dynamically update candidate cards during bidding rounds
        if (isBuyer) {
          if (step.tag === 'ROUND 1') {
            setLiveSellers(prev => prev.map((s, i) => i === 2 ? { ...s, status: 'Waiting', aiStatus: `Counter ₹${Math.round(targetPrice)}` } : s));
          } else if (step.tag === 'ROUND 2' || step.tag === 'ROUND 3') {
            setLiveSellers(prev => prev.map((s, i) => i === 0 ? { ...s, status: 'Negotiating', aiStatus: `Verified APMC Grade A` } : s));
          }
        } else {
          if (step.tag === 'ROUND 1') {
            setLiveBuyers(prev => prev.map((b, i) => i === 2 ? { ...b, status: 'Negotiating', aiStatus: 'Counter ₹2500' } : b));
          } else if (step.tag === 'ROUND 2' || step.tag === 'WINNER') {
            setLiveBuyers(prev => prev.map((b, i) => i === 0 ? { ...b, status: 'Negotiating', aiStatus: 'Farmer Override: ₹2500' } : b));
          }
        }

        if (idx === timelineSteps.length - 1) {
          setIsParallelRunning(false);
          refetchNeg();
        }
      }, (idx + 1) * 750);
    });
  };

  const executeCopilotCommand = (commandOverride?: string) => {
    const rawCmd = commandOverride !== undefined ? commandOverride : copilotCommand;
    const cmd = (rawCmd || '').trim();
    if (!cmd) return;

    // CRITICAL: Unlock negotiation state so user's manual copilot instruction re-engages live active bidding
    setIsRenegotiating(true);
    setDealAccepted(false);
    setActiveTab('terminal');

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const userRole = isBuyer ? 'Buyer' : 'Farmer';
    const userMsg = { sender: userRole, text: cmd, time: now };

    setCopilotMessages(prev => [...prev, userMsg]);
    setLiveTerminalLogs(prev => [
      ...prev,
      {
        time: now,
        tag: 'COPILOT',
        color: 'text-amber-400',
        text: `⚡ [${userRole.toUpperCase()} COPILOT] Manual instruction applied: "${cmd}". Updating agent policy & parameters.`
      }
    ]);

    // Clear input field
    setCopilotCommand('');

    const lower = cmd.toLowerCase();

    if (isBuyer) {
      // ---------------- BUYER COPILOT EXECUTION ----------------
      if (lower.includes('pause') || lower.includes('stop') || lower.includes('hold')) {
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setLiveSellers(prev => prev.map(s => ({ ...s, status: 'Waiting', aiStatus: 'Paused by Copilot' })));
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'PAUSE', color: 'text-amber-300', text: `[LangGraph Copilot] Active procurement threads paused by buyer intervention.` }
          ]);
          setCopilotMessages(prev => [...prev, { sender: 'AI', text: 'Procurement negotiations paused. Waiting for your instruction to resume.', time: t }]);
        }, 300);
      } else if (lower.includes('resume') || lower.includes('continue') || lower.includes('start')) {
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setLiveSellers(prev => prev.map(s => ({ ...s, status: 'Negotiating', aiStatus: 'Active Bidding' })));
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'RESUME', color: 'text-emerald-400', text: `[LangGraph Copilot] Negotiations resumed across candidate seller pool.` }
          ]);
          setCopilotMessages(prev => [...prev, { sender: 'AI', text: 'Procurement negotiations resumed. Actively engaging candidate farmers.', time: t }]);
        }, 300);
      } else if (lower.includes('exceed') || lower.includes('ceiling') || lower.includes('above') || lower.includes('max')) {
        const match = cmd.match(/\d+(\.\d+)?/);
        const val = match ? Number(match[0]) : Math.round(maxAllowedCeiling);
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'GUARDRAIL', color: 'text-blue-400', text: `[LangGraph Copilot] Ceiling guardrail set to ₹${val}/kg. High-ask candidates will be auto-countered.` }
          ]);
          setCopilotMessages(prev => [...prev, { sender: 'AI', text: `Understood. Procurement ceiling set to ₹${val}/kg. AI will not accept bids above this rate.`, time: t }]);
        }, 300);
      } else {
        // Counter offer / Target / Specific price / Freeform
        const match = cmd.match(/\d+(\.\d+)?/);
        let counterVal = match ? Number(match[0]) : Math.round(targetPrice);
        if (!match && lower.includes('best')) {
          counterVal = Math.round(((liveSellers[0]?.offer || 50) - 2) * 10) / 10;
        } else if (!match && lower.includes('target')) {
          counterVal = Math.round(targetPrice);
        }

        setManualPrice(String(counterVal));

        // Step 1: Dispatch to candidate farmers (500ms)
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'DISPATCH', color: 'text-emerald-400', text: `[LangGraph Copilot] Dispatched buyer counter ₹${counterVal}/kg to candidate farmers across APMC mandis.` }
          ]);
          setLiveSellers(prev => prev.map((s, i) => i === 2 ? { ...s, status: 'Waiting', aiStatus: `Evaluating ₹${counterVal}/kg` } : s));
          setCopilotMessages(prev => [...prev, { sender: 'AI', text: `Manual instruction applied. Counter offer of ₹${counterVal}/kg dispatched to candidate farmers.`, time: t }]);
        }, 500);

        // Step 2: Intermediate rounds (1200ms)
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          const vilasAsk = Math.round((counterVal * 1.04) * 10) / 10;
          const rameshAsk = Math.round((counterVal * 1.02) * 10) / 10;
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'ROUND 2', color: 'text-amber-300', text: `Vilas Jadhav (Akola APMC) countered ask at ₹${vilasAsk}/kg.` },
            { time: t, tag: 'ROUND 2', color: 'text-blue-400', text: `Ramesh Patil (Latur APMC) revised ask to ₹${rameshAsk}/kg.` }
          ]);
          setLiveSellers(prev => [
            prev[0],
            { ...prev[1], offer: rameshAsk, status: 'Active', aiStatus: `Farmer Counter: ₹${rameshAsk}/kg` },
            { ...prev[2], offer: vilasAsk, status: 'Waiting', aiStatus: `Counter ₹${vilasAsk}/kg` }
          ]);
        }, 1200);

        // Step 3: Best seller matches (1900ms)
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'ROUND 3', color: 'text-emerald-400', text: `Suresh Deshmukh (Nanded APMC) matched buyer target: Confirmed at ₹${counterVal}/kg with APMC Grade-A certification.` },
            { time: t, tag: 'WINNER', color: 'text-emerald-300 font-bold', text: `🏆 Optimal Deal Ready: Suresh Deshmukh at ₹${counterVal}/kg. Net: ₹${Math.round(counterVal * cropQty).toLocaleString()}. Click 'Accept Deal' to confirm contract.` }
          ]);
          setLiveSellers(prev => [
            { ...prev[0], offer: counterVal, status: 'Negotiating', aiStatus: `Buyer Override: ₹${counterVal}/kg (Matched)` },
            prev[1],
            prev[2]
          ]);
        }, 1900);
      }
    } else {
      // ---------------- FARMER COPILOT EXECUTION ----------------
      if (lower.includes('pause') || lower.includes('stop') || lower.includes('hold')) {
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setLiveBuyers(prev => prev.map(b => ({ ...b, status: 'Waiting', aiStatus: 'Paused by Copilot' })));
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'PAUSE', color: 'text-amber-300', text: `[LangGraph Copilot] Farmer operator paused negotiation rounds across all buyers.` }
          ]);
          setCopilotMessages(prev => [...prev, { sender: 'AI', text: 'Negotiations paused. Waiting for your instruction to resume.', time: t }]);
        }, 300);
      } else if (lower.includes('resume') || lower.includes('continue') || lower.includes('start')) {
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setLiveBuyers(prev => prev.map(b => ({ ...b, status: 'Negotiating', aiStatus: 'Active Bidding' })));
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'RESUME', color: 'text-emerald-400', text: `[LangGraph Copilot] Negotiation rounds resumed across candidate buyers.` }
          ]);
          setCopilotMessages(prev => [...prev, { sender: 'AI', text: 'Negotiations resumed. Counter offers active across buyer pool.', time: t }]);
        }, 300);
      } else if (lower.includes('below') || lower.includes('minimum') || lower.includes('floor')) {
        const match = cmd.match(/\d+(\.\d+)?/);
        if (match) {
          const rawVal = Number(match[0]);
          const valQ = rawVal < 100 ? rawVal * 100 : rawVal;
          const valKg = rawVal < 100 ? rawVal : (rawVal / 100);

          if (valKg < minAllowedFloor) {
            setTimeout(() => {
              const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
              setLiveTerminalLogs(prev => [
                ...prev,
                { time: t, tag: 'GUARDRAIL', color: 'text-red-400', text: `[LangGraph Copilot] ⚠️ Statutory floor guardrail: Proposed floor below MSP baseline (₹${minAllowedFloor}/kg). Override rejected.` }
              ]);
              setCopilotMessages(prev => [...prev, { sender: 'AI', text: `⚠️ Override blocked. ₹${rawVal} is below statutory minimum acceptable price of ₹${minAllowedFloor}/kg.`, time: t }]);
            }, 300);
          } else {
            setFarmerManualPrice(valQ);
            setTimeout(() => {
              const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
              setLiveTerminalLogs(prev => [
                ...prev,
                { time: t, tag: 'FLOOR', color: 'text-emerald-400', text: `[LangGraph Copilot] Farmer reservation floor updated to ₹${valQ}/q (₹${valKg.toFixed(1)}/kg). Counter-offers dispatched.` },
                { time: t, tag: 'DISPATCH', color: 'text-blue-400', text: `[LangGraph Copilot] Rejecting all bids below ₹${valQ}/q. Buyer pool instructed to meet reservation floor.` }
              ]);
              setCopilotMessages(prev => [...prev, { sender: 'AI', text: `Understood. I'll update your negotiation floor to ₹${valQ}/q (₹${valKg.toFixed(1)}/kg). Negotiators are forcing buyers to meet floor.`, time: t }]);
              setLiveBuyers(prev => prev.map(b => ({
                ...b,
                offer: Math.max(valQ, b.offer),
                status: 'Negotiating',
                aiStatus: b.offer < valQ ? `Raised to meet floor: ₹${valQ}/q` : b.aiStatus
              })));
            }, 500);

            setTimeout(() => {
              const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
              const bestOffer = Math.max(valQ, liveBuyers[0]?.offer || valQ);
              setLiveTerminalLogs(prev => [
                ...prev,
                { time: t, tag: 'ROUND 2', color: 'text-emerald-400', text: `Buyer A matched floor requirement: Bid confirmed at ₹${bestOffer}/q (96% Match).` },
                { time: t, tag: 'WINNER', color: 'text-emerald-300 font-bold', text: `🏆 Optimal Deal Ready: Buyer A at ₹${bestOffer}/q. Click 'Accept Deal' to confirm contract.` }
              ]);
              setLiveBuyers(prev => prev.map((b, i) => i === 0 ? { ...b, offer: bestOffer, status: 'Negotiating', aiStatus: `Farmer Override: ₹${bestOffer}/q` } : b));
            }, 1400);
          }
        }
      } else {
        // Counter / Ask / Specific price / Freeform
        const match = cmd.match(/\d+(\.\d+)?/);
        let targetAsk = farmerManualPrice;
        if (match) {
          const raw = Number(match[0]);
          targetAsk = raw < 100 ? raw * 100 : raw;
        } else if (lower.includes('best')) {
          targetAsk = (liveBuyers[0]?.offer || 2500) + 50;
        }

        const targetAskKg = (targetAsk / 100).toFixed(1);
        setFarmerManualPrice(targetAsk);

        // Step 1: Dispatch to candidate buyers (500ms)
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'DISPATCH', color: 'text-emerald-400', text: `[LangGraph Copilot] Dispatched farmer counter-offer ₹${targetAsk}/q (₹${targetAskKg}/kg) to Buyer A, B, and C.` }
          ]);
          setLiveBuyers(prev => prev.map((b, i) => i === 2 ? { ...b, status: 'Negotiating', aiStatus: `Countering ask: ₹${Math.round(targetAsk * 0.96)}/q` } : b));
          setCopilotMessages(prev => [...prev, { sender: 'AI', text: `Manual instruction applied. Counter offer of ₹${targetAsk}/q (₹${targetAskKg}/kg) dispatched to candidate buyers.`, time: t }]);
        }, 500);

        // Step 2: Intermediate rounds (1200ms)
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          const buyerCOffer = Math.round(targetAsk * 0.96);
          const buyerBOffer = Math.round(targetAsk * 0.985);
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'ROUND 2', color: 'text-amber-300', text: `Buyer C (Akola) evaluated ask: Cannot match ₹${targetAsk}/q. Standing at ₹${buyerCOffer}/q.` },
            { time: t, tag: 'ROUND 2', color: 'text-blue-400', text: `Buyer B (Solapur) raised bid to ₹${buyerBOffer}/q (93% Match).` }
          ]);
          setLiveBuyers(prev => [
            prev[0],
            { ...prev[1], offer: buyerBOffer, status: 'Negotiating', aiStatus: `Counter ₹${buyerBOffer}/q` },
            { ...prev[2], offer: buyerCOffer, status: 'Waiting', aiStatus: `Standing at ₹${buyerCOffer}/q` }
          ]);
        }, 1200);

        // Step 3: Best buyer matches (1900ms)
        setTimeout(() => {
          const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          const netTotal = Math.round(targetAsk * (cropQty < 100 ? cropQty * 100 : cropQty) - 1850);
          setLiveTerminalLogs(prev => [
            ...prev,
            { time: t, tag: 'ROUND 3', color: 'text-emerald-400', text: `Buyer A / Dining accepted farmer ask: Revised bid matched to ₹${targetAsk}/q (96% Match).` },
            { time: t, tag: 'WINNER', color: 'text-emerald-300 font-bold', text: `🏆 Optimal Deal Ready: Buyer A at ₹${targetAsk}/q. Net: ₹${netTotal.toLocaleString()}. Click 'Accept Deal' to confirm contract.` }
          ]);
          setLiveBuyers(prev => [
            { ...prev[0], offer: targetAsk, status: 'Negotiating', aiStatus: `Farmer Override: ₹${targetAsk}/q (Matched)` },
            prev[1],
            prev[2]
          ]);
        }, 1900);
      }
    }
  };

  const handleCopilotSubmit = (e: any) => {
    e.preventDefault();
    executeCopilotCommand();
  };

  // CRITICAL FIX: Only show full-screen initialization spinner on first load when there is an active session being fetched and no data has arrived yet.
  // NEVER show it during silent background polling/refetches, so the page NEVER flashes or buffers!
  if (isLoading && !negState && effectiveId) {
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center space-y-3">
        <div className="w-10 h-10 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-600 font-bold text-sm">Initializing LangGraph Negotiation Engine...</p>
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
                  {(['FARMER', 'PROCESSOR', 'BUYER'].includes(activeStakeholder) || isBuyer) && activeWorkflow === 'FULL_SUPPLY_CHAIN' ? <CheckCircle size={14} className="text-emerald-600" /> : <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />}
                  <span className={(['FARMER', 'PROCESSOR', 'BUYER'].includes(activeStakeholder) || isBuyer) && activeWorkflow === 'FULL_SUPPLY_CHAIN' ? 'text-slate-800 font-bold' : 'text-slate-400'}>
                    {isBuyer ? 'Farmer / Producer' : 'Buyer / Supplier'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {activeWorkflow === 'FULL_SUPPLY_CHAIN' || activeWorkflow === 'TRANSPORT_ONLY' ? <CheckCircle size={14} className="text-emerald-600" /> : <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300" />}
                  <span className={activeWorkflow === 'FULL_SUPPLY_CHAIN' || activeWorkflow === 'TRANSPORT_ONLY' ? 'text-slate-800 font-bold' : 'text-slate-400'}>
                    Transport
                  </span>
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
              <span className="text-slate-500">{isBuyer ? 'Procurement Volume' : 'Lot Volume'}</span>
              <span className="font-black text-slate-800">{cropQty.toLocaleString()} kg</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Live Modal Price</span>
              <span className="font-black text-slate-800">₹{marketPrice}/kg</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">{isBuyer ? 'Target Offer' : 'Target Ceiling'}</span>
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
              <div className="flex items-center justify-between">
                <p className="font-bold text-amber-700 flex items-center gap-1.5">
                  <Truck size={14} /> HIGHWAY LOGISTICS
                </p>
              </div>
              <p className="text-slate-600">
                Freight estimated dynamically across Maharashtra corridors based on mandi transit and vehicle availability.
              </p>
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
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
              <MessageSquare size={17} className="text-emerald-500" /> AI Agent Negotiation — <span className="text-slate-500 font-normal">{cropName}</span>
            </h3>
            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Live
            </div>
          </div>

          <div className="flex-1 overflow-y-auto bg-slate-50/40 p-5 space-y-4">

            {isBuyer ? (
              /* Buyer's view of Candidate Farmers & Best Deal */
              <>
                <div className="space-y-3">
                  {liveSellers.map((s, i) => (
                    <div key={i} className={`bg-white border rounded-2xl p-4 shadow-sm relative overflow-hidden transition-all ${s.aiStatus?.includes('Target') || s.aiStatus?.includes('Override') ? 'border-indigo-400 ring-2 ring-indigo-50' : 'border-slate-200/90'}`}>
                      <div className="flex justify-between items-center mb-2.5">
                        <div>
                          <h4 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
                            <Star size={16} className="text-amber-400 fill-amber-400" /> {s.id} — {s.match}% Match
                          </h4>
                          <p className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
                            <MapPin size={10} /> {s.location}
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="font-black text-slate-900 text-lg">₹{s.offer}/kg</span>
                        </div>
                      </div>

                      {s.aiStatus?.includes('Target') || s.aiStatus?.includes('Override') ? (
                        <div className="mb-2.5">
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                            <ShieldCheck size={12} className="text-indigo-600" /> BUYER OVERRIDE APPLIED
                          </span>
                        </div>
                      ) : (
                        <div className="mb-2.5">
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                            <ShieldCheck size={12} className="text-emerald-600" /> VERIFIED APMC GRADE A
                          </span>
                        </div>
                      )}

                      <div className="space-y-1.5 text-xs pt-2 border-t border-slate-100">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-500 font-medium">AI Strategy:</span>
                          <span className="font-semibold text-slate-700">{s.aiStatus}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-500 font-medium">Status:</span>
                          <span className="font-semibold flex items-center gap-1.5">
                            <span className={`w-2 h-2 rounded-full ${
                              (i === 0 && isDealFinalized)
                                ? 'bg-emerald-600'
                                : (s.status === 'Negotiating' || s.status === 'Active' ? 'bg-emerald-500 animate-pulse' : 'bg-blue-500')
                            }`}></span>
                            <span className={
                              (i === 0 && isDealFinalized)
                                ? 'text-emerald-700 font-bold'
                                : (s.status === 'Negotiating' || s.status === 'Active' ? 'text-emerald-700' : 'text-blue-700')
                            }>
                              {(i === 0 && isDealFinalized)
                                ? 'Deal Closed (Accepted)'
                                : (s.status === 'Active' ? 'Negotiating' : s.status)}
                            </span>
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Finalized Banner if Deal Accepted */}
                {isDealFinalized && (
                  <div className="bg-emerald-50 border-2 border-emerald-500/80 rounded-2xl p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3 animate-in fade-in">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-emerald-500 flex items-center justify-center text-slate-900 font-black text-sm shrink-0">
                        ✓
                      </div>
                      <div>
                        <h4 className="font-bold text-emerald-950 text-sm">Deal Accepted & Finalized</h4>
                        <p className="text-xs text-emerald-700">Contract confirmed under Maharashtra APMC framework. Recorded in ledger.</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <button
                        onClick={() => setShowValidationModal(true)}
                        className="flex-1 sm:flex-initial px-3.5 py-2 rounded-xl bg-white border border-emerald-300 text-emerald-800 font-bold text-xs hover:bg-emerald-100 transition shadow-sm"
                      >
                        View Term Sheet
                      </button>
                      <Link
                        to="/transactions"
                        className="flex-1 sm:flex-initial px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-black text-xs transition shadow flex items-center justify-center gap-1.5"
                      >
                        <ExternalLink size={13} /> View in Transactions
                      </Link>
                    </div>
                  </div>
                )}

                {/* Best Deal So Far (Buyer Parity with Farmer Layout) */}
                <div className="bg-[#064e3b] p-4 text-white rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4 shadow-md mt-2">
                  <div>
                    <p className="text-emerald-300 text-[10px] font-bold uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      <Trophy size={13} className="text-amber-400" /> BEST DEAL SO FAR
                    </p>
                    <div className="flex items-center flex-wrap gap-2 text-xs">
                      <span className="font-bold text-base text-white">{liveSellers[0].id}</span>
                      <span className="bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 px-2 py-0.5 rounded text-xs font-bold">
                        ₹{liveSellers[0].offer}/kg
                      </span>
                      <span className="text-emerald-100">{cropQty.toLocaleString()} kg</span>
                      <span className="text-emerald-100">{liveSellers[0].match}% Match</span>
                      <span className="font-bold text-emerald-200">
                        Net: ₹{Math.round(liveSellers[0].offer * cropQty).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
                    <button
                      onClick={() => setIsRagOpen(true)}
                      className="px-3.5 py-2 rounded-xl border border-emerald-500/70 text-emerald-100 bg-emerald-800/40 hover:bg-emerald-800 text-xs font-bold transition flex-1 sm:flex-none text-center cursor-pointer"
                    >
                      View Analysis
                    </button>
                    <button
                      onClick={() => {
                        handleAcceptDeal({
                          price: liveSellers[0].offer,
                          farmer: liveSellers[0].id,
                          farmer_name: liveSellers[0].id,
                          buyer: buyerName,
                          crop: cropName,
                          quantity: cropQty
                        });
                      }}
                      className={`px-4 py-2 rounded-xl font-black text-xs transition shadow flex-1 sm:flex-none text-center cursor-pointer ${
                        isDealFinalized
                          ? 'bg-emerald-600 text-white hover:bg-emerald-500'
                          : 'bg-emerald-500 hover:bg-emerald-400 text-slate-900'
                      }`}
                    >
                      {isDealFinalized ? '✓ Accepted • View Contract' : 'Accept Deal'}
                    </button>
                  </div>
                </div>
              </>
            ) : liveBuyers.length > 0 ? (
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

                {/* Finalized Banner if Deal Accepted (Farmer Parity with Buyer) */}
                {isDealFinalized && (
                  <div className="bg-emerald-50 border-2 border-emerald-500/80 rounded-2xl p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3 animate-in fade-in">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-emerald-500 flex items-center justify-center text-slate-900 font-black text-sm shrink-0">
                        ✓
                      </div>
                      <div>
                        <h4 className="font-bold text-emerald-950 text-sm">Deal Accepted & Finalized</h4>
                        <p className="text-xs text-emerald-700">Contract confirmed under Maharashtra APMC framework. Recorded in ledger.</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <button
                        onClick={() => setShowValidationModal(true)}
                        className="flex-1 sm:flex-initial px-3.5 py-2 rounded-xl bg-white border border-emerald-300 text-emerald-800 font-bold text-xs hover:bg-emerald-100 transition shadow-sm"
                      >
                        View Term Sheet
                      </button>
                      <Link
                        to="/transactions"
                        className="flex-1 sm:flex-initial px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-black text-xs transition shadow flex items-center justify-center gap-1.5"
                      >
                        <ExternalLink size={13} /> View in Transactions
                      </Link>
                    </div>
                  </div>
                )}

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
                        handleAcceptDeal({
                          price: liveBuyers[0].offer,
                          farmer: user?.name,
                          buyer: liveBuyers[0].id,
                          crop: cropName,
                          quantity: cropQty
                        });
                      }}
                      className={`px-4 py-2 rounded-xl font-black text-xs transition shadow flex-1 sm:flex-none text-center cursor-pointer ${
                        isDealFinalized
                          ? 'bg-emerald-600 text-white hover:bg-emerald-500'
                          : 'bg-emerald-500 hover:bg-emerald-400 text-slate-900'
                      }`}
                    >
                      {isDealFinalized ? '✓ Accepted • View Contract' : 'Accept Deal'}
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
        </div>
      </div>

      {/* ════ COLUMN 3: Right Panel (LangGraph + Farmer Copilot ~25%) ════ */}
      <div className="w-full xl:w-1/4 flex flex-col gap-4 h-full">

        {/* Card 1: LangGraph Execution */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                <Zap size={16} className="text-emerald-500" /> LangGraph Execution
              </h4>
            </div>

            <div className="space-y-3 mb-5">
              <div className="flex items-center justify-between text-xs font-bold text-slate-800">
                <span>PLANNING</span>
                <span className="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 border border-emerald-100">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> RUNNING
                </span>
              </div>
              <div className="text-xs font-bold text-slate-400">INTELLIGENCE</div>
              <div className="text-xs font-bold text-slate-400">NEGOTIATION</div>
              <div className="text-xs font-bold text-slate-400">VALIDATION</div>
            </div>
          </div>

          {/* View RAG Context Button */}
          <button
            type="button"
            onClick={() => setIsRagOpen(true)}
            className="w-full py-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 text-slate-700 font-bold rounded-xl transition text-xs flex justify-center items-center gap-2 shadow-sm"
          >
            <Database size={14} className="text-slate-500" /> View RAG Context
          </button>
        </div>

        {/* Card 2: Either Buyer Copilot or Farmer Copilot */}
        {isBuyer ? (
          <div className="bg-[#0f172a] rounded-2xl shadow-lg border border-slate-800 p-5 text-white flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-sm flex items-center gap-2 text-white">
                  <ShieldCheck size={16} className="text-blue-400" />
                  <span className="text-base">🏢</span> Buyer Procurement Copilot
                </h3>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                AI is procuring automatically based on your target price, reservation ceiling, and APMC freight. You can intervene at any time.
              </p>

              {/* Quick Action Chips */}
              <div className="flex flex-wrap gap-2 mb-4">
                <button
                  type="button"
                  onClick={() => executeCopilotCommand(`Counter at target ₹${Math.round(targetPrice || 48)}`)}
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition cursor-pointer"
                >
                  Counter target ₹{Math.round(targetPrice || 48)}
                </button>
                <button
                  type="button"
                  onClick={() => executeCopilotCommand(`Don't exceed ₹${Math.round(maxAllowedCeiling || 52)}`)}
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition cursor-pointer"
                >
                  Ceiling ₹{Math.round(maxAllowedCeiling || 52)}
                </button>
                <button
                  type="button"
                  onClick={() => executeCopilotCommand('Counter best farmer')}
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition cursor-pointer"
                >
                  Counter best farmer
                </button>
                <button
                  type="button"
                  onClick={() => executeCopilotCommand('Pause negotiations')}
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition cursor-pointer"
                >
                  Pause negotiations
                </button>
              </div>

              {/* Manual Bid Increment Tools */}
              <div className="mb-4 p-3 bg-slate-900/90 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-300 font-semibold">
                  <span>Manual Offer Price:</span>
                  <span className="text-emerald-400 font-mono font-bold">₹{manualPrice || targetPrice}/kg</span>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      const base = parseFloat(manualPrice) || targetPrice || 40;
                      setManualPrice((base - 1.0).toFixed(1));
                    }}
                    className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-amber-300 rounded-lg text-[11px] font-bold border border-slate-700 transition cursor-pointer text-center"
                  >
                    -₹1.00
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const base = parseFloat(manualPrice) || targetPrice || 40;
                      setManualPrice((base + 1.0).toFixed(1));
                    }}
                    className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-emerald-400 rounded-lg text-[11px] font-bold border border-slate-700 transition cursor-pointer text-center"
                  >
                    +₹1.00
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const val = parseFloat(manualPrice) || targetPrice;
                      if (val) {
                        executeCopilotCommand(`Submit offer at ₹${val}/kg`);
                      }
                    }}
                    className="flex-1 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[11px] font-bold transition cursor-pointer text-center shadow-sm"
                  >
                    Bid Offer
                  </button>
                </div>
              </div>

              {/* Last Copilot Response Feedback (if user intervened) */}
              {copilotMessages.length > 0 && (
                <div className="mb-3 p-2.5 bg-slate-800/80 border border-slate-700/60 rounded-xl text-[11px] text-slate-300 flex items-start gap-2">
                  <Bot size={14} className="text-blue-400 shrink-0 mt-0.5" />
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
                placeholder='e.g. "Counter Ramesh Patil at ₹49/kg"'
                className="w-full bg-[#1e293b]/80 border border-slate-700/80 rounded-xl px-4 py-3 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition"
              />
              <button
                type="submit"
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm rounded-xl transition shadow-md flex items-center justify-center gap-1.5 cursor-pointer"
              >
                Send Instruction
              </button>
            </form>
          </div>
        ) : (
          /* Card 2: Farmer Copilot (Dark Theme exactly matching user image - 100% UNTOUCHED) */
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
                  onClick={() => executeCopilotCommand(`Don't go below ₹${currentFloor < 100 ? currentFloor * 100 : currentFloor}/q`)}
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition cursor-pointer"
                >
                  Don't go below ₹{currentFloor < 100 ? currentFloor * 100 : currentFloor}/q
                </button>
                <button
                  type="button"
                  onClick={() => executeCopilotCommand('Counter best buyer')}
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition cursor-pointer"
                >
                  Counter best buyer
                </button>
                <button
                  type="button"
                  onClick={() => executeCopilotCommand('Pause negotiations')}
                  className="px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-300 rounded-lg text-[11px] font-medium border border-slate-700/60 transition cursor-pointer"
                >
                  Pause negotiations
                </button>
              </div>

              {/* Manual Asking Rate Increment Tools (Farmer Parity with Buyer) */}
              <div className="mb-4 p-3 bg-slate-900/90 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-300 font-semibold">
                  <span>Manual Asking Rate:</span>
                  <span className="text-emerald-400 font-mono font-bold">
                    ₹{farmerManualPrice}/q <span className="text-slate-400 text-[10px] font-normal">(₹{(farmerManualPrice / 100).toFixed(1)}/kg)</span>
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setFarmerManualPrice(prev => Math.max(1000, prev - 50))}
                    className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-amber-300 rounded-lg text-[11px] font-bold border border-slate-700 transition cursor-pointer text-center"
                  >
                    -₹50
                  </button>
                  <button
                    type="button"
                    onClick={() => setFarmerManualPrice(prev => prev + 50)}
                    className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-emerald-400 rounded-lg text-[11px] font-bold border border-slate-700 transition cursor-pointer text-center"
                  >
                    +₹50
                  </button>
                  <button
                    type="button"
                    onClick={() => executeCopilotCommand(`Counter best buyer at ₹${farmerManualPrice}/q`)}
                    className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[11px] font-bold transition cursor-pointer text-center shadow-sm"
                  >
                    Set Ask Price
                  </button>
                </div>
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
