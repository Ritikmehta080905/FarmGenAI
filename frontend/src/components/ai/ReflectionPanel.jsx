import React from 'react';
import { BrainCircuit, BookOpen, AlertOctagon, ArrowUpCircle } from 'lucide-react';

const mockReflections = [
    {
        id: 1,
        date: '2026-08-05',
        deal: '#NEG-8A92B',
        mistake: 'Offered too low initially (₹14/kg) for Grade A crop, causing opponent to walk away instantly.',
        lesson: 'For Grade A crops, initial offer must be at least 85% of market modal price to prevent immediate rejection.',
        policyUpdate: 'Updated BATNA generation logic for premium commodities.'
    },
    {
        id: 2,
        date: '2026-08-06',
        deal: '#NEG-99C12',
        mistake: 'Ignored impending heavy rainfall alert during transport negotiation.',
        lesson: 'Weather API alerts must increase transport urgency weight by 40% if rain probability > 80%.',
        policyUpdate: 'Modified Reward Function: High penalty for delayed transport during severe weather.'
    }
];

export default function ReflectionPanel() {
    return (
        <div className="space-y-6 animate-in fade-in duration-500">

            {/* Header Info */}
            <div className="bg-slate-900 rounded-2xl p-6 text-white shadow-sm flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-bold flex items-center gap-2"><BrainCircuit className="text-purple-400" /> Reflection Agent Core</h2>
                    <p className="text-slate-400 text-sm mt-1">Reviewing past negotiations to dynamically update the LangGraph prompt templates and RL policies.</p>
                </div>
                <div className="bg-slate-800 border border-slate-700 px-4 py-2 rounded-xl text-center">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Total Lessons Learned</p>
                    <p className="text-2xl font-black text-purple-400">1,248</p>
                </div>
            </div>

            {/* Timeline of Reflections */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2 border-b pb-4">
                    <BookOpen size={18} className="text-blue-500" /> Recent Strategy Updates
                </h3>

                <div className="space-y-8">
                    {mockReflections.map((ref) => (
                        <div key={ref.id} className="relative pl-6 border-l-2 border-slate-100 pb-2">
                            <div className="absolute w-4 h-4 rounded-full bg-purple-500 border-4 border-white left-[-9px] top-0"></div>

                            <div className="flex justify-between items-start mb-2">
                                <span className="text-xs font-bold text-slate-400 bg-slate-50 px-2 py-1 rounded">{ref.date} | Deal {ref.deal}</span>
                            </div>

                            <div className="space-y-3 mt-3">
                                <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex gap-3">
                                    <AlertOctagon size={16} className="text-red-500 shrink-0 mt-0.5" />
                                    <div>
                                        <p className="text-xs font-bold text-red-700 uppercase tracking-wider mb-1">Mistake Identified</p>
                                        <p className="text-sm text-slate-700">{ref.mistake}</p>
                                    </div>
                                </div>

                                <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl flex gap-3">
                                    <BookOpen size={16} className="text-blue-500 shrink-0 mt-0.5" />
                                    <div>
                                        <p className="text-xs font-bold text-blue-700 uppercase tracking-wider mb-1">Lesson Derived</p>
                                        <p className="text-sm text-slate-700">{ref.lesson}</p>
                                    </div>
                                </div>

                                <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-xl flex gap-3">
                                    <ArrowUpCircle size={16} className="text-emerald-500 shrink-0 mt-0.5" />
                                    <div>
                                        <p className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-1">System Policy Update Applied</p>
                                        <p className="text-sm text-slate-700 font-medium">{ref.policyUpdate}</p>
                                    </div>
                                </div>
                            </div>

                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
