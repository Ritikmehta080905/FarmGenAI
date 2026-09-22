import React, { useState } from 'react';
import { TruckIcon, MapPinIcon, CalendarDaysIcon, ClockIcon } from '@heroicons/react/24/outline';
import AutoNegotiationTracker from '@/components/transport/AutoNegotiationTracker';
import { api } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import TransporterDashboard from './TransporterDashboard';

function BookTransport() {
  const [isNegotiating, setIsNegotiating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  // Form State
  const [crop, setCrop] = useState('Tomato');
  const [quantityKg, setQuantityKg] = useState<number>(2000);
  const [pickupLocation, setPickupLocation] = useState('Ahmednagar');
  const [deliveryLocation, setDeliveryLocation] = useState('Pune');
  const [deadlineHours, setDeadlineHours] = useState<number>(12);
  const [shelfLifeHours, setShelfLifeHours] = useState<number>(24);
  const [refrigeratedRequired, setRefrigeratedRequired] = useState<boolean>(false);
  
  // Results
  const [negotiations, setNegotiations] = useState<any[]>([]);
  const [winner, setWinner] = useState<any>(null);
  
  // Route Estimate State
  const [routeEstimates, setRouteEstimates] = useState<any[]>([]);
  const [estimatingRoute, setEstimatingRoute] = useState(false);
  const [selectedRouteIdx, setSelectedRouteIdx] = useState<number | null>(null);
  const [manualFloorPrice, setManualFloorPrice] = useState<number | ''>('');

  // Debounced Route Fetching
  React.useEffect(() => {
    if (!pickupLocation || !deliveryLocation) return;
    
    const fetchEstimate = async () => {
      setEstimatingRoute(true);
      try {
        const res = await api.get('/transport/route-estimate', {
          params: {
            origin: pickupLocation,
            destination: deliveryLocation,
            quantity_kg: quantityKg,
            crop
          }
        });
        if (res.data?.success) {
          setRouteEstimates(res.data.routes);
          // Auto-select recommended route
          const recIdx = res.data.routes.findIndex((r: any) => r.is_recommended);
          if (recIdx !== -1) {
            setSelectedRouteIdx(recIdx);
            setManualFloorPrice(res.data.routes[recIdx].floor_price);
          }
        }
      } catch (err) {
        console.error("Failed to fetch route estimate", err);
      } finally {
        setEstimatingRoute(false);
      }
    };

    const timer = setTimeout(() => {
      fetchEstimate();
    }, 1000);

    return () => clearTimeout(timer);
  }, [pickupLocation, deliveryLocation, quantityKg, crop]);

  const handleAutoNegotiate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    
    try {
      const payload = {
        crop,
        quantity_kg: Number(quantityKg),
        pickup_location: pickupLocation,
        delivery_location: deliveryLocation,
        delivery_deadline_hours: Number(deadlineHours),
        shelf_life_hours: Number(shelfLifeHours),
        refrigerated_required: refrigeratedRequired,
        buyer_offer: manualFloorPrice ? Number(manualFloorPrice) : undefined,
      };

      if (selectedRouteIdx !== null && manualFloorPrice) {
        const suggestedFloor = routeEstimates[selectedRouteIdx].floor_price;
        if (Number(manualFloorPrice) > suggestedFloor * 1.5 || Number(manualFloorPrice) < suggestedFloor * 0.5) {
          setErrorMsg(`Please enter a realistic floor price. Suggested is ₹${suggestedFloor}.`);
          setLoading(false);
          return;
        }
      }

      const res = await api.post('/transport/vehicles/auto-negotiate', payload);
      
      if (res.data.success) {
        setNegotiations(res.data.data.all_negotiations);
        setWinner(res.data.data.winner);
        setIsNegotiating(true);
      } else {
        setErrorMsg(res.data.message || "Could not start auto-negotiation.");
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || "Network error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full pl-10 pr-4 py-3 bg-white/50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition shadow-sm backdrop-blur-sm text-slate-900";
  const labelClass = "block text-sm font-bold text-slate-700 mb-1.5";
  const iconClass = "absolute left-3 top-3.5 h-5 w-5 text-slate-400";

  return (
    <div className="min-h-screen bg-slate-50 pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        
        {!isNegotiating ? (
          <div className="animate-in fade-in duration-700 space-y-10">
            {/* Header Section */}
            <div className="text-center space-y-4 max-w-3xl mx-auto">
              <div className="inline-flex items-center justify-center p-4 bg-amber-100 rounded-full mb-4 shadow-inner">
                <TruckIcon className="h-12 w-12 text-amber-600" />
              </div>
              <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
                Book Transport, <span className="text-amber-600">Autonomously.</span>
              </h1>
              <p className="text-lg text-slate-600">
                Enter your shipment details below. Our Stakeholder Agent will instantly find the best vehicles and negotiate on your behalf in real-time to secure the lowest possible freight rate. No manual haggling required.
              </p>
            </div>

            {/* Input Form Card */}
            <div className="max-w-4xl mx-auto bg-white/70 backdrop-blur-xl rounded-3xl shadow-xl border border-white/50 overflow-hidden">
              <form onSubmit={handleAutoNegotiate} className="p-8 md:p-10">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  
                  {/* Column 1 */}
                  <div className="space-y-6">
                    <div>
                      <label className={labelClass}>What are you shipping?</label>
                      <div className="relative">
                        <TruckIcon className={iconClass} />
                        <input type="text" value={crop} onChange={e => setCrop(e.target.value)} required className={inputClass} placeholder="e.g. Tomato" />
                      </div>
                    </div>
                    
                    <div>
                      <label className={labelClass}>Pickup Location</label>
                      <div className="relative">
                        <MapPinIcon className={iconClass} />
                        <input type="text" value={pickupLocation} onChange={e => setPickupLocation(e.target.value)} required className={inputClass} placeholder="e.g. Ahmednagar" />
                      </div>
                    </div>

                    <div>
                      <label className={labelClass}>Delivery Deadline (Hours)</label>
                      <div className="relative">
                        <ClockIcon className={iconClass} />
                        <input type="number" min="1" value={deadlineHours} onChange={e => setDeadlineHours(Number(e.target.value))} required className={inputClass} />
                      </div>
                    </div>
                  </div>

                  {/* Column 2 */}
                  <div className="space-y-6">
                    <div>
                      <label className={labelClass}>Total Quantity (kg)</label>
                      <div className="relative">
                        <span className="absolute left-4 top-3.5 font-bold text-slate-400 text-sm">KG</span>
                        <input type="number" min="1" value={quantityKg} onChange={e => setQuantityKg(Number(e.target.value))} required className={`w-full pl-11 pr-4 py-3 bg-white/50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition shadow-sm backdrop-blur-sm text-slate-900`} />
                      </div>
                    </div>

                    <div>
                      <label className={labelClass}>Delivery Location</label>
                      <div className="relative">
                        <MapPinIcon className={iconClass} />
                        <input type="text" value={deliveryLocation} onChange={e => setDeliveryLocation(e.target.value)} required className={inputClass} placeholder="e.g. Pune" />
                      </div>
                    </div>

                    <div>
                      <label className={labelClass}>Product Shelf Life (Hours)</label>
                      <div className="relative">
                        <CalendarDaysIcon className={iconClass} />
                        <input type="number" min="1" value={shelfLifeHours} onChange={e => setShelfLifeHours(Number(e.target.value))} required className={inputClass} />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-8 pt-6 border-t border-slate-100 flex flex-col md:flex-row items-center justify-between gap-6">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className={`w-6 h-6 rounded flex items-center justify-center border-2 transition-colors ${refrigeratedRequired ? 'bg-blue-500 border-blue-500' : 'border-slate-300 group-hover:border-blue-400'}`}>
                      {refrigeratedRequired && <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                    </div>
                    <input type="checkbox" className="hidden" checked={refrigeratedRequired} onChange={e => setRefrigeratedRequired(e.target.checked)} />
                    <span className="font-semibold text-slate-700 select-none">Requires Refrigeration (Cold Chain)</span>
                  </label>

                  <button 
                    type="submit" 
                    disabled={loading || routeEstimates.length === 0}
                    className="w-full md:w-auto px-8 py-4 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white font-bold text-lg rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <><ClockIcon className="h-5 w-5 animate-spin" /> Agents Mobilizing...</>
                    ) : (
                      <>Find & Negotiate Best Deal</>
                    )}
                  </button>
                </div>
                
                {errorMsg && (
                  <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 font-medium text-sm text-center">
                    {errorMsg}
                  </div>
                )}
              </form>
              
              {/* Live Route Estimates Widget */}
              {(estimatingRoute || routeEstimates.length > 0) && (
                <div className="bg-slate-50 border-t border-slate-200 p-8">
                  <div className="flex items-center gap-2 mb-4">
                    <h3 className="text-lg font-bold text-slate-800">Live Route Analysis & Pricing Estimate</h3>
                    {estimatingRoute && <ClockIcon className="h-5 w-5 text-amber-500 animate-spin" />}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {routeEstimates.map((route, idx) => (
                      <div 
                        key={idx} 
                        onClick={() => {
                          setSelectedRouteIdx(idx);
                          setManualFloorPrice(route.floor_price);
                        }}
                        className={`relative p-4 rounded-xl border transition-all cursor-pointer ${
                        selectedRouteIdx === idx 
                          ? 'bg-amber-50 border-amber-400 shadow-md ring-2 ring-amber-500/30 transform scale-[1.02]' 
                          : 'bg-white border-slate-200 hover:border-amber-300 opacity-70 hover:opacity-100'
                      }`}>
                        {route.is_recommended && (
                          <div className="absolute -top-3 left-4 bg-amber-500 text-white text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full shadow-sm">
                            AI Recommended
                          </div>
                        )}
                        <h4 className="font-bold text-slate-800 text-sm mb-1">{route.name}</h4>
                        {route.route_path && (
                          <p className="text-[10px] font-mono text-slate-400 mb-3 overflow-hidden text-ellipsis whitespace-nowrap" title={route.route_path}>
                            {route.route_path}
                          </p>
                        )}
                        <div className="space-y-1 text-xs text-slate-600 mb-3">
                          <p className="flex justify-between"><span>Distance:</span> <span className="font-semibold">{route.distance_km} km</span></p>
                          <p className="flex justify-between"><span>Duration:</span> <span className="font-semibold">{route.duration_hours} hrs</span></p>
                        </div>
                        <div className="pt-3 border-t border-slate-200/60 space-y-1 text-xs text-slate-600 mb-3">
                          <p className="flex justify-between"><span>Est. Tolls:</span> <span className="text-rose-600 font-medium">₹{route.estimated_toll}</span></p>
                          <p className="flex justify-between"><span>Est. Fuel:</span> <span className="text-blue-600 font-medium">₹{route.estimated_fuel}</span></p>
                        </div>
                        <div className={`pt-3 border-t ${selectedRouteIdx === idx ? 'border-amber-200' : 'border-slate-200'} space-y-1`}>
                          <p className="flex justify-between text-xs items-center">
                            <span className="font-bold text-slate-700">Suggested Floor:</span> 
                            <span className="font-extrabold text-amber-600 text-sm">₹{route.floor_price}</span>
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {selectedRouteIdx !== null && (
                    <div className="mt-6 p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
                      <label className="block text-sm font-bold text-slate-700 mb-2">Set Your Custom Floor Price (₹)</label>
                      <p className="text-xs text-slate-500 mb-3">The AI will use this as the absolute maximum budget during negotiations. We recommend keeping it close to the suggested floor price.</p>
                      <div className="relative max-w-xs">
                        <span className="absolute left-4 top-3.5 font-bold text-slate-400 text-sm">₹</span>
                        <input 
                          type="number" 
                          value={manualFloorPrice} 
                          onChange={(e) => setManualFloorPrice(e.target.value ? Number(e.target.value) : '')}
                          className="w-full pl-8 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition shadow-sm text-slate-900 font-bold" 
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ) : (
          <AutoNegotiationTracker 
            negotiations={negotiations} 
            winner={winner} 
            onClose={() => setIsNegotiating(false)} 
          />
        )}
        
      </div>
    </div>
  );
}

export default function TransportDashboard() {
  const { user } = useAuth();
  
  if (user?.role === 'transport') {
    return <TransporterDashboard />;
  }
  
  return <BookTransport />;
}
