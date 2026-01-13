import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import DashboardView from '../components/dashboard/DashboardView';
import PortfolioTable from '../components/dashboard/PortfolioTable';
import AddInvestmentForm from '../components/dashboard/AddInvestmentForm';

function Dashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Top Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg"></div>
            <span className="text-xl font-bold text-white">CS2 Tracker</span>
          </div>

          {/* User info + Logout */}
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-gray-400">Welcome back,</p>
              <p className="text-white font-medium">{user?.username}</p>
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Tab Navigation */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                activeTab === 'dashboard'
                  ? 'border-cyan-500 text-cyan-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('portfolio')}
              className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                activeTab === 'portfolio'
                  ? 'border-cyan-500 text-cyan-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              Portfolio
            </button>
            <button
              onClick={() => setActiveTab('add')}
              className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                activeTab === 'add'
                  ? 'border-cyan-500 text-cyan-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              Add Investment
            </button>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'portfolio' && <PortfolioTable />}
        {activeTab === 'add' && <AddInvestmentForm />}
      </div>
    </div>
  );
}

export default Dashboard;