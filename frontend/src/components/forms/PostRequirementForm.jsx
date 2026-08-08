import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { requirementSchema } from '../../utils/validation';
import { X, Target, Loader2 } from 'lucide-react';
import { api } from '../../services/api';
import { useNotification } from '../../contexts/NotificationContext';

export default function PostRequirementForm({ isOpen, onClose, onSuccess }) {
  const { addNotification } = useNotification();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm({
    resolver: zodResolver(requirementSchema),
    defaultValues: {
      quality: 'ANY',
      storageRequired: false,
      transportRequired: true,
    }
  });

  if (!isOpen) return null;

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      await api.post('/requirements', data);
      addNotification('success', 'Requirement posted. AI is searching for matches.');
      reset();
      onSuccess?.();
      onClose();
    } catch (err) {
      addNotification('error', err.response?.data?.detail || 'Failed to post requirement');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-xl overflow-hidden max-h-[90vh] flex flex-col animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 sticky top-0 z-10">
          <h3 className="font-bold text-slate-700 flex items-center gap-2">
            <Target size={18} className="text-blue-600" /> Post Procurement Requirement
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition">
            <X size={20} />
          </button>
        </div>
        
        {/* Scrollable Form Body */}
        <div className="overflow-y-auto flex-1 p-6">
          <form id="req-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            
            {/* 1. Basic Details */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-800 border-b pb-2">1. Commodity Needs</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Crop Name *</label>
                  <input 
                    {...register('crop')}
                    placeholder="e.g. Onions"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm"
                  />
                  {errors.crop && <p className="text-xs text-red-500 mt-1">{errors.crop.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Quality Grade</label>
                  <select {...register('quality')} className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-blue-500">
                    <option value="ANY">Any Grade</option>
                    <option value="A">Grade A (Premium Only)</option>
                    <option value="B">Grade B (Standard)</option>
                    <option value="C">Grade C (Processing)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* 2. Constraints */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-800 border-b pb-2">2. Budget & Volume</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Required Volume (kg) *</label>
                  <input 
                    type="number"
                    {...register('quantity', { valueAsNumber: true })}
                    placeholder="e.g. 5000"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm"
                  />
                  {errors.quantity && <p className="text-xs text-red-500 mt-1">{errors.quantity.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Max Budget (₹/kg) *</label>
                  <input 
                    type="number" step="0.5"
                    {...register('maxBudget', { valueAsNumber: true })}
                    placeholder="e.g. 18.50"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm"
                  />
                  {errors.maxBudget && <p className="text-xs text-red-500 mt-1">{errors.maxBudget.message}</p>}
                </div>
              </div>
            </div>

            {/* 3. Logistics */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-800 border-b pb-2">3. Logistics</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Preferred Location</label>
                  <input 
                    {...register('preferredLocation')}
                    placeholder="e.g. Nashik District"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm"
                  />
                  {errors.preferredLocation && <p className="text-xs text-red-500 mt-1">{errors.preferredLocation.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Delivery Deadline *</label>
                  <input 
                    type="date"
                    {...register('deliveryDate')}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm"
                  />
                  {errors.deliveryDate && <p className="text-xs text-red-500 mt-1">{errors.deliveryDate.message}</p>}
                </div>
              </div>
              
              <div className="flex gap-4 items-center">
                <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                  <input type="checkbox" {...register('transportRequired')} className="rounded text-blue-600 focus:ring-blue-500" />
                  Require Logistics Setup
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                  <input type="checkbox" {...register('storageRequired')} className="rounded text-blue-600 focus:ring-blue-500" />
                  Require Cold Storage
                </label>
              </div>
            </div>

          </form>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-100 flex gap-3 bg-white sticky bottom-0 z-10">
          <button type="button" onClick={onClose} className="flex-1 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition">
            Cancel
          </button>
          <button 
            type="submit" 
            form="req-form"
            disabled={isSubmitting} 
            className="flex-1 py-2.5 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold rounded-xl transition shadow-sm"
          >
            {isSubmitting ? <><Loader2 size={18} className="animate-spin" /> Submitting...</> : 'Find Matches'}
          </button>
        </div>

      </div>
    </div>
  );
}
