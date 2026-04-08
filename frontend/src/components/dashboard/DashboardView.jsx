import React, { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, ReferenceLine
} from 'recharts';
import { useNavigate } from 'react-router-dom';
import { investmentsAPI, portfolioAPI } from '../../api/investments';
import { formatCurrency } from '../../utils/currency';
import client from '../../api/client';

const TIMEFRAMES = [
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '1Y', days: 365 },
  { label: 'ALL', days: null },
];

const PIE_COLORS = ['#06b6d4','#3b82f6','#8b5cf6','#f59e0b','#10b981','#ef4444','#f97316','#84cc16'];
const TYPE_LABELS = { skin:'Skins', knife:'Knives', gloves:'Gloves', case:'Cases', sticker:'Stickers', agent:'Agents', keychain:'Keychains', other:'Other' };

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, subColor, positive, negative, neutral, icon }) {
  const valueColor = positive ? 'text-emerald-400' : negative ? 'text-red-400' : 'text-white';
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">{label}</span>
        <div className="text-gray-600">{icon}</div>
      </div>
      <div className={`text-2xl font-bold font-mono ${valueColor}`}>{value}</div>
      {sub && <div className={`text-xs mt-1 font-mono ${subColor || 'text-gray-600'}`}>{sub}</div>}
    </div>
  );
}

// ─── Chart tooltip ────────────────────────────────────────────────────────────

