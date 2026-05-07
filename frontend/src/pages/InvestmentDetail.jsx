import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine, Customized
} from 'recharts';
import Navbar from '../components/Navbar';
import { investmentsAPI, portfolioAPI } from '../api/investments';
import { formatCurrency } from '../utils/currency';
import { useAuth } from '../contexts/AuthContext';
import { alertsAPI } from '../api/alerts';
import toast from 'react-hot-toast';

const RESOLUTIONS = [
  { label: '1M', days: 30,   resolution: 'hourly' },
  { label: '3M', days: 90,   resolution: 'daily'  },
  { label: '1Y', days: 365,  resolution: 'daily'  },
  { label: 'ALL', days: null, resolution: 'weekly' },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function holdingLabel(fromStr, toStr) {
  if (!fromStr) return null;
  const start = new Date(fromStr);
  const end   = toStr ? new Date(toStr) : new Date();
  const days  = Math.floor((end - start) / 86400000);
  if (days < 1)    return 'same day';
  if (days < 30)   return `${days}d`;
  const mo = Math.floor(days / 30);
  const yr = Math.floor(mo / 12);
  const rem = mo % 12;
  if (yr === 0)    return `${mo}mo`;
  return rem === 0 ? `${yr}yr` : `${yr}yr ${rem}mo`;
}

// Find chartData index whose rawTimestamp is nearest to an ISO date string
function nearestIndex(chartData, isoDate) {
  if (!isoDate || !chartData.length) return null;
  const target = new Date(isoDate).getTime();
  let best = 0, bestDiff = Infinity;
  chartData.forEach((d, i) => {
    const diff = Math.abs(d.rawTimestamp - target);
    if (diff < bestDiff) { bestDiff = diff; best = i; }
  });
  return best;
}

// ─── Chart tooltip ────────────────────────────────────────────────────────────

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

// ─── Trade markers (Recharts Customized layer) ────────────────────────────────

function TradeMarkers({ chartData, positions, xAxisMap, yAxisMap }) {
  if (!xAxisMap || !yAxisMap || !chartData.length || !positions.length) return null;

  const xScale = Object.values(xAxisMap)[0];
  const yScale = Object.values(yAxisMap)[0];
  if (!xScale || !yScale) return null;

  const markers = [];

  positions.forEach((pos, posIdx) => {
    // Entry marker — only if purchase_date falls within chart window
    if (pos.purchase_date) {
      const idx = nearestIndex(chartData, pos.purchase_date);
      if (idx !== null) {
        const x = xScale.scale(idx);
        const y = yScale.scale(pos.purchase_price);
        if (x !== undefined && y !== undefined && !isNaN(x) && !isNaN(y)) {
          markers.push(
            <EntryMarker
              key={`entry-${pos.id}`}
              x={x} y={y}
              price={pos.purchase_price}
              quantity={pos.quantity}
              date={pos.purchase_date}
              posIdx={posIdx}
            />
          );
        }
      }
    }

    // Exit marker — only if sold and sold_at falls within chart window
    if (pos.status === 'sold' && pos.sold_at && pos.sold_price) {
      const idx = nearestIndex(chartData, pos.sold_at);
      if (idx !== null) {
        const x = xScale.scale(idx);
        const y = yScale.scale(pos.sold_price);
        if (x !== undefined && y !== undefined && !isNaN(x) && !isNaN(y)) {
          markers.push(
            <ExitMarker
              key={`exit-${pos.id}`}
              x={x} y={y}
              price={pos.sold_price}
              quantity={pos.quantity}
              date={pos.sold_at}
            />
          );
        }
      }
    }
  });

  return <g>{markers}</g>;
}

function EntryMarker({ x, y, price, quantity, date, posIdx }) {
  const [hovered, setHovered] = useState(false);
  const label = `${quantity > 1 ? `×${quantity} ` : ''}${formatCurrency(price)}`;
  const dateStr = new Date(date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <g transform={`translate(${x},${y})`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ cursor: 'pointer' }}>
      {/* Arrow shaft */}
      <line x1="0" y1="-36" x2="0" y2="-10" stroke="#10b981" strokeWidth="2.5" />
      {/* Arrowhead pointing up */}
      <polygon points="0,-4 -7,-18 7,-18" fill="#10b981" />
      {/* Base dot */}
      <circle cx="0" cy="0" r="4" fill="#10b981" />
      {/* Always-visible quantity+price badge */}
      <rect x="-28" y="-58" width="56" height="18" rx="4" fill="#10b981" fillOpacity="0.15" stroke="#10b981" strokeWidth="0.8" strokeOpacity="0.6" />
      <text x="0" y="-45" textAnchor="middle" fontSize="9" fontWeight="bold" fill="#10b981" fontFamily="monospace">{label}</text>

      {/* Tooltip on hover */}
      {hovered && (
        <g transform="translate(8, -48)">
          <rect x="0" y="0" width="130" height="44" rx="6"
            fill="#111827" stroke="#10b981" strokeWidth="0.5" strokeOpacity="0.6" />
          <text x="8" y="14" fontSize="9" fill="#6b7280">{dateStr}</text>
          <text x="8" y="27" fontSize="11" fontWeight="bold" fill="#10b981" fontFamily="monospace">
            Buy {label}
          </text>
          <text x="8" y="39" fontSize="9" fill="#4b5563">Entry position</text>
        </g>
      )}
    </g>
  );
}

