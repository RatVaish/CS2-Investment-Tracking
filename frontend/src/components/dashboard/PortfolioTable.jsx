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
      item_name: investment.item_name,
      item_type: investment.item_type,
      purchase_price: investment.purchase_price,
      quantity: investment.quantity
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const saveEdit = async (id) => {
    try {
      const updated = await investmentsAPI.update(id, editForm);
      setInvestments(investments.map(inv => inv.id === id ? updated : inv));
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

  const calculateProfitLoss = (investment) => {
    if (!investment.current_price) return null;
    return (investment.current_price - investment.purchase_price) * investment.quantity;
  };

  const calculateROI = (investment) => {
    if (!investment.current_price || investment.purchase_price === 0) return null;
    return ((investment.current_price - investment.purchase_price) / investment.purchase_price) * 100;
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
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Type
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
                    <td className="px-6 py-4">
                      {editingId === investment.id ? (
                        <input
                          type="text"
                          value={editForm.item_name}
                          onChange={(e) => setEditForm({...editForm, item_name: e.target.value})}
                          className="w-full px-2 py-1 bg-gray-900 border border-gray-600 rounded text-white text-sm"
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <div className="text-white font-medium">{investment.item_name}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs uppercase">
                        {investment.item_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-white">
                      {editingId === investment.id ? (
                        <input
                          type="number"
                          value={editForm.purchase_price}
                          onChange={(e) => setEditForm({...editForm, purchase_price: parseFloat(e.target.value)})}
                          className="w-24 px-2 py-1 bg-gray-900 border border-gray-600 rounded text-white text-sm text-right"
                          onClick={(e) => e.stopPropagation()}
                          step="0.01"
                        />
                      ) : (
                        `£${investment.purchase_price.toFixed(2)}`
                      )}
                    </td>
                    <td className="px-6 py-4 text-right text-white">
                      {investment.current_price ? `£${investment.current_price.toFixed(2)}` : '-'}
                    </td>
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
                    <td className="px-6 py-4 text-right">
                      {(() => {
                        const pl = calculateProfitLoss(investment);
                        if (pl === null) return <span className="text-gray-500">-</span>;
                        const isPositive = pl >= 0;
                        return (
                          <span className={isPositive ? 'text-green-400' : 'text-red-400'}>
                            {isPositive ? '+' : ''}£{pl.toFixed(2)}
                          </span>
                        );
                      })()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {(() => {
                        const roi = calculateROI(investment);
                        if (roi === null) return <span className="text-gray-500">-</span>;
                        const isPositive = roi >= 0;
                        return (
                          <span className={isPositive ? 'text-green-400' : 'text-red-400'}>
                            {isPositive ? '+' : ''}{roi.toFixed(2)}%
                          </span>
                        );
                      })()}
                    </td>
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

                  {/* Expanded Row (Chart Placeholder) */}
                  {expandedRow === investment.id && (
                    <tr>
                      <td colSpan="8" className="px-6 py-6 bg-gray-900/50">
                        <div className="border border-gray-700 rounded-lg p-8 text-center">
                          <p className="text-gray-400 mb-2">Price Chart</p>
                          <p className="text-gray-500 text-sm">
                            Candlestick chart will be displayed here (Coming in v3)
                          </p>
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