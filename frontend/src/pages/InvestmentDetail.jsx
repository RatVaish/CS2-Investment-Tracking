import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts';
import Navbar from '../components/Navbar';
import { investmentsAPI, portfolioAPI } from '../api/investments';
import { formatCurrency, formatCNY } from '../utils/currency';
import toast from 'react-hot-toast';

const RESOLUTIONS = [
  { label: '1M', days: 30, resolution: 'hourly' },
  { label: '3M', days: 90, resolution: 'daily' },
  { label: '1Y', days: 365, resolution: 'daily' },
  { label: 'ALL', days: null, resolution: 'weekly' },
];




const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl px-3 py-2.5 shadow-xl text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      <p className="text-white font-bold font-mono">{formatCurrency(payload[0]?.value)}</p>
      {payload[0]?.payload?.volume > 0 && (
        <p className="text-gray-500 font-mono mt-0.5">
          Vol: {payload[0].payload.volume.toLocaleString()}
        </p>
      )}
    </div>
  );
};

export default function InvestmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [investment, setInvestment] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [availableMarkets, setAvailableMarkets] = useState([]);
  const [selectedResolution, setSelectedResolution] = useState(RESOLUTIONS[2]);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  const [isFirstLoad, setIsFirstLoad] = useState(false);

  const fetchInvestment = useCallback(async () => {
    try {
      const data = await investmentsAPI.getById(id);
      setInvestment(data);
    } catch {
      toast.error('Investment not found');
      navigate('/app/portfolio');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  const fetchChart = useCallback(async (inv, market, resolution) => {
    if (!inv?.item_id) return;
    setChartLoading(true);
    try {
      const data = await portfolioAPI.getPriceHistory(
        inv.item_id, market, resolution.resolution, resolution.days
      );
      setIsFirstLoad(data.backfilled || false);
      setChartData((data.candles || []).map(c => ({
        date: new Date(c.timestamp).toLocaleDateString('en-GB', {
          day: 'numeric', month: 'short',
          ...(resolution.resolution === 'hourly' ? { hour: '2-digit', minute: '2-digit' } : {}),
        }),
        open: c.open, high: c.high, low: c.low, close: c.close, volume: c.volume || 0,
      })));
    } catch {
      toast.error('Failed to load price history');
      setChartData([]);
    } finally {
      setChartLoading(false);
    }
  }, []);

  const fetchMarkets = useCallback(async (inv) => {
    if (!inv?.item_id) return;
    try {
      const data = await portfolioAPI.getAvailableMarkets(inv.item_id);
      setAvailableMarkets(data.markets || []);
    } catch {}
  }, []);

  useEffect(() => { fetchInvestment(); }, [fetchInvestment]);
  useEffect(() => {
    if (investment) {
      fetchChart(investment, 'steam', selectedResolution);
      fetchMarkets(investment);
    }
  }, [investment]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const item = investment?.item;
  const prices = investment?.prices || {};
  const steamPrice = prices.steam?.price;
  const csfloatPrice = prices.csfloat?.price;
  const buffPrice = prices.buff163?.price;
  const pnlPos = (investment?.profit_loss || 0) >= 0;

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-6xl mx-auto px-6 pt-24 pb-12 space-y-5">

        {/* Back */}
        <button onClick={() => navigate('/app/portfolio')}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-300 transition-colors text-sm">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Portfolio
        </button>

        {/* Header */}
        <div className="flex items-start gap-5 bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <div className="w-20 h-20 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shrink-0 flex items-center justify-center">
            {item?.image_url
              ? <img src={item.image_url} alt="" className="w-full h-full object-contain p-1" />
              : <svg className="w-8 h-8 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
            }
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h1 className="text-xl font-bold text-white">{item?.market_hash_name || 'Unknown'}</h1>
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                  {item?.rarity && <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{item.rarity}</span>}
                  {item?.collection && <span className="text-xs text-gray-600">{item.collection}</span>}
                  {item?.is_stattrak && <span className="text-xs text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/20">StatTrak™</span>}
                  {item?.wear && <span className="text-xs text-gray-500">{item.wear}</span>}
                </div>
              </div>
              <div className="text-right shrink-0">
                <div className={`text-2xl font-bold font-mono ${pnlPos ? 'text-emerald-400' : 'text-red-400'}`}>
                  {pnlPos ? '+' : ''}{formatCurrency(investment?.profit_loss)}
                </div>
                <div className={`text-sm font-mono ${pnlPos ? 'text-emerald-500' : 'text-red-500'}`}>
                  {pnlPos ? '+' : ''}{(investment?.roi || 0).toFixed(2)}% ROI
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Price cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { label: 'Your Position', sub: `${investment?.quantity}× @ ${formatCurrency(investment?.purchase_price)}`, value: formatCurrency(investment?.total_invested), color: 'text-white' },
            { label: 'Steam Price', sub: 'Real sales · P&L basis', value: steamPrice ? formatCurrency(steamPrice) : '—', color: 'text-cyan-400', badge: 'Steam' },
            { label: 'CSFloat', sub: 'Sell for (USD)', value: csfloatPrice ? formatCurrency(csfloatPrice) : '—', color: 'text-blue-400', badge: 'CSFloat' },
            { label: 'Buff163', sub: 'Sell for (USD equiv.)', value: buffPrice ? formatCurrency(buffPrice) : '—', color: 'text-orange-400', badge: 'Buff' },
          ].map(c => (
            <div key={c.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs text-gray-500">{c.label}</span>
                {c.badge && <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-gray-800 text-gray-500">{c.badge}</span>}
              </div>
              <div className={`text-lg font-bold font-mono ${c.color}`}>{c.value}</div>
              <div className="text-xs text-gray-600 mt-0.5">{c.sub}</div>
            </div>
          ))}
        </div>

        {/* Chart */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <div>
              <h3 className="text-white font-semibold">Price History</h3>
              {isFirstLoad && (
                <p className="text-cyan-400 text-xs mt-0.5 flex items-center gap-1.5">
                  <span className="w-3 h-3 border border-cyan-400 border-t-transparent rounded-full animate-spin" />
                  Fetching historical data for the first time...
                </p>
              )}
              {!chartLoading && chartData.length > 0 && (
                <p className="text-gray-700 text-xs mt-0.5">
                  {chartData.length} data points · Steam Market · {selectedResolution.resolution}
                </p>
              )}
            </div>
            <div className="flex bg-gray-800 rounded-xl p-1 gap-1">
              {RESOLUTIONS.map(res => (
                <button key={res.label}
                  onClick={() => { setSelectedResolution(res); fetchChart(investment, 'steam', res); }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${selectedResolution.label === res.label ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20' : 'text-gray-500 hover:text-gray-300'}`}>
                  {res.label}
                </button>
              ))}
            </div>
          </div>

          {chartLoading ? (
            <div className="flex items-center justify-center h-72">
              <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-72 text-gray-600 gap-2">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4" />
              </svg>
              <p className="text-sm">No price history available</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart
                data={chartData.map(d => ({ ...d, value: d.close }))}
                margin={{ top: 5, right: 65, bottom: 5, left: 0 }}
              >
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={v => formatCurrency(v, null, true)}
                  width={60}
                  domain={['auto', 'auto']}
                />
                <Tooltip content={<ChartTooltip />} />
                {investment?.purchase_price && (
                  <ReferenceLine
                    y={investment.purchase_price}
                    stroke="#4b5563"
                    strokeDasharray="5 3"
                    label={{ value: 'buy', position: 'right', fill: '#6b7280', fontSize: 9 }}
                  />
                )}
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#06b6d4"
                  strokeWidth={1.5}
                  fill="url(#areaGrad)"
                  dot={false}
                  activeDot={{ r: 3, fill: '#06b6d4', strokeWidth: 0 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}

          <p className="text-xs text-gray-700 mt-3 text-center">
            Steam Market · Median sale price per {selectedResolution.resolution}
          </p>
        </div>

        {/* Details */}
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-4">Position Details</h3>
            {[
              { label: 'Quantity', value: `${investment?.quantity}×` },
              { label: 'Purchase Price', value: formatCurrency(investment?.purchase_price) },
              { label: 'Total Invested', value: formatCurrency(investment?.total_invested) },
              { label: 'Current Value', value: investment?.current_value ? formatCurrency(investment.current_value) : '—' },
              { label: 'Unrealised P&L', value: investment?.profit_loss !== null ? `${pnlPos ? '+' : ''}${formatCurrency(investment.profit_loss)}` : '—', color: pnlPos ? 'text-emerald-400' : 'text-red-400' },
              { label: 'ROI', value: investment?.roi !== null ? `${pnlPos ? '+' : ''}${(investment.roi || 0).toFixed(2)}%` : '—', color: pnlPos ? 'text-emerald-400' : 'text-red-400' },
              { label: 'Purchase Date', value: investment?.purchase_date ? new Date(investment.purchase_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '—' },
              { label: 'Float Value', value: investment?.wear_value ? investment.wear_value.toFixed(8) : '—' },
            ].map(row => (
              <div key={row.label} className="flex justify-between items-center py-2.5 border-b border-gray-800/50 last:border-0">
                <span className="text-gray-500 text-sm">{row.label}</span>
                <span className={`text-sm font-mono ${row.color || 'text-gray-300'}`}>{row.value}</span>
              </div>
            ))}
          </div>

          <div className="space-y-4">
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-4">Market Prices</h3>
              <div className="space-y-2.5">
                {[
                  { label: 'Steam Market', dot: 'bg-cyan-400', color: 'text-cyan-400', price: steamPrice ? formatCurrency(steamPrice) : null, sub: 'Real sale data · P&L basis' },
                  { label: 'CSFloat', dot: 'bg-blue-400', color: 'text-blue-400', price: csfloatPrice ? formatCurrency(csfloatPrice) : null, sub: 'Sell instantly (USD)' },
                  { label: 'Buff163', dot: 'bg-orange-400', color: 'text-orange-400', price: buffPrice ? formatCurrency(buffPrice) : null, sub: 'Sell instantly (USD equiv.)' },
                ].map(m => (
                  <div key={m.label} className="flex items-center justify-between p-3 bg-gray-800/40 rounded-xl">
                    <div className="flex items-center gap-2.5">
                      <div className={`w-1.5 h-1.5 rounded-full ${m.dot}`} />
                      <div>
                        <span className="text-gray-300 text-sm font-medium">{m.label}</span>
                        <p className="text-xs text-gray-600">{m.sub}</p>
                      </div>
                    </div>
                    <span className={`font-mono font-bold text-sm ${m.price ? m.color : 'text-gray-700'}`}>
                      {m.price || '—'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {investment?.notes && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
                <h3 className="text-white font-semibold mb-3">Notes</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{investment.notes}</p>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-800 py-6 px-6 mt-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-700">
          <span>CS2 Tracker · Steam Market, Buff163 & CSFloat</span>
          <div className="flex gap-5">
            <a href="/privacy" className="hover:text-gray-500">Privacy</a>
            <a href="/terms" className="hover:text-gray-500">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
