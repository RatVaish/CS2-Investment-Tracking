import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { investmentsAPI } from '../../api/investments';
import { formatCurrency } from '../../utils/currency';
import ItemSearchSelect from '../ItemSearchSelect';
import PaywallModal from '../PaywallModal';

export default function AddInvestmentForm() {
  const navigate = useNavigate();
  const [selectedItem, setSelectedItem] = useState(null);
  const [form, setForm] = useState({
    item_id: null,
    purchase_price: '',
    quantity: '1',
    purchase_date: new Date().toISOString().slice(0, 16),
    notes: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPaywall, setShowPaywall] = useState(false);

  const handleItemSelect = (itemId, itemData) => {
    setSelectedItem(itemData);
    const steamPrice = itemData?.steam_price;
    setForm(prev => ({
      ...prev,
      item_id: itemId,
      purchase_price: prev.purchase_price === '' && steamPrice
        ? steamPrice.toFixed(2)
        : prev.purchase_price,
    }));
    if (errors.item_id) setErrors(prev => ({ ...prev, item_id: '' }));
  };

  const set = (field) => (e) => {
    setForm(prev => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: '' }));
  };

  const validate = () => {
    const errs = {};
    if (!form.item_id) errs.item_id = 'Select an item';
    if (!form.purchase_price || parseFloat(form.purchase_price) <= 0) errs.purchase_price = 'Enter a valid price';
    if (!form.quantity || parseInt(form.quantity) < 1) errs.quantity = 'Min 1';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setLoading(true);
    try {
      const inv = await investmentsAPI.create({
        item_id: form.item_id,
        purchase_price: parseFloat(form.purchase_price),
        quantity: parseInt(form.quantity),
        purchase_date: form.purchase_date || new Date().toISOString(),
        ...(form.notes && { notes: form.notes }),
      });
      toast.success('Investment added');
      navigate(`/investments/${inv.id}`);
    } catch (err) {
      if (err.response?.status === 403) {
        setShowPaywall(true);
      } else {
        toast.error(err.response?.data?.detail || 'Failed to add investment');
      }
    } finally {
      setLoading(false);
    }
  };

  // Live P&L preview
  const purchasePrice = parseFloat(form.purchase_price) || 0;
  const quantity = parseInt(form.quantity) || 1;
  const steamPrice = selectedItem?.steam_price;
  const pnl = steamPrice && purchasePrice > 0 ? (steamPrice - purchasePrice) * quantity : null;
  const roi = steamPrice && purchasePrice > 0 ? ((steamPrice - purchasePrice) / purchasePrice) * 100 : null;
  const pnlPos = pnl !== null && pnl >= 0;

  return (
    <div className="max-w-xl">
      {showPaywall && <PaywallModal onClose={() => setShowPaywall(false)} />}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-white">Add Investment</h2>
        <p className="text-gray-600 text-sm mt-1">Track a new item in your portfolio</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">

        {/* Item search — full width, prominent */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
          <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Item</p>
          <ItemSearchSelect
            value={form.item_id}
            onChange={handleItemSelect}
            error={errors.item_id}
          />
        </div>

        {/* Price + Quantity row */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
            <label className="block text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">
              Buy Price (USD)
            </label>
            <input
              type="number"
              value={form.purchase_price}
              onChange={set('purchase_price')}
              placeholder={steamPrice ? steamPrice.toFixed(2) : '0.00'}
              step="0.01"
              min="0"
              className={`w-full bg-transparent text-white text-xl font-mono font-semibold placeholder-gray-700
                focus:outline-none border-b pb-1 transition-colors
                ${errors.purchase_price ? 'border-red-500' : 'border-gray-700 focus:border-cyan-500'}`}
            />
            {steamPrice && (
              <p className="text-xs text-gray-600 mt-1.5 font-mono">
                Steam: {formatCurrency(steamPrice)}
              </p>
            )}
            {errors.purchase_price && <p className="text-red-400 text-xs mt-1">{errors.purchase_price}</p>}
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
            <label className="block text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">
              Quantity
            </label>
            <div className="flex items-center gap-2">
              <button type="button"
                onClick={() => setForm(p => ({ ...p, quantity: String(Math.max(1, parseInt(p.quantity || 1) - 1)) }))}
                className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center text-lg transition-colors shrink-0">
                −
              </button>
              <input
                type="number"
                value={form.quantity}
                onChange={set('quantity')}
                min="1"
                className="w-full bg-transparent text-white text-xl font-mono font-semibold text-center focus:outline-none"
              />
              <button type="button"
                onClick={() => setForm(p => ({ ...p, quantity: String(parseInt(p.quantity || 1) + 1) }))}
                className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center text-lg transition-colors shrink-0">
                +
              </button>
            </div>
            {purchasePrice > 0 && (
              <p className="text-xs text-gray-600 mt-1.5 font-mono text-center">
                Total: {formatCurrency(purchasePrice * quantity)}
              </p>
            )}
          </div>
        </div>

        {/* P&L preview — only show if we have a steam price to compare against */}
        {pnl !== null && (
          <div className={`rounded-2xl p-4 border ${pnlPos ? 'border-emerald-500/15 bg-emerald-500/5' : 'border-red-500/15 bg-red-500/5'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 mb-0.5">Estimated P&L at current Steam price</p>
                <p className="text-xs text-gray-600 font-mono">{formatCurrency(steamPrice)} × {quantity}</p>
              </div>
              <div className="text-right">
                <p className={`text-lg font-bold font-mono ${pnlPos ? 'text-emerald-400' : 'text-red-400'}`}>
                  {pnlPos ? '+' : ''}{formatCurrency(pnl)}
                </p>
                <p className={`text-sm font-mono ${pnlPos ? 'text-emerald-500' : 'text-red-500'}`}>
                  {pnlPos ? '+' : ''}{roi?.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Date + Notes — collapsed/minimal */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">
              Purchase Date
            </label>
            <input
              type="datetime-local"
              value={form.purchase_date}
              onChange={set('purchase_date')}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-gray-300 text-sm focus:outline-none focus:border-cyan-500/50 transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">
              Notes <span className="text-gray-700 normal-case font-normal">(optional)</span>
            </label>
            <textarea
              value={form.notes}
              onChange={set('notes')}
              rows={2}
              placeholder="Bought at low, expecting case to rise..."
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-gray-300 text-sm placeholder-gray-700 focus:outline-none focus:border-cyan-500/50 transition-colors resize-none"
            />
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !form.item_id}
          className="w-full py-3 rounded-xl font-semibold text-sm transition-all
            bg-gradient-to-r from-cyan-500 to-blue-600
            hover:from-cyan-400 hover:to-blue-500
            disabled:from-gray-800 disabled:to-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed
            text-white"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin" />
              Adding...
            </span>
          ) : 'Add Investment'}
        </button>
      </form>
    </div>
  );
}
