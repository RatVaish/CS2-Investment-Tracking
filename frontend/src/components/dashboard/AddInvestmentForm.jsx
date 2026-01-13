import React, { useState } from 'react';
import { investmentsAPI } from '../../api/investments';

function AddInvestmentForm() {
  const [formData, setFormData] = useState({
    item_name: '',
    item_type: 'skin',
    purchase_price: '',
    quantity: 1,
    purchase_date: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const itemTypes = [
    { value: 'skin', label: 'Skin' },
    { value: 'knife', label: 'Knife' },
    { value: 'gloves', label: 'Gloves' },
    { value: 'sticker', label: 'Sticker' },
    { value: 'case', label: 'Case' },
    { value: 'agent', label: 'Agent' },
    { value: 'patch', label: 'Patch' },
    { value: 'music_kit', label: 'Music Kit' },
    { value: 'graffiti', label: 'Graffiti' },
    { value: 'other', label: 'Other' }
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      // Convert purchase_price to float and quantity to int
      const investmentData = {
        item_name: formData.item_name,
        item_type: formData.item_type,
        purchase_price: parseFloat(formData.purchase_price),
        quantity: parseInt(formData.quantity),
        ...(formData.purchase_date && { purchase_date: formData.purchase_date })
      };

      await investmentsAPI.create(investmentData);

      // Success - reset form
      setSuccess(true);
      setFormData({
        item_name: '',
        item_type: 'skin',
        purchase_price: '',
        quantity: 1,
        purchase_date: ''
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
        {/* Item Name */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Item Name *
          </label>
          <input
            type="text"
            name="item_name"
            value={formData.item_name}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
            placeholder="e.g., AK-47 | Redline (Field-Tested)"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter the full item name including condition
          </p>
        </div>

        {/* Item Type */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Item Type *
          </label>
          <select
            name="item_type"
            value={formData.item_type}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 transition-colors"
            required
          >
            {itemTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Purchase Price and Quantity */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Purchase Price (£) *
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
              Quantity *
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

        {/* Purchase Date (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Purchase Date (Optional)
          </label>
          <input
            type="datetime-local"
            name="purchase_date"
            value={formData.purchase_date}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 transition-colors"
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