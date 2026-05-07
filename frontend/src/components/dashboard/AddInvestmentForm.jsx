import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { investmentsAPI } from '../../api/investments';
import { formatCurrency } from '../../utils/currency';
import { useAuth } from '../../contexts/AuthContext';
import VerifyEmailModal from '../auth/VerifyEmailModal';
import ItemSearchSelect from '../ItemSearchSelect';
import PaywallModal from '../PaywallModal';
import PurchaseDatePicker from './PurchaseDatePicker';

export default function AddInvestmentForm() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [showVerifyModal, setShowVerifyModal] = useState(false);
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

  const purchasePrice = parseFloat(form.purchase_price) || 0;
  const quantity = parseInt(form.quantity) || 1;
  const steamPrice = selectedItem?.steam_price;
  const pnl = steamPrice && purchasePrice > 0 ? (steamPrice - purchasePrice) * quantity : null;
  const roi = steamPrice && purchasePrice > 0 ? ((steamPrice - purchasePrice) / purchasePrice) * 100 : null;
  const pnlPos = pnl !== null && pnl >= 0;

  return (
    <div className="max-w-2xl mx-auto">
      {showPaywall && <PaywallModal onClose={() => setShowPaywall(false)} />}
      {showVerifyModal && <VerifyEmailModal onClose={() => setShowVerifyModal(false)} />}

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Add Investment</h1>
        <p className="text-gray-500 text-sm">
          Track a new item in your portfolio
        </p>
      </div>

      {/* Verification gate */}
      {user && !user.email_verified && (
        <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
          <svg className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-amber-300 font-medium text-sm mb-1">Verify your email to continue</p>
            <p className="text-gray-500 text-xs mb-3">
              {!user.email || user.email.endsWith('@steam.placeholder')
                ? 'Add and verify an email address before tracking investments.'
                : 'Please verify your email address.'}
            </p>
            <button
              onClick={() => setShowVerifyModal(true)}
              className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-black text-xs font-medium rounded-lg transition-colors"
            >
              {!user.email || user.email.endsWith('@steam.placeholder') ? 'Add Email' : 'Verify Now'}
            </button>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Item Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-3">Item</label>
          <ItemSearchSelect
            value={form.item_id}
            onChange={handleItemSelect}
            error={errors.item_id}
          />
        </div>

        {/* Price & Quantity Row */}
        <div className="grid grid-cols-2 gap-4">
          {/* Purchase Price */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-3">Purchase Price</label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-lg">$</span>
              <input
                type="number"
                value={form.purchase_price}
                onChange={set('purchase_price')}
                placeholder="0.00"
                step="0.01"
                min="0"
                className={`w-full pl-8 pr-4 py-3.5 bg-gray-900 border rounded-xl text-white text-lg font-medium
                  placeholder-gray-700 focus:outline-none focus:ring-2 transition-all
                  ${errors.purchase_price ? 'border-red-500/50 focus:ring-red-500/20' : 'border-gray-800 focus:border-cyan-500/50 focus:ring-cyan-500/10'}`}
              />
            </div>
            {steamPrice && (
              <p className="text-xs text-gray-600 mt-2">
                Current Steam: {formatCurrency(steamPrice)}
              </p>
            )}
            {errors.purchase_price && (
              <p className="text-xs text-red-400 mt-2">{errors.purchase_price}</p>
            )}
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-3">Quantity</label>
            <div className="flex items-center gap-2">
              <button 
                type="button"
                onClick={() => setForm(p => ({ ...p, quantity: String(Math.max(1, parseInt(p.quantity || 1) - 1)) }))}
                className="w-11 h-12 rounded-xl bg-gray-900 border border-gray-800 hover:bg-gray-800 hover:border-gray-700 text-gray-400 flex items-center justify-center transition-all"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              <input
                type="number"
                value={form.quantity}
                onChange={set('quantity')}
                min="1"
                className="flex-1 h-12 px-4 bg-gray-900 border border-gray-800 rounded-xl text-white text-lg font-medium text-center focus:outline-none focus:ring-2 focus:border-cyan-500/50 focus:ring-cyan-500/10 transition-all"
              />
              <button 
                type="button"
                onClick={() => setForm(p => ({ ...p, quantity: String(parseInt(p.quantity || 1) + 1) }))}
                className="w-11 h-12 rounded-xl bg-gray-900 border border-gray-800 hover:bg-gray-800 hover:border-gray-700 text-gray-400 flex items-center justify-center transition-all"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
            {purchasePrice > 0 && (
              <p className="text-xs text-gray-600 mt-2 text-center">
                Total: {formatCurrency(purchasePrice * quantity)}
              </p>
            )}
          </div>
        </div>

        {/* P&L Preview */}
        {pnl !== null && (
          <div className={`p-4 rounded-xl border ${pnlPos ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 mb-1">If sold at current Steam price</p>
                <p className="text-xs text-gray-600">
                  {formatCurrency(steamPrice)} × {quantity}
                </p>
              </div>
              <div className="text-right">
                <p className={`text-xl font-bold ${pnlPos ? 'text-emerald-400' : 'text-red-400'}`}>
                  {pnlPos ? '+' : ''}{formatCurrency(pnl)}
                </p>
                <p className={`text-sm ${pnlPos ? 'text-emerald-500' : 'text-red-500'}`}>
                  {pnlPos ? '+' : ''}{roi?.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Date & Notes */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-3">Purchase Date</label>
            <PurchaseDatePicker
              value={form.purchase_date}
              onChange={(iso) => setForm(prev => ({ ...prev, purchase_date: iso }))}
              itemId={form.item_id}
              purchasePrice={parseFloat(form.purchase_price) || 0}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-3">
              Notes <span className="text-gray-600 font-normal text-xs">(optional)</span>
            </label>
            <textarea
              value={form.notes}
              onChange={set('notes')}
              rows={3}
              placeholder="Add context about this investment..."
              className="w-full px-4 py-3 bg-gray-900 border border-gray-800 rounded-xl text-gray-300 text-sm placeholder-gray-700 focus:outline-none focus:ring-2 focus:border-cyan-500/50 focus:ring-cyan-500/10 transition-all resize-none"
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !form.item_id || (user && !user.email_verified)}
          className="w-full py-4 rounded-xl font-semibold text-sm transition-all
            bg-gradient-to-r from-cyan-500 to-blue-500
            hover:from-cyan-400 hover:to-blue-400
            disabled:from-gray-800 disabled:to-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed
            text-white shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 disabled:shadow-none"
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
