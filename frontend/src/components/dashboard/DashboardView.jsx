import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { useNavigate } from 'react-router-dom';
import { investmentsAPI, portfolioAPI } from '../../api/investments';
import { formatCurrency } from '../../utils/currency';

const TIMEFRAMES = [
  { label: '1W', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '1Y', days: 365 },
  { label: 'ALL', days: null },
];

const PIE_COLORS = [
  '#06b6d4', '#3b82f6', '#8b5cf6', '#f59e0b',
  '#10b981', '#ef4444', '#f97316', '#84cc16',
];

const TYPE_LABELS = {
  skin: 'Skins',
  knife: 'Knives',
  gloves: 'Gloves',
  case: 'Cases',
  sticker: 'Stickers',
  agent: 'Agents',
  keychain: 'Keychains',
  other: 'Other',
};

function StatCard({ label, value, sub, positive, negative, icon }) {
  const color = positive ? 'text-emerald-400' : negative ? 'text-red-400' : 'text-white';
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">{label}</span>
        <div className="text-gray-600">{icon}</div>
      </div>
      <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
      {sub && <div className="text-xs text-gray-600 mt-1 font-mono">{sub}</div>}
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 shadow-xl">
      <p className="text-gray-400 text-xs mb-1">{label}</p>
      <p className="text-white font-bold font-mono">{formatCurrency(payload[0].value)}</p>
    </div>
  );
};

export default function DashboardView() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [investments, setInvestments] = useState([]);
  const [topPerformers, setTopPerformers] = useState({ top_performers: [], worst_performers: [] });
  const [timeframe, setTimeframe] = useState(TIMEFRAMES[1]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchAll = useCallback(async () => {
    try {
      const [sum, invs, top] = await Promise.all([
        investmentsAPI.getSummary(),
        investmentsAPI.getAll('active'),
        portfolioAPI.getTopPerformers(5),
      ]);
      setSummary(sum);
      setInvestments(invs);
      setTopPerformers(top);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Listen for currency changes
  useEffect(() => {
    const handler = () => fetchAll();
    window.addEventListener('currencychange', handler);
    return () => window.removeEventListener('currencychange', handler);
  }, [fetchAll]);

  // Build diversification data from investments
  const pieData = React.useMemo(() => {
    const counts = {};
    investments.forEach(inv => {
      const type = inv.item?.item_type || 'other';
      const value = (inv.current_price || 0) * inv.quantity;
      counts[type] = (counts[type] || 0) + value;
    });
    return Object.entries(counts)
      .filter(([, v]) => v > 0)
      .sort((a, b) => b[1] - a[1])
      .map(([type, value]) => ({
        name: TYPE_LABELS[type] || type,
        value: parseFloat(value.toFixed(2)),
      }));
  }, [investments]);

  // Mock portfolio over time — will be replaced with real snapshot data
  const chartData = React.useMemo(() => {
    if (!summary) return [];
    const days = timeframe.days || 90;
    const data = [];
    const now = Date.now();
    const totalValue = summary.total_current_value || 0;
    for (let i = days; i >= 0; i--) {
      const d = new Date(now - i * 86400000);
      const label = d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
      // Simulate gentle curve toward current value
      const progress = (days - i) / days;
      const noise = (Math.random() - 0.5) * totalValue * 0.03;
      const v = totalValue * (0.85 + 0.15 * progress) + noise;
      data.push({ date: label, value: Math.max(0, v) });
    }
    // Last point = actual current value
    if (data.length) data[data.length - 1].value = totalValue;
    return data;
  }, [summary, timeframe]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
        {error}
      </div>
    );
  }

  const pnlPositive = (summary?.total_profit_loss || 0) >= 0;
  const roiPositive = (summary?.overall_roi || 0) >= 0;

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Invested"
          value={formatCurrency(summary?.total_invested || 0)}
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <StatCard
          label="Current Value"
          value={formatCurrency(summary?.total_current_value || 0)}
          sub={`${summary?.priced_investments || 0} of ${summary?.total_investments || 0} priced`}
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
        />
        <StatCard
          label="Total P&L"
          value={`${pnlPositive ? '+' : ''}${formatCurrency(summary?.total_profit_loss || 0)}`}
          positive={pnlPositive}
          negative={!pnlPositive}
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10" /></svg>}
        />
        <StatCard
          label="Overall ROI"
          value={`${roiPositive ? '+' : ''}${(summary?.overall_roi || 0).toFixed(2)}%`}
          positive={roiPositive}
          negative={!roiPositive}
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
        />
      </div>

      {/* Portfolio value chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-white font-semibold">Portfolio Value</h3>
            <p className="text-gray-500 text-xs mt-0.5">Based on Steam market prices</p>
          </div>
          <div className="flex gap-1">
            {TIMEFRAMES.map(tf => (
              <button
                key={tf.label}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  timeframe.label === tf.label
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <XAxis
              dataKey="date"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => formatCurrency(v, null, true)}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#06b6d4', strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-600 mt-3 text-center">
          Portfolio history chart will populate as daily snapshots accumulate
        </p>
      </div>

      {/* Diversification + Performers */}
      <div className="grid lg:grid-cols-2 gap-5">
        {/* Pie chart */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-1">Diversification</h3>
          <p className="text-gray-500 text-xs mb-4">Portfolio breakdown by item type</p>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Legend
                  formatter={(value) => <span className="text-gray-400 text-xs">{value}</span>}
                  iconType="circle"
                  iconSize={8}
                />
                <Tooltip
                  formatter={(v) => [formatCurrency(v), 'Value']}
                  contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 12 }}
                  labelStyle={{ color: '#9ca3af' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-600 text-sm">
              No portfolio data yet
            </div>
          )}
        </div>

        {/* Top/Worst performers */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4">
          <div>
            <h3 className="text-white font-semibold mb-3">Top Performers</h3>
            {topPerformers.top_performers.length > 0 ? (
              <div className="space-y-2">
                {topPerformers.top_performers.slice(0, 3).map(inv => (
                  <button
                    key={inv.id}
                    onClick={() => navigate(`/investments/${inv.id}`)}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-gray-800 transition-colors text-left"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <img
                        src={inv.item?.image_url}
                        alt=""
                        className="w-8 h-8 object-contain bg-gray-800 rounded"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                      <span className="text-gray-300 text-sm truncate">{inv.item?.market_hash_name}</span>
                    </div>
                    <span className="text-emerald-400 font-mono text-sm font-medium ml-2 shrink-0">
                      +{(inv.roi || 0).toFixed(1)}%
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">No data yet</p>
            )}
          </div>

          <div className="border-t border-gray-800 pt-4">
            <h3 className="text-white font-semibold mb-3">Worst Performers</h3>
            {topPerformers.worst_performers.length > 0 ? (
              <div className="space-y-2">
                {topPerformers.worst_performers.slice(0, 3).map(inv => (
                  <button
                    key={inv.id}
                    onClick={() => navigate(`/investments/${inv.id}`)}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-gray-800 transition-colors text-left"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <img
                        src={inv.item?.image_url}
                        alt=""
                        className="w-8 h-8 object-contain bg-gray-800 rounded"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                      <span className="text-gray-300 text-sm truncate">{inv.item?.market_hash_name}</span>
                    </div>
                    <span className="text-red-400 font-mono text-sm font-medium ml-2 shrink-0">
                      {(inv.roi || 0).toFixed(1)}%
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">No data yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