function ExitMarker({ x, y, price, quantity, date }) {
  const [hovered, setHovered] = useState(false);
  const label = `${quantity > 1 ? `×${quantity} ` : ''}${formatCurrency(price)}`;
  const dateStr = new Date(date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <g transform={`translate(${x},${y})`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ cursor: 'pointer' }}>
      {/* Arrow shaft */}
      <line x1="0" y1="8" x2="0" y2="28" stroke="#ef4444" strokeWidth="1.5" />
      {/* Arrowhead pointing down (exit = sell) */}
      <polygon points="0,4 -5,14 5,14" fill="#ef4444" />
      {/* Base dot on the price line */}
      <circle cx="0" cy="0" r="3" fill="#ef4444" />

      {hovered && (
        <g transform="translate(8, -48)">
          <rect x="0" y="0" width="130" height="44" rx="6"
            fill="#111827" stroke="#ef4444" strokeWidth="0.5" strokeOpacity="0.6" />
          <text x="8" y="14" fontSize="9" fill="#6b7280">{dateStr}</text>
          <text x="11" y="27" fontSize="11" fontWeight="bold" fill="#ef4444" fontFamily="monospace">
            Sell {label}
          </text>
          <text x="8" y="39" fontSize="9" fill="#4b5563">Position closed</text>
        </g>
      )}
    </g>
  );
}

// ─── Backfill waiting state ───────────────────────────────────────────────────

