import React from 'react';
import { CheckCircle2, Circle, Clock, Truck, Warehouse, Landmark, MapPin } from 'lucide-react';

export default function TrackingTimeline({ currentStep }) {
    const steps = [
        { id: 'AGREEMENT', label: 'Agreement Signed', icon: <CheckCircle2 size={16} /> },
        { id: 'WAREHOUSE_RESERVED', label: 'Warehouse Reserved', icon: <Warehouse size={16} /> },
        { id: 'TRANSPORT_ASSIGNED', label: 'Transport Assigned', icon: <Truck size={16} /> },
        { id: 'PICKUP_COMPLETED', label: 'In Transit', icon: <MapPin size={16} /> },
        { id: 'DELIVERY_COMPLETED', label: 'Delivered', icon: <CheckCircle2 size={16} /> },
        { id: 'PAYMENT_RELEASED', label: 'Escrow Released', icon: <Landmark size={16} /> },
    ];

    const currentIndex = steps.findIndex(s => s.id === currentStep);

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h3 className="font-bold text-slate-800 mb-6">Execution Progress</h3>

            <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-100"></div>

                <div className="space-y-6">
                    {steps.map((step, index) => {
                        const isCompleted = index <= currentIndex;
                        const isCurrent = index === currentIndex;
                        const isFuture = index > currentIndex;

                        return (
                            <div key={step.id} className="relative flex items-center gap-4">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center z-10 transition-colors ${isCompleted ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/20' :
                                        'bg-white border-2 border-slate-200 text-slate-300'
                                    }`}>
                                    {isCompleted ? step.icon : (isCurrent ? <Clock size={16} className="animate-spin text-blue-500" /> : <Circle size={10} />)}
                                </div>

                                <div className="flex-1">
                                    <h4 className={`font-bold text-sm ${isCompleted ? 'text-slate-800' : 'text-slate-400'}`}>
                                        {step.label}
                                    </h4>
                                    {isCurrent && (
                                        <p className="text-xs font-medium text-emerald-600 mt-0.5 animate-pulse">Processing...</p>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
