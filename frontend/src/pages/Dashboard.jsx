import React from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../components/Navbar';
import DashboardView from '../components/dashboard/DashboardView';
import PortfolioTable from '../components/dashboard/PortfolioTable';
import AddInvestmentForm from '../components/dashboard/AddInvestmentForm';

const TABS = [
  { label: 'Dashboard', path: '/app' },
  { label: 'Portfolio', path: '/app/portfolio' },
  { label: 'Add Investment', path: '/app/add' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/app') return location.pathname === '/app';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />

      {/* Tab bar */}
      <div className="fixed top-16 left-0 right-0 z-40 bg-gray-950/95 backdrop-blur border-b border-gray-800">
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

      {/* Page content */}
      <main className="max-w-7xl mx-auto px-6 pt-36 pb-12">
        <Routes>
          <Route index element={<DashboardView />} />
          <Route path="portfolio" element={<PortfolioTable />} />
          <Route path="add" element={<AddInvestmentForm />} />
          <Route path="*" element={<Navigate to="/app" replace />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-6 px-6 mt-12">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-600">
          <span>CS2 Tracker — Prices from Steam Market, Buff163, CSFloat</span>
          <div className="flex gap-5">
            <a href="#" className="hover:text-gray-400 transition-colors">Privacy</a>
            <a href="#" className="hover:text-gray-400 transition-colors">Terms</a>
            <a href="#" className="hover:text-gray-400 transition-colors">Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
