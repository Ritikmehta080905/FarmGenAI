import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { User, MapPin, Building, Phone, Mail, Save, ShieldCheck } from 'lucide-react';

export default function UserProfile() {
  const { user } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  
  // Mock initial state based on user role
  const [formData, setFormData] = useState({
    fullName: user?.name || '',
    email: user?.name ? `${user.name.toLowerCase().replace(' ', '.')}@example.com` : '',
    phone: '+91 98765 43210',
    companyName: user?.role === 'buyer' ? 'AgriProcure Ltd.' : 'Green Farms',
    location: 'Nashik, Maharashtra',
    gstin: '27AABCU9603R1ZM'
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsSaving(true);
    // Simulate API save
    setTimeout(() => {
      setIsSaving(false);
      setSuccessMsg('Profile updated successfully!');
      setTimeout(() => setSuccessMsg(''), 3000);
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-slide-up">
      
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex items-center space-x-6">
        <div className="bg-emerald-100 w-24 h-24 rounded-full flex items-center justify-center border-4 border-white shadow-md">
          <User className="h-12 w-12 text-emerald-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{formData.fullName}</h1>
          <p className="text-slate-500 flex items-center mt-1">
            <ShieldCheck className="w-4 h-4 mr-1 text-emerald-600" /> 
            Verified {user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'User'}
          </p>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
          <h2 className="text-lg font-bold text-slate-900">Personal & Business Information</h2>
          {successMsg && (
            <span className="text-sm font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
              {successMsg}
            </span>
          )}
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <div className="space-y-2">
              <label className="flex items-center text-sm font-medium text-slate-700">
                <User className="w-4 h-4 mr-2 text-slate-400" /> Full Name
              </label>
              <input 
                type="text" 
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500" 
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center text-sm font-medium text-slate-700">
                <Mail className="w-4 h-4 mr-2 text-slate-400" /> Email Address
              </label>
              <input 
                type="email" 
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500" 
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center text-sm font-medium text-slate-700">
                <Phone className="w-4 h-4 mr-2 text-slate-400" /> Phone Number
              </label>
              <input 
                type="text" 
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500" 
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center text-sm font-medium text-slate-700">
                <MapPin className="w-4 h-4 mr-2 text-slate-400" /> Location / Address
              </label>
              <input 
                type="text" 
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500" 
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center text-sm font-medium text-slate-700">
                <Building className="w-4 h-4 mr-2 text-slate-400" /> Company / Farm Name
              </label>
              <input 
                type="text" 
                name="companyName"
                value={formData.companyName}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500" 
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center text-sm font-medium text-slate-700">
                <ShieldCheck className="w-4 h-4 mr-2 text-slate-400" /> GSTIN / Tax ID
              </label>
              <input 
                type="text" 
                name="gstin"
                value={formData.gstin}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 bg-slate-50"
                readOnly 
              />
              <p className="text-xs text-slate-500">Contact admin to change tax identifier.</p>
            </div>

          </div>

          <div className="pt-6 border-t border-slate-200 flex justify-end">
            <button 
              type="submit"
              disabled={isSaving}
              className="bg-emerald-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-emerald-700 transition-colors flex items-center disabled:opacity-70"
            >
              {isSaving ? (
                'Saving...'
              ) : (
                <><Save className="w-4 h-4 mr-2" /> Save Changes</>
              )}
            </button>
          </div>
        </form>
      </div>

    </div>
  );
}
