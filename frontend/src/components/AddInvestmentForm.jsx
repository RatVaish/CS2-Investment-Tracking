import { useState } from 'react';
import { investmentAPI } from '../api/investments';

function AddInvestmentForm({ onInvestmentAdded }) {
  const [formData, setFormData] = useState({
    item_name: '',
    item_type: 'sticker',
    purchase_price: '',
    quantity: 1,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const itemTypes = [
    'skin', 'sticker', 'case', 'agent', 'knife',
    'gloves', 'patch', 'music_kit', 'graffiti', 'other'
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'purchase_price' || name === 'quantity'
        ? parseFloat(value) || ''
        : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const dataToSend = {
        ...formData,
        purchase_price: parseFloat(formData.purchase_price),
        quantity: parseInt(formData.quantity, 10)
      };

      await investmentAPI.create(dataToSend);

      setFormData({
        item_name: '',
        item_type: 'sticker',
        purchase_price: '',
        quantity: 1,
      });

      onInvestmentAdded();
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const labelStyle = {
    display: 'block',
    fontSize: '18px',
    fontWeight: '600',
    color: '#f9fafb',
    marginBottom: '20px'
  };

  const inputStyle = {
    width: '100%',
    padding: '20px 24px',
    fontSize: '16px',
    border: '2px solid #4b5563',
    borderRadius: '8px',
    backgroundColor: '#374151',
    color: '#f9fafb'
  };

  const buttonStyle = {
    width: '100%',
    padding: '24px',
    fontSize: '18px',
    fontWeight: '600',
    backgroundColor: '#2563eb',
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer'
  };

  return (
    <div style={{
      backgroundColor: '#1f2937',
      borderRadius: '12px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
      padding: '48px',
      border: '1px solid #374151'
    }}>
      {error && (
        <div style={{
          backgroundColor: '#7f1d1d',
          border: '1px solid #991b1b',
          color: '#fecaca',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '32px'
        }}>
          <p style={{ fontWeight: '600', marginBottom: '8px' }}>Error</p>
          <p style={{ fontSize: '14px' }}>{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '48px' }}>
          <label style={labelStyle}>
            Item Name
          </label>
          <input
            type="text"
            name="item_name"
            value={formData.item_name}
            onChange={handleChange}
            required
            placeholder="e.g., AK-47 | Redline (Field-Tested)"
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: '48px' }}>
          <label style={labelStyle}>
            Item Type
          </label>
          <select
            name="item_type"
            value={formData.item_type}
            onChange={handleChange}
            style={inputStyle}
          >
            {itemTypes.map(type => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '32px',
          marginBottom: '48px'
        }}>
          <div>
            <label style={labelStyle}>
              Purchase Price (£)
            </label>
            <input
              type="number"
              name="purchase_price"
              value={formData.purchase_price}
              onChange={handleChange}
              required
              min="0"
              step="0.01"
              placeholder="0.00"
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>
              Quantity
            </label>
            <input
              type="number"
              name="quantity"
              value={formData.quantity}
              onChange={handleChange}
              required
              min="1"
              placeholder="1"
              style={inputStyle}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            ...buttonStyle,
            opacity: loading ? 0.5 : 1,
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
          onMouseOver={(e) => {
            if (!loading) e.target.style.backgroundColor = '#1d4ed8';
          }}
          onMouseOut={(e) => {
            if (!loading) e.target.style.backgroundColor = '#2563eb';
          }}
        >
          {loading ? 'Adding Investment...' : 'Add Investment'}
        </button>
      </form>
    </div>
  );
}

export default AddInvestmentForm;