function BackfillWaiting({ itemId, onReady }) {
  const pollRef = useRef(null);
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    pollRef.current = setInterval(async () => {
      try {
        const status = await portfolioAPI.getBackfillStatus(itemId);
        setAttempts(a => a + 1);
        if (status.has_data) {
          clearInterval(pollRef.current);
          onReady();
        }
      } catch { /* silent */ }
    }, 4000); // poll every 4s

    return () => clearInterval(pollRef.current);
  }, [itemId, onReady]);

  return (
    <div className="flex flex-col items-center justify-center h-72 gap-4">
      <div className="relative">
        <div className="w-12 h-12 border-2 border-gray-800 rounded-full" />
        <div className="w-12 h-12 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin absolute inset-0" />
      </div>
      <div className="text-center">
        <p className="text-gray-300 text-sm font-medium">Fetching price history</p>
        <p className="text-gray-600 text-xs mt-1">
          Steam data is being collected — this takes up to a minute
        </p>
        {attempts > 10 && (
          <p className="text-gray-700 text-xs mt-1">Still working... Steam rate limits occasionally delay this</p>
        )}
      </div>
      <div className="flex gap-1">
        {[0,1,2].map(i => (
          <div key={i} className="w-1.5 h-1.5 bg-cyan-500/40 rounded-full animate-pulse"
            style={{ animationDelay: `${i * 0.2}s` }} />
        ))}
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function InvestmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [investment, setInvestment] = useState(null);
  const [positions, setPositions]   = useState([]);   // all user positions for this item
  const [chartData, setChartData]   = useState([]);
  const [selectedResolution, setSelectedResolution] = useState(RESOLUTIONS[2]);
  const [loading, setLoading]       = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  const [isQueued, setIsQueued]     = useState(false); // backfill queued, no data yet

  // Alert state
  const [alerts, setAlerts]         = useState([]);
  const [alertMarket, setAlertMarket]       = useState('steam');
  const [alertDirection, setAlertDirection] = useState('below');
  const [alertPrice, setAlertPrice]         = useState('');
  const [alertLoading, setAlertLoading]     = useState(false);
  const isPro = user?.tier === 'pro';

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

  const fetchPositions = useCallback(async (itemId) => {
    try {
      const data = await investmentsAPI.getByItem(itemId);
      setPositions(data.positions || []);
    } catch { /* non-critical */ }
  }, []);

  const fetchChart = useCallback(async (inv, resolution) => {
    if (!inv?.item_id) return;
    setChartLoading(true);
    setIsQueued(false);
    try {
      const data = await portfolioAPI.getPriceHistory(
        inv.item_id, 'steam', resolution.resolution, resolution.days
      );

      // No candles yet — check if queued
      if (!data.candles?.length) {
        if (data.queued_for_backfill || data.backfilled) {
          setIsQueued(true);
        }
        setChartData([]);
        return;
      }

      setChartData(data.candles.map(c => ({
        date: new Date(c.timestamp).toLocaleDateString('en-GB', {
          day: 'numeric', month: 'short',
          ...(resolution.resolution === 'hourly' ? { hour: '2-digit', minute: '2-digit' } : {}),
        }),
        rawTimestamp: new Date(c.timestamp).getTime(),
        value: c.close,
        volume: c.volume || 0,
      })));
    } catch {
      toast.error('Failed to load price history');
      setChartData([]);
    } finally {
      setChartLoading(false);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    if (!isPro) return;
    try {
      const data = await alertsAPI.list();
      setAlerts(data);
    } catch {}
  }, [isPro]);

  const handleCreateAlert = async () => {
    if (!alertPrice || parseFloat(alertPrice) <= 0) return toast.error('Enter a valid price');
    setAlertLoading(true);
    try {
      await alertsAPI.create({
        item_id: investment.item_id,
        market: alertMarket,
        target_price: parseFloat(alertPrice),
        direction: alertDirection,
      });
      toast.success('Alert created');
      setAlertPrice('');
      fetchAlerts();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create alert');
    }
    setAlertLoading(false);
  };

  const handleDeleteAlert = async (alertId) => {
    try {
      await alertsAPI.delete(alertId);
      setAlerts(prev => prev.filter(a => a.id !== alertId));
      toast.success('Alert removed');
    } catch {
      toast.error('Failed to remove alert');
    }
  };

  useEffect(() => { fetchInvestment(); }, [fetchInvestment]);

  useEffect(() => {
    if (!investment) return;
    fetchChart(investment, selectedResolution);
    fetchPositions(investment.item_id);
    fetchAlerts();
  }, [investment]);

  // When backfill completes, reload chart
  const handleBackfillReady = useCallback(() => {
    setIsQueued(false);
    if (investment) fetchChart(investment, selectedResolution);
  }, [investment, selectedResolution, fetchChart]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const item     = investment?.item;
  const prices   = investment?.prices || {};
  const steamPrice   = prices.steam?.price;
  const csfloatPrice = prices.csfloat?.price;
  const buffPrice    = prices.buff163?.price;
  const pnlPos = (investment?.profit_loss || 0) >= 0;

  // DCA summary across all positions
  const totalQty = positions.reduce((s, p) => s + p.quantity, 0);
  const avgEntry = positions.length > 1
    ? positions.reduce((s, p) => s + p.purchase_price * p.quantity, 0) / totalQty
    : null;

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
                  {positions.length > 1 && (
                    <span className="text-xs text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded border border-cyan-400/20">
                      DCA · {positions.length} positions
                    </span>
                  )}
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
            {
              label: positions.length > 1 ? 'Your Position (DCA)' : 'Your Position',
              sub: positions.length > 1
                ? `${totalQty}× avg ${formatCurrency(avgEntry)}`
                : `${investment?.quantity}× @ ${formatCurrency(investment?.purchase_price)}`,
              value: formatCurrency(investment?.total_invested),
              color: 'text-white',
            },
            { label: 'Steam Price',  sub: 'Real sales · P&L basis',   value: steamPrice   ? formatCurrency(steamPrice)   : '—', color: 'text-cyan-400',   badge: 'Steam'   },
            { label: 'CSFloat',      sub: 'Sell for (USD)',            value: csfloatPrice ? formatCurrency(csfloatPrice) : '—', color: 'text-blue-400',   badge: 'CSFloat' },
            { label: 'Buff163',      sub: 'Sell for (USD equiv.)',     value: buffPrice    ? formatCurrency(buffPrice)    : '—', color: 'text-orange-400', badge: 'Buff'    },
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

        {/* DCA breakdown — only shown when multiple positions */}
        {positions.length > 1 && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-white font-semibold">DCA Positions</h3>
                <p className="text-gray-500 text-xs mt-0.5">
                  {positions.length} entries · avg {formatCurrency(avgEntry)} · {totalQty} total
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">Weighted avg entry</p>
                <p className="text-lg font-bold font-mono text-cyan-400">{formatCurrency(avgEntry)}</p>
              </div>
            </div>
            <div className="space-y-2">
              {positions.map((pos, i) => {
                const posRoi = steamPrice
                  ? ((steamPrice - pos.purchase_price) / pos.purchase_price * 100)
                  : null;
                const posPos = (posRoi || 0) >= 0;
                const held = holdingLabel(pos.purchase_date, pos.sold_at);
                return (
                  <div key={pos.id} className="flex items-center justify-between p-3 bg-gray-800/40 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className={`w-1.5 h-8 rounded-full ${pos.status === 'sold' ? 'bg-red-500/50' : 'bg-emerald-500/50'}`} />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-300 text-sm font-mono font-medium">
                            {formatCurrency(pos.purchase_price)}
                          </span>
                          <span className="text-gray-600 text-xs">×{pos.quantity}</span>
                          {pos.status === 'sold' && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">sold</span>
                          )}
                        </div>
                        <p className="text-gray-600 text-xs mt-0.5">
                          {pos.purchase_date
                            ? new Date(pos.purchase_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
                            : '—'}
                          {held && ` · ${held}`}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      {posRoi !== null ? (
                        <>
                          <p className={`text-sm font-mono font-medium ${posPos ? 'text-emerald-400' : 'text-red-400'}`}>
                            {posPos ? '+' : ''}{posRoi.toFixed(2)}%
                          </p>
                          <p className={`text-xs font-mono ${posPos ? 'text-emerald-600' : 'text-red-600'}`}>
                            {posPos ? '+' : ''}{formatCurrency((steamPrice - pos.purchase_price) * pos.quantity)}
                          </p>
                        </>
                      ) : (
                        <span className="text-gray-600 text-sm">—</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Chart */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <div>
              <h3 className="text-white font-semibold">Price History</h3>
              {!chartLoading && !isQueued && chartData.length > 0 && (
                <p className="text-gray-700 text-xs mt-0.5">
                  {chartData.length} data points · Steam Market · {selectedResolution.resolution}
                  {positions.length > 0 && ' · trade markers shown'}
                </p>
              )}
            </div>
            <div className="flex bg-gray-800 rounded-xl p-1 gap-1">
              {RESOLUTIONS.map(res => (
                <button key={res.label}
                  onClick={() => {
                    setSelectedResolution(res);
                    if (!isQueued) fetchChart(investment, res);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    selectedResolution.label === res.label
                      ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20'
                      : 'text-gray-500 hover:text-gray-300'
                  }`}>
                  {res.label}
                </button>
              ))}
            </div>
          </div>

          {chartLoading ? (
            <div className="flex items-center justify-center h-72">
              <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : isQueued ? (
            <BackfillWaiting itemId={investment?.item_id} onReady={handleBackfillReady} />
          ) : chartData.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-72 text-gray-600 gap-2">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4" />
              </svg>
              <p className="text-sm">No price history available</p>
              <p className="text-xs text-gray-700">Steam may not have data for this item</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart
                data={chartData}
                margin={{ top: 10, right: 70, bottom: 5, left: 0 }}
              >
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#06b6d4" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}   />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  axisLine={false} tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  axisLine={false} tickLine={false}
                  tickFormatter={v => formatCurrency(v, null, true)}
                  width={60}
                  domain={[dataMin => Math.min(dataMin, avgEntry || investment?.purchase_price || dataMin) * 0.95, 'auto']}
                />
                <Tooltip content={<ChartTooltip />} />

                {/* Weighted average entry line — DCA only */}
                {avgEntry && (
                  <ReferenceLine
                    y={avgEntry}
                    stroke="#10b981"
                    strokeDasharray="5 3"
                    strokeOpacity={0.7}
                    label={{ value: `▲ avg entry ${formatCurrency(avgEntry)}`, position: 'right', fill: '#10b981', fontSize: 10, fontWeight: 'bold' }}
                  />
                )}

                {/* Single position entry line */}
                {!avgEntry && investment?.purchase_price && (
                  <ReferenceLine
                    y={investment.purchase_price}
                    stroke="#10b981"
                    strokeDasharray="5 3"
                    strokeOpacity={0.7}
                    label={{ value: `▲ entry ${formatCurrency(investment.purchase_price)}${investment.quantity > 1 ? ` ×${investment.quantity}` : ''}`, position: 'right', fill: '#10b981', fontSize: 10, fontWeight: 'bold' }}
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

                {/* Trade markers overlay */}
                <Customized component={(props) => (
                  <TradeMarkers
                    chartData={chartData}
                    positions={positions}
                    xAxisMap={props.xAxisMap}
                    yAxisMap={props.yAxisMap}
                  />
                )} />
              </AreaChart>
            </ResponsiveContainer>
          )}

          {!isQueued && chartData.length > 0 && (
            <div className="flex items-center justify-between mt-3">
              <p className="text-xs text-gray-700">
                Steam Market · Median sale price per {selectedResolution.resolution}
              </p>
              {positions.length > 0 && (
                <div className="flex items-center gap-3 text-xs text-gray-600">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full inline-block" />
                    Buy
                  </span>
                  {positions.some(p => p.status === 'sold') && (
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 bg-red-500 rounded-full inline-block" />
                      Sell
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Details */}
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-4">Position Details</h3>
            {[
              { label: 'Quantity',       value: `${investment?.quantity}×` },
              { label: 'Purchase Price', value: formatCurrency(investment?.purchase_price) },
              { label: 'Total Invested', value: formatCurrency(investment?.total_invested) },
              { label: 'Current Value',  value: investment?.current_value ? formatCurrency(investment.current_value) : '—' },
              { label: 'Unrealised P&L', value: investment?.profit_loss !== null ? `${pnlPos?'+':''}${formatCurrency(investment.profit_loss)}` : '—', color: pnlPos ? 'text-emerald-400' : 'text-red-400' },
              { label: 'ROI',            value: investment?.roi !== null ? `${pnlPos?'+':''}${(investment.roi||0).toFixed(2)}%` : '—', color: pnlPos ? 'text-emerald-400' : 'text-red-400' },
              { label: 'Held for',       value: holdingLabel(investment?.purchase_date) || '—' },
              { label: 'Purchase Date',  value: investment?.purchase_date ? new Date(investment.purchase_date).toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'numeric' }) : '—' },
              { label: 'Float Value',    value: investment?.wear_value ? investment.wear_value.toFixed(8) : '—' },
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
                  { label: 'Steam Market', dot: 'bg-cyan-400',    color: 'text-cyan-400',    price: steamPrice   ? formatCurrency(steamPrice)   : null, sub: 'Real sale data · P&L basis' },
                  { label: 'CSFloat',      dot: 'bg-blue-400',    color: 'text-blue-400',    price: csfloatPrice ? formatCurrency(csfloatPrice) : null, sub: 'Sell instantly (USD)'       },
                  { label: 'Buff163',      dot: 'bg-orange-400',  color: 'text-orange-400',  price: buffPrice    ? formatCurrency(buffPrice)    : null, sub: 'Sell instantly (USD equiv.)' },
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

            {/* Price Alerts */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-4">Price Alerts</h3>
              {!isPro ? (
                <div className="text-center py-2">
                  <p className="text-gray-500 text-sm mb-3">Price alerts are a Pro feature</p>
                  <button onClick={() => navigate('/app/billing')}
                    className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm rounded-lg hover:bg-cyan-500/20 transition-colors">
                    Upgrade to Pro
                  </button>
                </div>
              ) : (
                <>
                  {/* Existing active alerts for this item */}
                  {alerts.filter(a => a.item_id === investment?.item_id && a.is_active).map(a => (
                    <div key={a.id} className="flex items-center justify-between p-3 bg-gray-800/40 rounded-xl mb-2">
                      <div>
                        <p className="text-gray-300 text-sm font-mono">
                          {a.direction === 'above' ? '↑ above' : '↓ below'} ${a.target_price.toFixed(2)}
                        </p>
                        <p className="text-gray-600 text-xs">{a.market.toUpperCase()}</p>
                      </div>
                      <button onClick={() => handleDeleteAlert(a.id)}
                        className="text-gray-600 hover:text-red-400 transition-colors">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}

                  {/* Create new alert */}
                  <div className="space-y-2 mt-1">
                    <div className="grid grid-cols-2 gap-2">
                      <select value={alertMarket} onChange={e => setAlertMarket(e.target.value)}
                        className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500">
                        <option value="steam">Steam</option>
                        <option value="csfloat">CSFloat</option>
                        <option value="buff163">Buff163</option>
                      </select>
                      <select value={alertDirection} onChange={e => setAlertDirection(e.target.value)}
                        className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500">
                        <option value="below">↓ drops below</option>
                        <option value="above">↑ rises above</option>
                      </select>
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={alertPrice}
                        onChange={e => setAlertPrice(e.target.value)}
                        placeholder="Target price (USD)"
                        step="0.01" min="0"
                        className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-500 transition-colors"
                      />
                      <button
                        onClick={handleCreateAlert}
                        disabled={alertLoading || !alertPrice}
                        className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-500 text-black text-sm font-semibold rounded-lg transition-colors"
                      >
                        {alertLoading ? '...' : 'Set'}
                      </button>
                    </div>
                    <p className="text-gray-700 text-xs">
                      Checked every 30 min · in-app notification on trigger
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-800 py-6 px-6 mt-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-700">
          <span>Floatbase · Steam Market, Buff163 & CSFloat</span>
          <div className="flex gap-5">
            <a href="/privacy" className="hover:text-gray-500">Privacy</a>
            <a href="/terms" className="hover:text-gray-500">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
