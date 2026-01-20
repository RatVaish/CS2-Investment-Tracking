import React, { useState } from 'react';
import { investmentsAPI } from '../../api/investments';
import ItemSearchSelect from '../ItemSearchSelect';

function AddInvestmentForm() {
  const [formData, setFormData] = useState({
    item_id: null,
    purchase_price: '',
    quantity: 1,
    purchase_date: '',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleItemSelect = (itemId) => {
    setFormData(prev => ({
      ...prev,
      item_id: itemId
    }));
    // Clear item error when selected
    if (fieldErrors.item_id) {
      setFieldErrors(prev => ({ ...prev, item_id: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setFieldErrors({});
    setLoading(true);

    try {
      // Validate item is selected
      if (!formData.item_id) {
        setFieldErrors({ item_id: 'Please select an item' });
        setLoading(false);
        return;
      }

      // Prepare investment data for V3 backend
      const investmentData = {
        item_id: formData.item_id,
        purchase_price: parseFloat(formData.purchase_price),
        quantity: parseInt(formData.quantity),
        purchase_date: formData.purchase_date || new Date().toISOString(),
        ...(formData.notes && { notes: formData.notes })
      };

      await investmentsAPI.create(investmentData);

      // Success - reset form
      setSuccess(true);
      setFormData({
        item_id: null,
        purchase_price: '',
        quantity: 1,
        purchase_date: '',
        notes: ''
      });

      // Hide success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to create investment:', err);
      setError(err.response?.data?.detail || 'Failed to add investment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold text-white mb-6">Add New Investment</h2>

      {/* Success Message */}
      {success && (
        <div className="mb-6 p-4 bg-green-500/10 border border-green-500/50 rounded-lg">
          <p className="text-green-400">Investment added successfully!</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-gray-800 border border-gray-700 rounded-xl p-6 space-y-6">
        {/* Item Search/Select */}
        <ItemSearchSelect
          value={formData.item_id}
          onChange={handleItemSelect}
          error={fieldErrors.item_id}
        />

        {/* Purchase Price and Quantity */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Purchase Price (£) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              name="purchase_price"
              value={formData.purchase_price}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
              placeholder="12.50"
              step="0.01"
              min="0"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Quantity <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              name="quantity"
              value={formData.quantity}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
              placeholder="1"
              min="1"
              required
            />
          </div>
        </div>

        {/* Purchase Date */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Purchase Date <span className="text-red-400">*</span>
          </label>
          <input
            type="datetime-local"
            name="purchase_date"
            value={formData.purchase_date}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 transition-colors"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Leave empty to use current date/time
          </p>
        </div>

        {/* Notes (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Notes (Optional)
          </label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors resize-none"
            placeholder="Add any notes about this investment..."
            rows="3"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg font-semibold transition-all"
        >
          {loading ? 'Adding Investment...' : 'Add Investment'}
        </button>
      </form>
    </div>
  );
}

export default AddInvestmentForm;