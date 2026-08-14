import React, { useState, useEffect } from 'react';
import { Download, Eye, FileText, CheckCircle2, Truck, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '@/services/api';

const MOCK_TRANSACTIONS = [
  {
    id: 'TXN-9021',
    date: '2026-08-07',
    crop: 'Organic Tomato (Grade A)',
    farmer: 'Green Farms',
    buyer: 'AgriProcure Ltd',
    quantity: '500 kg',
    price: '₹24/kg',
    total: '₹12,000',
    status: 'completed',
    workflow: 'Complete Supply Chain'
  },
  {
    id: 'TXN-9020',
    date: '2026-08-06',
    crop: 'Red Onion (Grade B)',
    farmer: 'Nashik Growers',
    buyer: 'FreshMart',
    quantity: '2000 kg',
    price: '₹18/kg',
    total: '₹36,000',
    status: 'in_transit',
    workflow: 'Direct + Transport'
  },
  {
    id: 'TXN-9019',
    date: '2026-08-05',
    crop: 'Potato (Grade A)',
    farmer: 'AgriCorp',
    buyer: 'FoodCo',
    quantity: '1000 kg',
    price: '₹14/kg',
    total: '₹14,000',
    status: 'disputed',
    workflow: 'Direct Sale'
  }
];

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState(MOCK_TRANSACTIONS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchTransactions() {
      try {
        setLoading(true);
        const res = await api.get('/analytics/history');
        if (res.data && res.data.length > 0) {
          const mapped = res.data.map((item, idx) => ({
            id: item.negotiation_id ? `TXN-${item.negotiation_id.slice(-4).toUpperCase()}` : `TXN-${9000 + idx}`,
            date: item.created_at ? item.created_at.slice(0, 10) : '2026-08-14',
            crop: item.crop || 'Produce',
            farmer: item.farmer || 'Farmer',
            buyer: item.buyer || item.selected_buyer || 'Wholesale Buyer',
            quantity: `${item.quantity || 0} kg`,
            price: `₹${item.final_price || item.price || 0}/kg`,
            total: `₹${((item.quantity || 0) * (item.final_price || item.price || 0)).toLocaleString()}`,
            status: item.status === 'DEAL' ? 'completed' : 'in_transit',
            workflow: 'Direct Supply Chain'
          }));
          setTransactions(mapped);
        }
      } catch (err) {
        console.warn('Using transaction fallback data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchTransactions();
  }, []);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800"><CheckCircle2 className="w-3 h-3 mr-1"/> Completed</span>;
      case 'in_transit':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"><Truck className="w-3 h-3 mr-1"/> In Transit</span>;
      case 'disputed':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"><ShieldAlert className="w-3 h-3 mr-1"/> Disputed</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      
      {/* Header */}
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Transaction History</h1>
          <p className="text-slate-500 mt-1">View completed agreements and download invoices.</p>
        </div>
        <button className="bg-emerald-50 text-emerald-700 px-4 py-2 rounded-lg font-medium hover:bg-emerald-100 border border-emerald-200 transition-colors flex items-center">
          <Download className="w-4 h-4 mr-2" /> Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Transaction ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Details
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Participants
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Amount
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {transactions.map((txn) => (
                <tr key={txn.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-slate-900">{txn.id}</div>
                    <div className="text-sm text-slate-500">{txn.date}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-slate-900">{txn.crop}</div>
                    <div className="text-sm text-slate-500">{txn.quantity} @ {txn.price}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-slate-900"><strong>F:</strong> {txn.farmer}</div>
                    <div className="text-sm text-slate-900"><strong>B:</strong> {txn.buyer}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-emerald-600">{txn.total}</div>
                    <div className="text-xs text-slate-500">{txn.workflow}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(txn.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-3">
                      <Link to={`/deal/${txn.id.split('-')[1]}/track`} className="text-slate-400 hover:text-emerald-600 tooltip-trigger" title="Track Workflow">
                        <Eye className="w-5 h-5" />
                      </Link>
                      <button className="text-slate-400 hover:text-blue-600 tooltip-trigger" title="Download Receipt">
                        <FileText className="w-5 h-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
