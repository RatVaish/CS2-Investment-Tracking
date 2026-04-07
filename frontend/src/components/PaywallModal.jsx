import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { paymentsAPI } from '../api/payments';
import toast from 'react-hot-toast';

const PRO_HIGHLIGHTS = [
  'Unlimited investments',
  'Price updates every 30 minutes',
  'Full price history charts',
  'Price alerts & notifications',
  'Steam inventory import',
];

export default function PaywallModal({ onClose }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async (priceId) => {
    setLoading(true);
    try {
      const { url } = await paymentsAPI.createCheckoutSession(priceId);
      window.location.href = url;
    } catch {
      toast.error('Failed to start checkout');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-gray-900 border border-gray-700 rounded-2xl p-8 max-w-md w-full shadow-2xl">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-gray-300 transition-colors">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="w-14 h-14 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <svg className="w-7 h-7 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>

        <h2 className="text-xl font-bold text-white text-center mb-1">Free tier limit reached</h2>
        <p className="text-gray-400 text-sm text-center mb-6">
          You've hit the 10 investment limit. Upgrade to Pro for unlimited tracking.
        </p>

        <ul className="space-y-2 mb-7">
          {PRO_HIGHLIGHTS.map(f => (
            <li key={f} className="flex items-center gap-2.5 text-sm text-gray-300">
              <svg className="w-4 h-4 text-cyan-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
              {f}
            </li>
          ))}
        </ul>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <button
            onClick={() => handleUpgrade(import.meta.env.VITE_STRIPE_MONTHLY_PRICE_ID)}
            disabled={loading}
            className="py-3 rounded-xl border border-gray-700 hover:border-cyan-500/50 text-white text-sm font-medium transition-all disabled:opacity-50 flex flex-col items-center gap-0.5"
          >
            <span className="text-lg font-bold">$6</span>
            <span className="text-gray-500 text-xs">/ month</span>
          </button>
          <button
            onClick={() => handleUpgrade(import.meta.env.VITE_STRIPE_ANNUAL_PRICE_ID)}
            disabled={loading}
            className="py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-gray-950 text-sm font-semibold transition-all disabled:opacity-50 flex flex-col items-center gap-0.5 relative"
          >
            <span className="absolute -top-2 left-1/2 -translate-x-1/2 text-[9px] px-2 py-0.5 bg-emerald-500 text-white rounded-full font-bold whitespace-nowrap">
              2 MONTHS FREE
            </span>
            <span className="text-lg font-bold">$50</span>
            <span className="text-gray-800 text-xs">/ year</span>
          </button>
        </div>

        <button
          onClick={() => { onClose(); navigate('/app/billing'); }}
          className="w-full text-center text-gray-500 hover:text-gray-300 text-xs transition-colors py-1"
        >
          See full plan comparison →
        </button>
      </div>
    </div>
  );
}
