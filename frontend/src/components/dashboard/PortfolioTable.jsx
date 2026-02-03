import React, { useState, useEffect } from 'react';
import { investmentsAPI } from '../../api/investments';

function PortfolioTable() {
  const [investments, setInvestments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedRow, setExpandedRow] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    fetchInvestments();
  }, []);

  const fetchInvestments = async () => {
    try {
      const data = await investmentsAPI.getAll();
      setInvestments(data);
      setError('');
    } catch (err) {
      console.error('Failed to fetch investments:', err);
      setError('Failed to load investments');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this investment?')) {
      return;
    }

    try {
      await investmentsAPI.delete(id);
      setInvestments(investments.filter(inv => inv.id !== id));
    } catch (err) {
      console.error('Failed to delete investment:', err);
      alert('Failed to delete investment');
    }
  };

  const startEdit = (investment) => {
    setEditingId(investment.id);
    setEditForm({
      purchase_price: investment.purchase_price,
      quantity: investment.quantity,
      notes: investment.notes || ''
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const saveEdit = async (id) => {
    try {
      await investmentsAPI.update(id, editForm);
      await fetchInvestments(); // Refetch to get updated data with recalculated P&L
      setEditingId(null);
      setEditForm({});
    } catch (err) {
      console.error('Failed to update investment:', err);
      alert('Failed to update investment');
    }
  };

  const toggleExpand = (id) => {
    setExpandedRow(expandedRow === id ? null : id);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-400">Loading investments...</div>
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

  if (investments.length === 0) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-12 text-center">
        <p className="text-gray-400 text-lg mb-4">No investments yet</p>
        <p className="text-gray-500">Add your first investment to get started</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-6">Portfolio Holdings</h2>

      <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-900/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Item
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Purchase Price
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Total Value
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  ROI
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {investments.map((investment) => (
                <React.Fragment key={investment.id}>
                  {/* Main Row */}
                  <tr
                    className="hover:bg-gray-700/30 transition-colors cursor-pointer"
                    onClick={() => toggleExpand(investment.id)}
                  >
                    {/* Item Name & Image */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <img
                          src={investment.item?.image_url || 'https://via.placeholder.com/48/1f2937/ffffff?text=CS2'}
                          alt={investment.item?.market_hash_name || 'Item'}
                          className="w-12 h-12 object-contain bg-gray-900 rounded border border-gray-700"
                          onError={(e) => {
                            e.target.src = 'https://via.placeholder.com/48/1f2937/ffffff?text=CS2';
                          }}
                        />
                        <div>
                          <div className="text-white font-medium">
                            {investment.item?.market_hash_name || 'Unknown Item'}
                          </div>
                          <div className="text-gray-500 text-xs">
                            {investment.item?.item_type || 'Unknown'}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Purchase Price */}
                    <td className="px-6 py-4 text-right text-white">
                      {editingId === investment.id ? (
                        <input
                          type="number"
                          value={editForm.purchase_price}
                          onChange={(e) => setEditForm({...editForm, purchase_price: parseFloat(e.target.value)})}
                          className="w-24 px-2 py-1 bg-gray-900 border border-gray-600 rounded text-white text-sm text-right"
                          onClick={(e) => e.stopPropagation()}
                          step="0.01"
                          min="0"
                        />
                      ) : (
                        `£${investment.purchase_price.toFixed(2)}`
                      )}
                    </td>

                    {/* Current Price (CSFloat) */}
                    <td className="px-6 py-4 text-right">
                      {investment.csfloat_price?.csfloat_price ? (
                        <div>
                          <div className="text-white">
                            £{investment.csfloat_price.csfloat_price.toFixed(2)}
                          </div>
                          <div className="text-xs text-cyan-400">CSFloat</div>
                        </div>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </td>

                    {/* Quantity */}
                    <td className="px-6 py-4 text-right text-white">
                      {editingId === investment.id ? (
                        <input
                          type="number"
                          value={editForm.quantity}
                          onChange={(e) => setEditForm({...editForm, quantity: parseInt(e.target.value)})}
                          className="w-16 px-2 py-1 bg-gray-900 border border-gray-600 rounded text-white text-sm text-right"
                          onClick={(e) => e.stopPropagation()}
                          min="1"
                        />
                      ) : (
                        investment.quantity
                      )}
                    </td>

                    {/* Total Value */}
                    <td className="px-6 py-4 text-right text-white font-medium">
                      {investment.csfloat_price?.csfloat_price ? (
                        `£${(investment.csfloat_price.csfloat_price * investment.quantity).toFixed(2)}`
                      ) : (
                        '-'
                      )}
                    </td>

                    {/* Profit/Loss */}
                    <td className="px-6 py-4 text-right">
                      {investment.profit_loss !== null && investment.profit_loss !== undefined ? (
                        <span className={`font-medium ${investment.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {investment.profit_loss >= 0 ? '+' : ''}£{investment.profit_loss.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </td>

                    {/* ROI */}
                    <td className="px-6 py-4 text-right">
                      {investment.roi !== null && investment.roi !== undefined ? (
                        <span className={`font-medium ${investment.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {investment.roi >= 0 ? '+' : ''}{investment.roi.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      {editingId === investment.id ? (
                        <div className="flex justify-end space-x-2">
                          <button
                            onClick={() => saveEdit(investment.id)}
                            className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                          >
                            Save
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex justify-end space-x-2">
                          <button
                            onClick={() => startEdit(investment)}
                            className="px-3 py-1 bg-cyan-600 hover:bg-cyan-700 text-white rounded text-sm transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(investment.id)}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>

                  {/* Expanded Row (Details) */}
                  {expandedRow === investment.id && (
                    <tr>
                      <td colSpan="8" className="px-6 py-6 bg-gray-900/50">
                        <div className="border border-gray-700 rounded-lg p-6">
                          <h3 className="text-lg font-semibold text-white mb-4">Investment Details</h3>
                          <div className="grid grid-cols-2 gap-6">
                            {/* Left Column */}
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <span className="text-gray-400">Item ID:</span>
                                <span className="text-white">{investment.item_id}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">Purchase Date:</span>
                                <span className="text-white">{formatDate(investment.purchase_date)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">Total Invested:</span>
                                <span className="text-white font-medium">
                                  £{(investment.purchase_price * investment.quantity).toFixed(2)}
                                </span>
                              </div>

                              {/* Price Sources */}
                              <div className="pt-3 border-t border-gray-700">
                                <span className="text-gray-400 block mb-2">Price Sources:</span>
                                <div className="space-y-1 text-sm">
                                  {investment.item?.csfloat_price && (
                                    <div className="flex justify-between">
                                      <span className="text-cyan-400">CSFloat:</span>
                                      <span className="text-white">£{investment.item.csfloat_price.toFixed(2)}</span>
                                    </div>
                                  )}
                                  {investment.item?.buff_price && (
                                    <div className="flex justify-between">
                                      <span className="text-orange-400">Buff163:</span>
                                      <span className="text-white">£{investment.item.buff_price.toFixed(2)}</span>
                                    </div>
                                  )}
                                  {investment.item?.steam_price && (
                                    <div className="flex justify-between">
                                      <span className="text-blue-400">Steam:</span>
                                      <span className="text-white">£{investment.item.steam_price.toFixed(2)}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Right Column */}
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <span className="text-gray-400">Created:</span>
                                <span className="text-white text-sm">{formatDate(investment.created_at)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">Last Updated:</span>
                                <span className="text-white text-sm">{formatDate(investment.updated_at)}</span>
                              </div>
                            </div>
                          </div>

                          {/* Notes */}
                          {investment.notes && (
                            <div className="mt-4 pt-4 border-t border-gray-700">
                              <span className="text-gray-400 block mb-2">Notes:</span>
                              <p className="text-white text-sm">{investment.notes}</p>
                            </div>
                          )}

                          {/* Price Chart Placeholder */}
                          <div className="mt-6 pt-6 border-t border-gray-700">
                            <h4 className="text-white font-medium mb-4">7-Day Price History</h4>
                            <div className="flex items-center justify-center h-48 border border-gray-700 rounded-lg bg-gray-800">
                              <div className="text-center">
                                <p className="text-gray-400 mb-2">Price Chart</p>
                                <p className="text-gray-500 text-sm">
                                  Coming soon - Candlestick chart with 7 days of price data
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default PortfolioTable;
