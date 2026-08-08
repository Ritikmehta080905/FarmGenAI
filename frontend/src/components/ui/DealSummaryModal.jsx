import React, { useState } from 'react';
import { Star, CheckCircle, XCircle, TrendingUp, Briefcase } from 'lucide-react';
import { api } from '../../services/api';

export default function DealSummaryModal({ isOpen, status, negotiationId, onClose }) {
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const isSuccess = status === 'COMPLETED';

  const handleSubmitRLFeedback = async () => {
    setIsSubmitting(true);
    try {
      const token = localStorage.getItem('agri_token');
      if (token !== 'mock_token') {
        await api.post(`/negotiations/${negotiationId}/feedback`, { rating, feedback });
      }
      setSubmitted(true);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className={`p-6 text-white text-center ${isSuccess ? 'bg-emerald-600' : 'bg-red-600'}`}>
          <div className="flex justify-center mb-4">
            {isSuccess ? <CheckCircle size={48} className="text-emerald-200"/> : <XCircle size={48} className="text-red-200"/>}
          </div>
          <h2 className="text-2xl font-bold">{isSuccess ? 'Deal Successfully Closed!' : 'Negotiation Failed'}</h2>
          <p className="text-sm opacity-90 mt-1">
            {isSuccess ? 'Both parties have accepted the digital contract.' : 'The negotiation was aborted.'}
          </p>
        </div>

        {/* AI Reflection Summary */}
        <div className="p-6 bg-slate-50 border-b border-slate-100">
          <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3">AI Reflection Summary</h3>
          <div className="space-y-2 text-sm text-slate-600">
            <p className="flex items-start gap-2">
              <TrendingUp size={16} className="text-blue-500 mt-0.5 shrink-0"/> 
              <span><strong>Strategy:</strong> The AI aggressively countered below ₹21 due to the incoming storm risk.</span>
            </p>
            <p className="flex items-start gap-2">
              <Briefcase size={16} className="text-purple-500 mt-0.5 shrink-0"/> 
              <span><strong>Market Impact:</strong> Secured a price 5% above the Agmarknet modal average.</span>
            </p>
          </div>
        </div>

        {/* Reinforcement Learning Feedback Form */}
        <div className="p-6">
          {submitted ? (
            <div className="text-center py-4">
              <CheckCircle size={32} className="text-emerald-500 mx-auto mb-2" />
              <p className="font-bold text-slate-800">Feedback Submitted!</p>
              <p className="text-sm text-slate-500">The AI model has updated its policies based on your rating.</p>
              <button onClick={onClose} className="mt-4 w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-lg transition">
                Return to Dashboard
              </button>
            </div>
          ) : (
            <>
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3">Train Your AI</h3>
              <p className="text-xs text-slate-500 mb-4">Rate the AI's performance. Your feedback directly impacts the Reinforcement Learning policy weights for future trades.</p>
              
              <div className="flex justify-center gap-2 mb-4">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button key={star} onClick={() => setRating(star)} className="focus:outline-none hover:scale-110 transition-transform">
                    <Star size={32} className={rating >= star ? 'fill-yellow-400 text-yellow-400' : 'text-slate-300'} />
                  </button>
                ))}
              </div>

              <textarea 
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Optional: What could the AI have done better?"
                className="w-full text-sm p-3 border border-slate-200 rounded-lg focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 mb-4 h-24 resize-none"
              ></textarea>

              <div className="flex gap-3">
                <button onClick={onClose} className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-lg transition">
                  Skip
                </button>
                <button 
                  onClick={handleSubmitRLFeedback}
                  disabled={rating === 0 || isSubmitting}
                  className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold rounded-lg transition"
                >
                  {isSubmitting ? 'Training AI...' : 'Submit Feedback'}
                </button>
              </div>
            </>
          )}
        </div>

      </div>
    </div>
  );
}
