import React, { useState } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../components/Navbar';
import DashboardView from '../components/dashboard/DashboardView';
import PortfolioTable from '../components/dashboard/PortfolioTable';
import AddInvestmentForm from '../components/dashboard/AddInvestmentForm';
import VerifyEmailModal from '../components/auth/VerifyEmailModal';
import { useAuth } from '../contexts/AuthContext';

const TABS = [
  { label: 'Dashboard', path: '/app' },
  { label: 'Portfolio', path: '/app/portfolio' },
  { label: 'Add Investment', path: '/app/add' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [showVerifyModal, setShowVerifyModal] = useState(false);

  const isActive = (path) => {
    if (path === '/app') return location.pathname === '/app';
    return location.pathname.startsWith(path);
  };

  const needsVerification = user && !user.email_verified;

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />

      {/* Email verification banner */}
      {needsVerification && (
        <div className="fixed top-16 left-0 right-0 z-50 bg-amber-500/10 border-b border-amber-500/30 px-6 py-2.5">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
            <div className="flex items-center gap-2.5 text-sm text-amber-300">
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>
                {!user.email || user.email.endsWith('@steam.placeholder')
                  ? 'Add an email address to enable price alerts and notifications.'
                  : 'Please verify your email address to unlock all features.'}
              </span>
            </div>
            <button
              onClick={() => setShowVerifyModal(true)}
              className="shrink-0 px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-black text-xs font-semibold rounded-lg transition-colors"
            >
              {!user.email || user.email.endsWith('@steam.placeholder') ? 'Add Email' : 'Verify Account'}
            </button>
          </div>
        </div>
      )}

      {/* Tab bar — shifts down when banner is visible */}
      <div className={`fixed left-0 right-0 z-40 bg-gray-950/95 backdrop-blur border-b border-gray-800 ${needsVerification ? 'top-28' : 'top-16'}`}>
        <div className="max-w-7xl mx-auto px-6 flex gap-1 py-2">
          {TABS.map(tab => (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive(tab.path)
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Page content — shifts down when banner is visible */}
      <main className={`max-w-7xl mx-auto px-6 pb-12 ${needsVerification ? 'pt-48' : 'pt-36'}`}>
        <Routes>
          <Route index element={<DashboardView />} />
          <Route path="portfolio" element={<PortfolioTable />} />
          <Route path="add" element={<AddInvestmentForm />} />
          <Route path="*" element={<Navigate to="/app" replace />} />
        </Routes>
      </main>

      <footer className="border-t border-gray-800 py-6 px-6 mt-12">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-600">
          <span>Floatbase — Prices from Steam Market, Buff163 & CSFloat</span>
          <div className="flex gap-5">
            <a href="/privacy" className="hover:text-gray-400 transition-colors">Privacy</a>
            <a href="/terms" className="hover:text-gray-400 transition-colors">Terms</a>
            <a href="mailto:hello@floatbase.app" className="hover:text-gray-400 transition-colors">Support</a>
          </div>
        </div>
      </footer>

      {showVerifyModal && <VerifyEmailModal onClose={() => setShowVerifyModal(false)} />}
    </div>
  );
}
