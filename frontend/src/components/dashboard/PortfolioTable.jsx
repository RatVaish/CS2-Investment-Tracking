import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { investmentsAPI } from '../../api/investments';
import { formatCurrency, formatCNY } from '../../utils/currency';

const SORT_KEYS = {
  name: (a, b) => (a.item?.market_hash_name || '').localeCompare(b.item?.market_hash_name || ''),
  value: (a, b) => (b.current_value || 0) - (a.current_value || 0),
  pnl: (a, b) => (b.profit_loss || 0) - (a.profit_loss || 0),
  roi: (a, b) => (b.roi || 0) - (a.roi || 0),
  invested: (a, b) => b.total_invested - a.total_invested,
};

function RarityBadge({ rarity }) {
  const colors = {
    'Consumer Grade': 'text-gray-400 bg-gray-800',
    'Industrial Grade': 'text-blue-400 bg-blue-900/30',
    'Mil-Spec Grade': 'text-blue-400 bg-blue-900/30',
    'Restricted': 'text-purple-400 bg-purple-900/30',
    'Classified': 'text-pink-400 bg-pink-900/30',
    'Covert': 'text-red-400 bg-red-900/30',
    'Contraband': 'text-amber-400 bg-amber-900/30',
    'Extraordinary': 'text-amber-400 bg-amber-900/30',
  };
  const cls = colors[rarity] || 'text-gray-500 bg-gray-800';
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${cls}`}>
      {rarity || '—'}
    </span>
  );
}

export default function PortfolioTable() {
  const navigate = useNavigate();
  const [investments, setInvestments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('value');
  const [sortDir, setSortDir] = useState(1);
  const [filter, setFilter] = useState('active');
  const [search, setSearch] = useState('');
  const [deleting, setDeleting] = useState(null);

  const fetchInvestments = useCallback(async () => {
    try {
      const data = await investmentsAPI.getAll(filter);
      setInvestments(data);
    } catch (err) {
      toast.error('Failed to load investments');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { fetchInvestments(); }, [fetchInvestments]);

  useEffect(() => {
    const handler = () => fetchInvestments();
    window.addEventListener('currencychange', handler);
    return () => window.removeEventListener('currencychange', handler);
  }, [fetchInvestments]);

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d * -1);
    else { setSortKey(key); setSortDir(1); }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!confirm('Delete this investment?')) return;
    setDeleting(id);
    try {
      await investmentsAPI.delete(id);
      setInvestments(prev => prev.filter(inv => inv.id !== id));
      toast.success('Investment deleted');
    } catch {
      toast.error('Failed to delete');
    } finally {
      setDeleting(null);
    }
  };

  const filtered = investments
    .filter(inv => {
      if (!search) return true;
      return (inv.item?.market_hash_name || '').toLowerCase().includes(search.toLowerCase());
    })
    .sort((a, b) => (SORT_KEYS[sortKey]?.(a, b) || 0) * sortDir);

  const totalValue = filtered.reduce((s, inv) => s + (inv.current_value || 0), 0);
  const totalInvested = filtered.reduce((s, inv) => s + inv.total_invested, 0);
  const totalPnl = filtered.reduce((s, inv) => s + (inv.profit_loss || 0), 0);

  const SortIcon = ({ col }) => (
    <svg
      className={`w-3 h-3 inline ml-1 transition-colors ${sortKey === col ? 'text-cyan-400' : 'text-gray-700'}`}
      fill="none" viewBox="0 0 24 24" stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d={sortKey === col && sortDir === -1 ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"}
      />
    </svg>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header + controls */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Portfolio Holdings</h2>
          <p className="text-gray-500 text-sm mt-0.5">{filtered.length} investments · Click any row to view chart</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {/* Status filter */}
          <div className="flex bg-gray-800 rounded-xl p-1 gap-1">
            {['active', 'sold'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize ${
                  filter === f ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          {/* Search */}
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search items..."
            className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-xl text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-600 w-44"
          />
        </div>
      </div>

      {/* Summary bar */}
      {filtered.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Total Invested', value: formatCurrency(totalInvested) },
            { label: 'Current Value', value: formatCurrency(totalValue) },
            { label: 'P&L', value: `${totalPnl >= 0 ? '+' : ''}${formatCurrency(totalPnl)}`, color: totalPnl >= 0 ? 'text-emerald-400' : 'text-red-400' },
          ].map(s => (
            <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
              <div className="text-xs text-gray-500 mb-1">{s.label}</div>
              <div className={`font-bold font-mono ${s.color || 'text-white'}`}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-16 text-center">
          <div className="w-12 h-12 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <p className="text-gray-400 font-medium">No investments found</p>
          <p className="text-gray-600 text-sm mt-1">
            {search ? 'Try a different search' : 'Add your first investment to get started'}
          </p>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="px-4 py-3 text-left text-xs text-gray-500 font-medium uppercase tracking-wider">
                    Item
                  </th>
                  <th
                    onClick={() => handleSort('invested')}
                    className="px-4 py-3 text-right text-xs text-gray-500 font-medium uppercase tracking-wider cursor-pointer hover:text-gray-300"
                  >
                    Bought <SortIcon col="invested" />
                  </th>
                  <th
                    onClick={() => handleSort('value')}
                    className="px-4 py-3 text-right text-xs text-gray-500 font-medium uppercase tracking-wider cursor-pointer hover:text-gray-300"
                  >
                    Value <SortIcon col="value" />
                  </th>
                  <th className="px-4 py-3 text-right text-xs text-gray-500 font-medium uppercase tracking-wider">
                    Sell For
                  </th>
                  <th
                    onClick={() => handleSort('pnl')}
                    className="px-4 py-3 text-right text-xs text-gray-500 font-medium uppercase tracking-wider cursor-pointer hover:text-gray-300"
                  >
                    P&L <SortIcon col="pnl" />
                  </th>
                  <th
                    onClick={() => handleSort('roi')}
                    className="px-4 py-3 text-right text-xs text-gray-500 font-medium uppercase tracking-wider cursor-pointer hover:text-gray-300"
                  >
                    ROI <SortIcon col="roi" />
                  </th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {filtered.map(inv => {
                  const pnlPos = (inv.profit_loss || 0) >= 0;
                  const csfloatPrice = inv.prices?.csfloat?.price;
                  const buffPrice = inv.prices?.buff163?.price;

                  return (
                    <tr
                      key={inv.id}
                      onClick={() => navigate(`/investments/${inv.id}`)}
                      className="hover:bg-gray-800/40 cursor-pointer transition-colors group"
                    >
                      {/* Item */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gray-800 rounded-lg overflow-hidden shrink-0 border border-gray-700">
                            {inv.item?.image_url ? (
                              <img
                                src={inv.item.image_url}
                                alt=""
                                className="w-full h-full object-contain"
                                onError={(e) => { e.target.style.display = 'none'; }}
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-700">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                                </svg>
                              </div>
                            )}
                          </div>
                          <div className="min-w-0">
                            <div className="text-white text-sm font-medium truncate max-w-[200px]">
                              {inv.item?.market_hash_name || 'Unknown'}
                            </div>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className="text-gray-600 text-xs">×{inv.quantity}</span>
                              <RarityBadge rarity={inv.item?.rarity} />
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Bought */}
                      <td className="px-4 py-3 text-right">
                        <div className="text-gray-300 text-sm font-mono">
                          {formatCurrency(inv.purchase_price)}
                        </div>
                        <div className="text-gray-600 text-xs font-mono">
                          {formatCurrency(inv.total_invested)} total
                        </div>
                      </td>

                      {/* Current value (Steam) */}
                      <td className="px-4 py-3 text-right">
                        {inv.current_price ? (
                          <div>
                            <div className="text-white text-sm font-mono font-medium">
                              {formatCurrency(inv.current_value)}
                            </div>
                            <div className="text-gray-500 text-xs font-mono">
                              {formatCurrency(inv.current_price)} ea
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>

                      {/* Sell for (CSFloat + Buff) */}
                      <td className="px-4 py-3 text-right">
                        <div className="space-y-0.5">
                          {csfloatPrice && (
                            <div className="flex items-center justify-end gap-1.5">
                              <span className="text-[10px] text-cyan-600 font-medium">CF</span>
                              <span className="text-gray-300 text-xs font-mono">{formatCurrency(csfloatPrice)}</span>
                            </div>
                          )}
                          {buffPrice && (
                            <div className="flex items-center justify-end gap-1.5">
                              <span className="text-[10px] text-orange-600 font-medium">B</span>
                              <span className="text-gray-500 text-xs font-mono">{formatCNY(buffPrice)}</span>
                            </div>
                          )}
                          {!csfloatPrice && !buffPrice && <span className="text-gray-600">—</span>}
                        </div>
                      </td>

                      {/* P&L */}
                      <td className="px-4 py-3 text-right">
                        {inv.profit_loss !== null ? (
                          <span className={`text-sm font-mono font-medium ${pnlPos ? 'text-emerald-400' : 'text-red-400'}`}>
                            {pnlPos ? '+' : ''}{formatCurrency(inv.profit_loss)}
                          </span>
                        ) : <span className="text-gray-600">—</span>}
                      </td>

                      {/* ROI */}
                      <td className="px-4 py-3 text-right">
                        {inv.roi !== null ? (
                          <span className={`text-sm font-mono font-medium ${inv.roi >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {inv.roi >= 0 ? '+' : ''}{inv.roi.toFixed(2)}%
                          </span>
                        ) : <span className="text-gray-600">—</span>}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity justify-end">
                          <button
                            onClick={(e) => handleDelete(e, inv.id)}
                            disabled={deleting === inv.id}
                            className="p-1.5 rounded-lg hover:bg-red-500/10 text-gray-600 hover:text-red-400 transition-colors"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                          <svg className="w-3.5 h-3.5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
