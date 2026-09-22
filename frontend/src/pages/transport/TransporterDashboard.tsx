import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { useQuery } from '@tanstack/react-query';
import { Truck, MapPin, Clock, Plus, CheckCircle, XCircle, ThermometerSnowflake, Fuel } from 'lucide-react';

export default function TransporterDashboard() {
  const { user } = useAuth();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form State
  const [vehicleName, setVehicleName] = useState('');
  const [vehicleType, setVehicleType] = useState('Medium Truck');
  const [capacityKg, setCapacityKg] = useState(5000);
  const [fuelType, setFuelType] = useState('Diesel');
  const [fuelEfficiency, setFuelEfficiency] = useState(8);
  const [currentLocation, setCurrentLocation] = useState('Ahmednagar');
  const [registrationNumber, setRegistrationNumber] = useState('');
  const [driverName, setDriverName] = useState('');
  const [baseRate, setBaseRate] = useState<number | ''>('');
  const [suggestedRate, setSuggestedRate] = useState<number | null>(null);
  const [fuelPrice, setFuelPrice] = useState<number | null>(null);
  const [refrigerated, setRefrigerated] = useState(false);
  const [tempMin, setTempMin] = useState<number | ''>('');
  const [tempMax, setTempMax] = useState<number | ''>('');

  React.useEffect(() => {
    if (isFormOpen && currentLocation && fuelType && fuelEfficiency) {
      const fetchEstimate = async () => {
        try {
          const res = await api.get('/transport/fuel-estimate', {
            params: {
              fuel_type: fuelType,
              location: currentLocation,
              efficiency_kmpl: fuelEfficiency,
              capacity_kg: capacityKg,
              vehicle_type: vehicleType
            }
          });
          if (res.data?.success) {
            setSuggestedRate(res.data.suggested_rate_per_km);
            setFuelPrice(res.data.fuel_price);
            if (baseRate === '') {
              setBaseRate(res.data.suggested_rate_per_km);
            }
          }
        } catch (e) {
          console.error("Failed to fetch fuel estimate", e);
        }
      };
      const debounce = setTimeout(fetchEstimate, 500);
      return () => clearTimeout(debounce);
    }
  }, [fuelType, currentLocation, fuelEfficiency, capacityKg, vehicleType, isFormOpen]);

  const { data: myVehicles, isLoading: loadingVehicles, refetch } = useQuery({
    queryKey: ['my_vehicles'],
    queryFn: async () => {
      const res = await api.get('/transport/vehicles/me');
      return res.data?.data || [];
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/transport/vehicles', {
        vehicle_type: vehicleType,
        vehicle_name: vehicleName,
        registration_number: registrationNumber,
        driver_name: driverName,
        base_rate_per_km: Number(baseRate),
        capacity_kg: Number(capacityKg),
        fuel_type: fuelType,
        fuel_efficiency_kmpl: Number(fuelEfficiency),
        current_location: currentLocation,
        refrigerated: refrigerated,
        temperature_min_c: tempMin === '' ? null : Number(tempMin),
        temperature_max_c: tempMax === '' ? null : Number(tempMax)
      });
      setIsFormOpen(false);
      refetch();
      // Reset form
      setVehicleName('');
      setRegistrationNumber('');
      setDriverName('');
      setBaseRate('');
      setCapacityKg(5000);
      setRefrigerated(false);
    } catch (err) {
      console.error(err);
      alert('Failed to register vehicle');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full pl-3 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition shadow-sm text-sm text-slate-900";
  const labelClass = "block text-xs font-bold text-slate-700 mb-1";

  const isRateValid = baseRate !== '' && suggestedRate !== null && 
                      Number(baseRate) >= suggestedRate * 0.8 && 
                      Number(baseRate) <= suggestedRate * 1.2;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Transporter Dashboard</h1>
          <p className="text-slate-500 mt-1">Manage your fleet and incoming transport bookings.</p>
        </div>
        <button
          onClick={() => setIsFormOpen(true)}
          className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition shadow-sm"
        >
          <Plus size={16} /> Add Vehicle
        </button>
      </div>

      {isFormOpen && (
        <div className="bg-white p-6 rounded-2xl shadow-lg border border-amber-200 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <Truck size={20} className="text-amber-500" /> Register New Vehicle
            </h2>
            <button onClick={() => setIsFormOpen(false)} className="text-slate-400 hover:text-slate-600">
              <XCircle size={24} />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className={labelClass}>Vehicle Name / Model</label>
              <input type="text" required value={vehicleName} onChange={e => setVehicleName(e.target.value)} className={inputClass} placeholder="e.g. Tata Ace Gold" />
            </div>
            <div>
              <label className={labelClass}>Registration Number (Number Plate)</label>
              <input type="text" required value={registrationNumber} onChange={e => setRegistrationNumber(e.target.value)} className={inputClass} placeholder="e.g. MH 12 AB 1234" />
            </div>
            <div>
              <label className={labelClass}>Driver Name</label>
              <input type="text" required value={driverName} onChange={e => setDriverName(e.target.value)} className={inputClass} placeholder="e.g. Ramesh Kumar" />
            </div>
            <div>
              <label className={labelClass}>Vehicle Type</label>
              <select value={vehicleType} onChange={e => setVehicleType(e.target.value)} className={inputClass}>
                <option>Mini Truck</option>
                <option>Medium Truck</option>
                <option>Heavy Truck</option>
                <option>Refrigerated Truck</option>
                <option>Tractor + Trailer</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Capacity (kg)</label>
              <input type="number" required value={capacityKg} onChange={e => setCapacityKg(Number(e.target.value))} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Current Location</label>
              <input type="text" required value={currentLocation} onChange={e => setCurrentLocation(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Fuel Type</label>
              <select value={fuelType} onChange={e => setFuelType(e.target.value)} className={inputClass}>
                <option>Diesel</option>
                <option>Petrol</option>
                <option>CNG</option>
                <option>EV</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Fuel Efficiency (km/l)</label>
              <input type="number" step="0.1" required value={fuelEfficiency} onChange={e => setFuelEfficiency(Number(e.target.value))} className={inputClass} />
            </div>
            <div className="md:col-span-3 bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col sm:flex-row gap-6 items-start sm:items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Fuel size={16} className="text-amber-500" /> Live Rate Estimator
                </h4>
                <p className="text-xs text-slate-500 mt-1">Based on live {fuelType} prices in {currentLocation} (₹{fuelPrice || '...'} / L)</p>
              </div>
              <div className="flex-1 flex gap-4 w-full">
                <div className="flex-1">
                  <label className={labelClass}>AI Suggested Base Rate (₹/km)</label>
                  <div className="w-full pl-3 pr-4 py-2 bg-slate-100 border border-slate-200 rounded-lg text-sm text-slate-500 font-mono">
                    {suggestedRate ? `₹${suggestedRate}` : 'Calculating...'}
                  </div>
                </div>
                <div className="flex-1">
                  <label className={labelClass}>Your Manual Base Rate (₹/km)</label>
                  <input 
                    type="number" 
                    step="0.1" 
                    required 
                    value={baseRate} 
                    onChange={e => setBaseRate(e.target.value === '' ? '' : Number(e.target.value))} 
                    className={`${inputClass} ${baseRate !== '' && !isRateValid ? 'border-rose-500 ring-rose-500 focus:ring-rose-500' : ''}`} 
                  />
                  {baseRate !== '' && !isRateValid && (
                    <p className="text-[10px] text-rose-500 font-bold mt-1">Rate must be within ±20% of AI suggestion (₹{(suggestedRate || 0)*0.8} - ₹{(suggestedRate || 0)*1.2})</p>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center mt-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={refrigerated} onChange={e => setRefrigerated(e.target.checked)} className="rounded text-amber-600 focus:ring-amber-500" />
                <span className="text-sm font-semibold text-slate-700">Refrigerated (Cold Chain)</span>
              </label>
            </div>
            {refrigerated && (
              <>
                <div>
                  <label className={labelClass}>Min Temp (°C)</label>
                  <input type="number" value={tempMin} onChange={e => setTempMin(e.target.value === '' ? '' : Number(e.target.value))} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Max Temp (°C)</label>
                  <input type="number" value={tempMax} onChange={e => setTempMax(e.target.value === '' ? '' : Number(e.target.value))} className={inputClass} />
                </div>
              </>
            )}
            <div className="md:col-span-3 flex justify-end mt-2">
              <button disabled={loading || !isRateValid} type="submit" className="bg-amber-600 hover:bg-amber-700 text-white px-6 py-2 rounded-lg font-bold disabled:opacity-50 transition">
                {loading ? 'Saving...' : 'Save Vehicle'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-5 border-b border-slate-100 bg-slate-50">
          <h2 className="font-bold text-lg text-slate-800">My Fleet</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-white text-slate-500 border-b border-slate-100">
              <tr>
                <th className="px-5 py-3 font-medium">Vehicle</th>
                <th className="px-5 py-3 font-medium">Type</th>
                <th className="px-5 py-3 font-medium">Capacity</th>
                <th className="px-5 py-3 font-medium">Est. Base Rate</th>
                <th className="px-5 py-3 font-medium">Floor Price</th>
                <th className="px-5 py-3 font-medium">Location</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loadingVehicles ? (
                <tr><td colSpan={5} className="p-8 text-center text-slate-400">Loading your fleet...</td></tr>
              ) : !myVehicles || myVehicles.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-slate-400">
                    <Truck size={48} className="mx-auto mb-4 opacity-20" />
                    <p className="text-lg font-medium">You haven't added any vehicles yet.</p>
                    <p className="mt-1">Click "Add Vehicle" to list your fleet and start getting bookings.</p>
                  </td>
                </tr>
              ) : (
                myVehicles.map((v: any, i: number) => (
                  <tr key={i} className="hover:bg-slate-50/50 transition">
                    <td className="px-5 py-4">
                      <div className="font-bold text-slate-800">{v.vehicle_name}</div>
                      <div className="text-xs text-slate-500">ID: {v.vehicle_id}</div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-700">{v.vehicle_type}</span>
                        {v.refrigerated && <ThermometerSnowflake size={14} className="text-blue-500" title="Refrigerated" />}
                      </div>
                    </td>
                    <td className="px-5 py-4 font-medium text-amber-600">{v.capacity_kg} kg</td>
                    <td className="px-5 py-4 font-medium text-emerald-600">
                      {v.market_rate_per_km ? `₹${v.market_rate_per_km}/km` : 'N/A'}
                    </td>
                    <td className="px-5 py-4 font-medium text-rose-600">
                      {v.floor_price_per_km ? `₹${v.floor_price_per_km}/km` : 'N/A'}
                    </td>
                    <td className="px-5 py-4 text-slate-600 flex items-center gap-1">
                      <MapPin size={14} className="text-slate-400" /> {v.current_location}
                    </td>
                    <td className="px-5 py-4">
                      <span className={`px-2.5 py-1 text-xs rounded-full font-bold ${
                        v.status === 'AVAILABLE' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {v.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-5 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
          <h2 className="font-bold text-lg text-slate-800">Incoming Deals / Negotiations</h2>
        </div>
        <div className="p-12 text-center text-slate-400">
            <Clock size={48} className="mx-auto mb-4 opacity-20" />
            <p className="text-lg font-medium">No active negotiations right now.</p>
            <p className="mt-1">When stakeholders request transport, our AI agent will automatically negotiate on your behalf to maximize your profit.</p>
        </div>
      </div>
    </div>
  );
}
