import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { investmentsAPI } from '../../api/investments';
import PurchaseDatePicker from './PurchaseDatePicker';

export default function EditInvestmentModal({ investment, onClose, onSaved }) {
  const [form, setForm] = useState({
    purchase_price: '',
    quantity: '',
    purchase_date: '',
    notes: '',
    target_price: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!investment) return;
    setForm({
      purchase_price: investment.purchase_price ?? '',
      quantity: investment.quantity ?? 1,
      purchase_date: investment.purchase_date
        ? new Date(investment.purchase_date).toISOString().slice(0, 16)
        : '',
      notes: investment.notes ?? '',
      target_price: investment.target_price ?? '',
    });
  }, [investment]);

  const set = (field) => (e) => setForm(prev => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await investmentsAPI.update(investment.id, {
        purchase_price: parseFloat(form.purchase_price),
        quantity: parseInt(form.quantity),
        purchase_date: form.purchase_date || null,
        notes: form.notes || null,
        target_price: form.target_price ? parseFloat(form.target_price) : null,
      });
      toast.success('Investment updated');
      onSaved?.();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update investment');
    } finally {
      setLoading(false);
    }
  };

  if (!investment) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <div>
            <h2 className="text-white font-semibold">Edit Investment</h2>
            <p className="text-gray-500 text-xs mt-0.5 truncate max-w-[280px]">
              {investment.item?.market_hash_name}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 transition-colors p-1">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Purchase Price (USD)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={form.purchase_price}
                onChange={set('purchase_price')}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Quantity</label>
              <input
                type="number"
                min="1"
                step="1"
                value={form.quantity}
                onChange={set('quantity')}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div>
            <PurchaseDatePicker
            value={form.purchase_date}
            onChange={(iso) => setForm(prev => ({ ...prev, purchase_date: iso }))}
            itemId={investment?.item_id}
            purchasePrice={parseFloat(form.purchase_price) || 0}
          />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1.5">
              Target Price (USD) <span className="text-gray-600">— optional</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.target_price}
              onChange={set('target_price')}
              placeholder="Set a sell target..."
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500 placeholder-gray-600 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1.5">
              Notes <span className="text-gray-600">— optional</span>
            </label>
            <textarea
              rows={2}
              value={form.notes}
              onChange={set('notes')}
              placeholder="Any notes about this investment..."
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500 placeholder-gray-600 resize-none"
            />
          </div>

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2.5 bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl text-sm font-semibold transition-colors"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
