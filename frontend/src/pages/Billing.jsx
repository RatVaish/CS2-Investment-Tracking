import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { paymentsAPI } from '../api/payments';
import Navbar from '../components/Navbar';
import toast from 'react-hot-toast';

const MONTHLY_PRICE_ID = import.meta.env.VITE_STRIPE_MONTHLY_PRICE_ID;
const ANNUAL_PRICE_ID = import.meta.env.VITE_STRIPE_ANNUAL_PRICE_ID;

const PRO_FEATURES = [
  'Unlimited investments',
  'Price updates every 30 minutes',
  'Full price history charts',
  'Price alerts & notifications',
  'Spreadsheet import (CSV, Excel, TSV)',
  'CSV / Excel export',
  'Multi-currency support',
  'Priority support',
];

const FREE_FEATURES = [
  'Up to 10 investments',
  'Daily price updates',
  'Basic portfolio analytics',
  'Steam & Google login',
];

export default function Billing() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [billing, setBilling] = useState('monthly'); // 'monthly' | 'annual'
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const isPro = user?.tier === 'pro';

  useEffect(() => {
    // Handle Stripe redirect back
    if (searchParams.get('success') === 'true') {
      toast.success('Welcome to Floatbase Pro! 🎉');
      // Refresh immediately and again after a delay to catch webhook processing
      refreshUser();
      setTimeout(() => refreshUser(), 2000);
      setTimeout(() => refreshUser(), 5000);
    } else if (searchParams.get('canceled') === 'true') {
      toast('Checkout canceled — no charge was made.', { icon: 'ℹ️' });
    }

    paymentsAPI.getStatus()
      .then(setStatus)
      .catch(() => {});
  }, []);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const priceId = billing === 'monthly' ? MONTHLY_PRICE_ID : ANNUAL_PRICE_ID;
      const { url } = await paymentsAPI.createCheckoutSession(priceId);
      window.location.href = url;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start checkout');
      setLoading(false);
    }
  };

  const handleManageBilling = async () => {
    setLoading(true);
    try {
      const { url } = await paymentsAPI.getBillingPortal();
      window.location.href = url;
    } catch (err) {
      toast.error('Failed to open billing portal');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-5xl mx-auto px-6 pt-24 pb-16">

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-white mb-3">
            {isPro ? 'Your Subscription' : 'Upgrade to Pro'}
          </h1>
          <p className="text-gray-400 max-w-lg mx-auto">
            {isPro
              ? 'You have full access to all Floatbase Pro features.'
              : 'Unlock unlimited investments, faster updates, and advanced analytics.'}
          </p>
        </div>

        {isPro ? (
          /* ── Pro user view ── */
          <div className="max-w-md mx-auto">
            <div className="bg-gray-900 border border-cyan-500/30 rounded-2xl p-8 text-center">
              <div className="w-16 h-16 bg-cyan-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-white mb-1">Floatbase Pro</h2>
              <p className="text-gray-400 text-sm mb-2">
                Status: <span className={`font-medium ${
                  status?.subscription_status === 'active' ? 'text-emerald-400'
                  : status?.subscription_status === 'past_due' ? 'text-amber-400'
                  : 'text-gray-400'
                }`}>{status?.subscription_status || 'active'}</span>
              </p>

              {status?.subscription_status === 'past_due' && (
                <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400 text-sm">
                  Your last payment failed. Please update your payment method to keep Pro access.
                </div>
              )}

              <ul className="text-left space-y-2 mb-8 mt-6">
                {PRO_FEATURES.map(f => (
                  <li key={f} className="flex items-center gap-2.5 text-sm text-gray-300">
                    <svg className="w-4 h-4 text-cyan-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>

              <button
                onClick={handleManageBilling}
                disabled={loading}
                className="w-full py-3 rounded-xl border border-gray-700 text-gray-300 hover:bg-gray-800 transition-colors text-sm font-medium disabled:opacity-50"
              >
                {loading ? 'Opening portal...' : 'Manage Subscription'}
              </button>
            </div>
          </div>
        ) : (
          /* ── Free user — pricing cards ── */
          <>
            {/* Billing toggle */}
            <div className="flex items-center justify-center gap-4 mb-10">
              <div className="flex bg-gray-900 border border-gray-800 rounded-xl p-1 gap-1">
                <button
                  onClick={() => setBilling('monthly')}
                  className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                    billing === 'monthly'
                      ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20'
                      : 'text-gray-500 hover:text-gray-300'
                  }`}
                >
                  Monthly
                </button>
                <button
                  onClick={() => setBilling('annual')}
                  className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                    billing === 'annual'
                      ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20'
                      : 'text-gray-500 hover:text-gray-300'
                  }`}
                >
                  Annual
                  <span className="text-[10px] px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded font-semibold border border-emerald-500/20">
                    2 months free
                  </span>
                </button>
              </div>
            </div>

            {/* Cards */}
            <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">

              {/* Free card */}
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-7 flex flex-col">
                <div className="mb-6">
                  <h2 className="text-lg font-bold text-white mb-1">Free</h2>
                  <p className="text-gray-500 text-sm">For casual trackers</p>
                  <div className="mt-4">
                    <span className="text-4xl font-bold text-white">$0</span>
                    <span className="text-gray-500 text-sm ml-1">/ month</span>
                  </div>
                </div>
                <ul className="space-y-2.5 flex-1 mb-8">
                  {FREE_FEATURES.map(f => (
                    <li key={f} className="flex items-center gap-2.5 text-sm text-gray-400">
                      <svg className="w-4 h-4 text-gray-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => navigate('/app')}
                  className="w-full py-3 rounded-xl border border-gray-700 text-gray-400 text-sm font-medium hover:bg-gray-800 transition-colors"
                >
                  Current plan
                </button>
              </div>

              {/* Pro card */}
              <div className="bg-gray-900 border border-cyan-500/40 rounded-2xl p-7 flex flex-col relative overflow-hidden">
                <div className="absolute top-4 right-4">
                  <span className="text-[10px] px-2 py-1 bg-cyan-500/15 text-cyan-400 rounded-full border border-cyan-500/20 font-semibold uppercase tracking-wider">
                    Popular
                  </span>
                </div>
                <div className="mb-6">
                  <h2 className="text-lg font-bold text-white mb-1">Pro</h2>
                  <p className="text-gray-500 text-sm">For serious traders</p>
                  <div className="mt-4">
                    {billing === 'monthly' ? (
                      <>
                        <span className="text-4xl font-bold text-white">$6</span>
                        <span className="text-gray-500 text-sm ml-1">/ month</span>
                      </>
                    ) : (
                      <>
                        <span className="text-4xl font-bold text-white">$50</span>
                        <span className="text-gray-500 text-sm ml-1">/ year</span>
                        <p className="text-emerald-400 text-xs mt-1">$4.17/mo · 2 months free</p>
                      </>
                    )}
                  </div>
                </div>
                <ul className="space-y-2.5 flex-1 mb-8">
                  {PRO_FEATURES.map(f => (
                    <li key={f} className="flex items-center gap-2.5 text-sm text-gray-300">
                      <svg className="w-4 h-4 text-cyan-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={handleUpgrade}
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Redirecting...' : `Upgrade to Pro`}
                </button>
              </div>

            </div>

            <p className="text-center text-gray-600 text-xs mt-6">
              Payments processed securely by Stripe · Cancel anytime
            </p>
          </>
        )}
      </main>
    </div>
  );
}
