import React from 'react';
import { MapPin, Navigation } from 'lucide-react';

export default function DeliveryMap({ status }) {
    // A lightweight UI abstraction of a map to prevent bloating the bundle with leaflet before backend mapping is ready
    return (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden flex flex-col h-full">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                <h3 className="font-bold text-slate-700 flex items-center gap-2">
                    <Navigation size={18} className="text-blue-600" /> Live Route Tracking
                </h3>
                <span className="text-xs font-bold text-emerald-600 px-2 py-1 bg-emerald-100 rounded-lg animate-pulse">
                    GPS Active
                </span>
            </div>

            {/* Map Simulation Container */}
            <div className="flex-1 bg-slate-200 relative min-h-[300px] flex items-center justify-center overflow-hidden">

                {/* Fake Grid Background */}
                <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(#475569 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>

                {/* Route Line */}
                <div className="absolute left-1/4 right-1/4 h-1.5 bg-blue-300 rounded-full top-1/2 -translate-y-1/2">
                    <div className={`h-full bg-blue-600 rounded-full transition-all duration-1000 ${status === 'DELIVERY_COMPLETED' ? 'w-full' :
                            status === 'PICKUP_COMPLETED' ? 'w-1/2' : 'w-0'
                        }`}></div>
                </div>

                {/* Nodes */}
                <div className="absolute left-1/4 top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center">
                    <div className="w-6 h-6 bg-emerald-500 rounded-full border-4 border-white shadow-md z-10"></div>
                    <span className="mt-2 text-xs font-bold text-slate-700 bg-white/80 px-2 rounded backdrop-blur">Farm (Nashik)</span>
                </div>

                <div className="absolute left-1/2 top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center">
                    <div className="w-5 h-5 bg-purple-500 rounded-full border-4 border-white shadow-md z-10"></div>
                    <span className="mt-2 text-xs font-bold text-slate-700 bg-white/80 px-2 rounded backdrop-blur">Cold Storage</span>
                </div>

                <div className="absolute right-1/4 top-1/2 -translate-y-1/2 translate-x-1/2 flex flex-col items-center">
                    <div className="w-6 h-6 bg-blue-500 rounded-full border-4 border-white shadow-md z-10"></div>
                    <span className="mt-2 text-xs font-bold text-slate-700 bg-white/80 px-2 rounded backdrop-blur">Buyer (Mumbai)</span>
                </div>

                {/* Live Vehicle Marker */}
                {status === 'PICKUP_COMPLETED' && (
                    <div className="absolute left-1/2 top-1/2 -translate-y-1/2 -translate-x-1/2 z-20 animate-bounce">
                        <div className="bg-slate-800 text-white p-1.5 rounded-full shadow-xl">
                            <MapPin size={20} fill="#10b981" />
                        </div>
                    </div>
                )}
            </div>

        </div>
    );
}