const ChartTooltip = ({ active, payload, label, startValue, isAllTime, totalInvested }) => {
  if (!active || !payload?.length) return null;
  const val = payload[0].value;
  const baseline = isAllTime ? totalInvested : startValue;
  const delta = baseline ? val - baseline : null;
  const pct = baseline && baseline > 0 ? ((val - baseline) / baseline * 100) : null;
  const up = delta >= 0;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 shadow-xl min-w-[140px]">
      <p className="text-gray-400 text-xs mb-2">{label}</p>
      <p className="text-white font-bold font-mono text-sm">{formatCurrency(val)}</p>
      {delta !== null && (
        <p className={`text-xs font-mono mt-1 ${up ? 'text-emerald-400' : 'text-red-400'}`}>
          {up ? '+' : ''}{formatCurrency(delta)} ({up ? '+' : ''}{pct?.toFixed(2)}%)
        </p>
      )}
    </div>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────

export default function DashboardView() {
  const navigate = useNavigate();
  const [timeframe, setTimeframe] = useState(TIMEFRAMES[0]); // default 1M
  const [performance, setPerformance] = useState(null);
  const [investments, setInvestments] = useState([]);
  const [topPerformers, setTopPerformers] = useState({ top_performers: [], worst_performers: [] });
  const [loading, setLoading] = useState(true);
  const [perfLoading, setPerfLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch static data (investments, top performers) — once
  const fetchStatic = useCallback(async () => {
    try {
      const [invs, top] = await Promise.all([
        investmentsAPI.getAll('active'),
        portfolioAPI.getTopPerformers(5),
      ]);
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

  // Fetch performance for the selected timeframe
  const fetchPerformance = useCallback(async (days) => {
    setPerfLoading(true);
    try {
      const params = days !== null ? { days } : {};
      const data = await client.get('/portfolio/performance', { params }).then(r => r.data);
      setPerformance(data);
    } catch (err) {
      console.error('Performance fetch failed:', err);
    } finally {
      setPerfLoading(false);
    }
  }, []);

  useEffect(() => { fetchStatic(); }, [fetchStatic]);
  useEffect(() => { fetchPerformance(timeframe.days); }, [fetchPerformance, timeframe]);

  useEffect(() => {
    const h = () => { fetchStatic(); fetchPerformance(timeframe.days); };
    window.addEventListener('currencychange', h);
    return () => window.removeEventListener('currencychange', h);
  }, [fetchStatic, fetchPerformance, timeframe]);

  // Build chart data from performance snapshots + live today point
  const chartData = React.useMemo(() => {
    if (!performance) return [];
    const points = (performance.snapshots || []).map(s => ({
      date: new Date(s.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }),
      value: s.value,
    }));
    // Append live today
    if (performance.current_value > 0) {
      const todayLabel = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
      const last = points[points.length - 1];
      if (!last || last.date !== todayLabel) {
        points.push({ date: todayLabel, value: performance.current_value });
      } else if (last) {
        last.value = performance.current_value;
      }
    }
    return points;
  }, [performance]);

  // Diversification pie
  const pieData = React.useMemo(() => {
    const counts = {};
    investments.forEach(inv => {
      const type = inv.item?.item_type || 'other';
      const value = (inv.current_price || 0) * inv.quantity;
      counts[type] = (counts[type] || 0) + value;
    });
    return Object.entries(counts).filter(([,v]) => v > 0).sort((a,b) => b[1]-a[1])
      .map(([type, value]) => ({ name: TYPE_LABELS[type] || type, value: parseFloat(value.toFixed(2)) }));
  }, [investments]);

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (error) return (
    <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">{error}</div>
  );

  const isAllTime = timeframe.days === null;
  const perf = performance;
  const periodPnlPos = (perf?.period_pnl || 0) >= 0;
  const periodRoiPos = (perf?.period_roi || 0) >= 0;

  // Chart colours based on period performance
  const chartUp = (perf?.period_pnl || 0) >= 0;
  const chartColor = chartUp ? '#10b981' : '#ef4444';
  const chartGradId = chartUp ? 'dashGradGreen' : 'dashGradRed';

  // For chart reference line: ALL = total_invested, windowed = start_value
  const refLineValue = isAllTime ? perf?.total_invested : perf?.start_value;
  const hasChartData = chartData.length > 1;

  // Timeframe label for sub-text
  const tfLabel = isAllTime ? 'all time' : `last ${timeframe.label.replace('M',' month').replace('Y',' year')}`;

  return (
    <div className="space-y-6">

      {/* ── Timeframe selector ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-white font-semibold">Portfolio Overview</h2>
          <p className="text-gray-500 text-xs mt-0.5">Performance over {tfLabel}</p>
        </div>
        <div className="flex bg-gray-900 border border-gray-800 rounded-xl p-1 gap-1">
          {TIMEFRAMES.map(tf => (
            <button key={tf.label} onClick={() => setTimeframe(tf)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                timeframe.label === tf.label
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20'
                  : 'text-gray-500 hover:text-gray-300'
              }`}>{tf.label}</button>
          ))}
        </div>
      </div>

      {/* ── Stat cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

        {/* Total invested — always static cost basis */}
        <StatCard
          label="Total Invested"
          value={perf ? formatCurrency(perf.total_invested) : '—'}
          sub="Cost basis · all time"
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />

        {/* Current value */}
        <StatCard
          label="Current Value"
          value={perf ? formatCurrency(perf.current_value) : '—'}
          sub={`${investments.filter(i => i.current_price).length} of ${investments.length} priced`}
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
        />

        {/* Period P&L — changes with timeframe */}
        <StatCard
          label={isAllTime ? 'Total P&L' : `${timeframe.label} Return`}
          value={perf
            ? `${periodPnlPos ? '+' : ''}${formatCurrency(perf.period_pnl)}`
            : '—'}
          sub={
            perfLoading ? 'Calculating...'
            : !perf?.has_snapshot_data && !isAllTime ? 'No history yet'
            : isAllTime ? 'vs purchase cost'
            : perf?.start_date
              ? `vs ${new Date(perf.start_date).toLocaleDateString('en-GB', { day:'numeric', month:'short' })}`
              : 'vs cost basis (no snapshot)'
          }
          subColor={
            perfLoading ? 'text-gray-600'
            : !perf?.has_snapshot_data && !isAllTime ? 'text-gray-600'
            : periodPnlPos ? 'text-emerald-600' : 'text-red-600'
          }
          positive={periodPnlPos && !!perf}
          negative={!periodPnlPos && !!perf}
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10" /></svg>}
        />

        {/* Period ROI — changes with timeframe */}
        <StatCard
          label={isAllTime ? 'Overall ROI' : `${timeframe.label} ROI`}
          value={perf
            ? `${periodRoiPos ? '+' : ''}${(perf.period_roi || 0).toFixed(2)}%`
            : '—'}
          sub={
            perfLoading ? 'Calculating...'
            : !perf?.has_snapshot_data && !isAllTime ? 'Accumulating data'
            : isAllTime ? 'since purchase' : `over ${tfLabel}`
          }
          subColor={
            perfLoading || (!perf?.has_snapshot_data && !isAllTime) ? 'text-gray-600'
            : periodRoiPos ? 'text-emerald-600' : 'text-red-600'
          }
          positive={periodRoiPos && !!perf}
          negative={!periodRoiPos && !!perf}
          icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
        />
      </div>

      {/* ── Portfolio chart ── */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-white font-semibold">Portfolio Value</h3>
          {perfLoading && <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />}
        </div>
        <p className="text-gray-500 text-xs mb-5">
          {hasChartData
            ? `${chartData.length} data points · ${tfLabel}`
            : isAllTime ? 'Daily snapshots accumulate automatically' : `No snapshot data for ${tfLabel} yet`}
        </p>

        {hasChartData ? (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id={chartGradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColor} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill:'#6b7280', fontSize:11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={{ fill:'#6b7280', fontSize:11 }} axisLine={false} tickLine={false}
                tickFormatter={v => formatCurrency(v, null, true)} width={60} domain={['auto','auto']} />
              <Tooltip content={
                <ChartTooltip
                  startValue={perf?.start_value}
                  isAllTime={isAllTime}
                  totalInvested={perf?.total_invested}
                />
              } />
              {/* Reference line — start of window or cost basis */}
              {refLineValue && (
                <ReferenceLine y={refLineValue} stroke="#374151" strokeDasharray="4 3"
                  label={{ value: isAllTime ? 'cost' : 'start', position: 'right', fill: '#4b5563', fontSize: 9 }} />
              )}
              <Area type="monotone" dataKey="value" stroke={chartColor} strokeWidth={2}
                fill={`url(#${chartGradId})`} dot={false} activeDot={{ r:4, fill:chartColor, strokeWidth:0 }} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex flex-col items-center justify-center h-48 text-gray-700 gap-2">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
            <p className="text-sm text-gray-600">
              {isAllTime ? 'Portfolio history appears here as snapshots accumulate' : `Switch to ALL to see your full history`}
            </p>
          </div>
        )}
      </div>

      {/* ── Diversification + Performers ── */}
      <div className="grid lg:grid-cols-2 gap-5">

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-1">Diversification</h3>
          <p className="text-gray-500 text-xs mb-4">Portfolio breakdown by item type</p>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={2} dataKey="value">
                  {pieData.map((_,i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Legend formatter={v => <span className="text-gray-400 text-xs">{v}</span>} iconType="circle" iconSize={8} />
                <Tooltip formatter={v => [formatCurrency(v),'Value']}
                  contentStyle={{ background:'#111827', border:'1px solid #374151', borderRadius:12 }}
                  labelStyle={{ color:'#9ca3af' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-600 text-sm">No portfolio data yet</div>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4">
          <div>
            <h3 className="text-white font-semibold mb-3">Top Performers</h3>
            {topPerformers.top_performers.length > 0 ? (
              <div className="space-y-2">
                {topPerformers.top_performers.slice(0,3).map(inv => (
                  <button key={inv.id} onClick={() => navigate(`/investments/${inv.id}`)}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-gray-800 transition-colors text-left">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <img src={inv.item?.image_url} alt="" className="w-8 h-8 object-contain bg-gray-800 rounded"
                        onError={e => { e.target.style.display='none'; }} />
                      <span className="text-gray-300 text-sm truncate">{inv.item?.market_hash_name}</span>
                    </div>
                    <span className="text-emerald-400 font-mono text-sm font-medium ml-2 shrink-0">+{(inv.roi||0).toFixed(1)}%</span>
                  </button>
                ))}
              </div>
            ) : <p className="text-gray-600 text-sm">No data yet</p>}
          </div>

          <div className="border-t border-gray-800 pt-4">
            <h3 className="text-white font-semibold mb-3">Worst Performers</h3>
            {topPerformers.worst_performers.length > 0 ? (
              <div className="space-y-2">
                {topPerformers.worst_performers.slice(0,3).map(inv => (
                  <button key={inv.id} onClick={() => navigate(`/investments/${inv.id}`)}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-gray-800 transition-colors text-left">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <img src={inv.item?.image_url} alt="" className="w-8 h-8 object-contain bg-gray-800 rounded"
                        onError={e => { e.target.style.display='none'; }} />
                      <span className="text-gray-300 text-sm truncate">{inv.item?.market_hash_name}</span>
                    </div>
                    <span className="text-red-400 font-mono text-sm font-medium ml-2 shrink-0">{(inv.roi||0).toFixed(1)}%</span>
                  </button>
                ))}
              </div>
            ) : <p className="text-gray-600 text-sm">No data yet</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
