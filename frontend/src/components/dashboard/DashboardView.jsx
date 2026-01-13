import React, { useState, useEffect } from 'react';
import { authAPI } from '../../api/auth';
import { investmentsAPI } from '../../api/investments';

function DashboardView() {
  const [stats, setStats] = useState(null);
  const [investments, setInvestments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [userStats, investmentsList] = await Promise.all([
        authAPI.getProfileWithStats(),
        investmentsAPI.getAll()
      ]);

      setStats(userStats);
      setInvestments(investmentsList);
      setError('');
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getTopPerformers = () => {
    return investments
      .filter(inv => inv.current_price && inv.purchase_price)
      .map(inv => ({
        ...inv,
        profitLoss: (inv.current_price - inv.purchase_price) * inv.quantity,
        roi: ((inv.current_price - inv.purchase_price) / inv.purchase_price) * 100
      }))
      .sort((a, b) => b.roi - a.roi)
      .slice(0, 5);
  };

  const getWorstPerformers = () => {
    return investments
      .filter(inv => inv.current_price && inv.purchase_price)
      .map(inv => ({
        ...inv,
        profitLoss: (inv.current_price - inv.purchase_price) * inv.quantity,
        roi: ((inv.current_price - inv.purchase_price) / inv.purchase_price) * 100
      }))
      .sort((a, b) => a.roi - b.roi)
      .slice(0, 5);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  const topPerformers = getTopPerformers();
  const worstPerformers = getWorstPerformers();

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Dashboard Overview</h2>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Investments */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-sm">Total Investments</p>
            <svg className="w-5 h-5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <p className="text-3xl font-bold text-white">{stats?.total_investments || 0}</p>
        </div>

        {/* Total Value */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-sm">Portfolio Value</p>
            <svg className="w-5 h-5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-3xl font-bold text-white">£{stats?.total_value?.toFixed(2) || '0.00'}</p>
        </div>

        {/* Total P&L */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-sm">Total P&L</p>
            <svg className="w-5 h-5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <p className={`text-3xl font-bold ${
            stats?.total_profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {stats?.total_profit_loss >= 0 ? '+' : ''}£{stats?.total_profit_loss?.toFixed(2) || '0.00'}
          </p>
        </div>

        {/* ROI */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-sm">Overall ROI</p>
            <svg className="w-5 h-5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className={`text-3xl font-bold ${
            stats?.total_profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {(() => {
              const totalInvested = investments.reduce((sum, inv) => sum + (inv.purchase_price * inv.quantity), 0);
              if (totalInvested === 0) return '0.00%';
              const roi = (stats?.total_profit_loss / totalInvested) * 100;
              return `${roi >= 0 ? '+' : ''}${roi.toFixed(2)}%`;
            })()}
          </p>
        </div>
      </div>

      {/* Top & Worst Performers */}
      {investments.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Performers */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">Top Performers</h3>
            {topPerformers.length > 0 ? (
              <div className="space-y-3">
                {topPerformers.map((inv) => (
                  <div key={inv.id} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-medium truncate">{inv.item_name}</p>
                      <p className="text-gray-400 text-sm">
                        {inv.quantity}x @ £{inv.purchase_price.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-green-400 font-bold">
                        +{inv.roi.toFixed(2)}%
                      </p>
                      <p className="text-green-400 text-sm">
                        +£{inv.profitLoss.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No data available yet
              </p>
            )}
          </div>

          {/* Worst Performers */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">Worst Performers</h3>
            {worstPerformers.length > 0 ? (
              <div className="space-y-3">
                {worstPerformers.map((inv) => (
                  <div key={inv.id} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-medium truncate">{inv.item_name}</p>
                      <p className="text-gray-400 text-sm">
                        {inv.quantity}x @ £{inv.purchase_price.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-red-400 font-bold">
                        {inv.roi.toFixed(2)}%
                      </p>
                      <p className="text-red-400 text-sm">
                        £{inv.profitLoss.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No data available yet
              </p>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {investments.length === 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-12 text-center">
          <svg className="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-gray-400 text-lg mb-2">No investments yet</p>
          <p className="text-gray-500">Add your first investment to see your dashboard come alive!</p>
        </div>
      )}
    </div>
  );
}

export default DashboardView;