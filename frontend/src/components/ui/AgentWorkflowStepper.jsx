import React from 'react';
import { Network, BrainCircuit, Search, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function AgentWorkflowStepper({ activeAgent }) {
    const steps = [
        { id: 'Planner', icon: <Network size={16} />, label: 'Planning' },
        { id: 'Market Intel', icon: <Search size={16} />, label: 'Intelligence' },
        { id: 'Negotiator', icon: <BrainCircuit size={16} />, label: 'Negotiation' },
        { id: 'Validator', icon: <ShieldCheck size={16} />, label: 'Validation' }
    ];

    // Helper to determine step status
    const getStepStatus = (stepId) => {
        if (!activeAgent) return 'pending';

        const activeIndex = steps.findIndex(s => activeAgent.includes(s.id));
        const currentIndex = steps.findIndex(s => s.id === stepId);

        if (activeIndex === -1) {
            // If agent not in list, assume completed or idle
            return 'completed';
        }

        if (currentIndex < activeIndex) return 'completed';
        if (currentIndex === activeIndex) return 'active';
        return 'pending';
    };

    return (
        <div className="w-full bg-slate-900 rounded-xl p-4 shadow-inner mb-6 border border-slate-800">
            <div className="flex justify-between items-center relative">
                {/* Connecting Line */}
                <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-800 -z-10 -translate-y-1/2"></div>

                {steps.map((step, idx) => {
                    const status = getStepStatus(step.id);

                    return (
                        <div key={idx} className="flex flex-col items-center bg-slate-900 px-2 relative z-10">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${status === 'completed' ? 'bg-emerald-500 text-slate-900' :
                                    status === 'active' ? 'bg-blue-500 text-white animate-pulse ring-4 ring-blue-500/30' :
                                        'bg-slate-800 text-slate-500 border border-slate-700'
                                }`}>
                                {status === 'completed' ? <CheckCircle2 size={16} /> : step.icon}
                            </div>
                            <span className={`text-[10px] uppercase font-bold mt-2 tracking-wider ${status === 'active' ? 'text-blue-400' :
                                    status === 'completed' ? 'text-emerald-500' :
                                        'text-slate-500'
                                }`}>
                                {step.label}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
