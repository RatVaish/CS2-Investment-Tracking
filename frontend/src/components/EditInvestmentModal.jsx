import { useState, useEffect } from 'react';
import { investmentAPI } from '../api/investments';

function EditInvestmentModal({ investment, onClose, onUpdated }) {
  const [formData, setFormData] = useState({
    item_name: investment.item_name,
    item_type: investment.item_type,
    purchase_price: investment.purchase_price,
    quantity: investment.quantity,
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
        // Auto-format item names based on type
        let formattedItemName = formData.item_name.trim();

        // Add "Sticker | " prefix if it's a sticker and doesn't already have it
        if (formData.item_type === 'sticker' && !formattedItemName.startsWith('Sticker | ')) {
          formattedItemName = `Sticker | ${formattedItemName}`;
        }

        // Add "Patch | " prefix for patches
        if (formData.item_type === 'patch' && !formattedItemName.startsWith('Patch | ')) {
          formattedItemName = `Patch | ${formattedItemName}`;
        }

        // Add "Music Kit | " prefix for music kits
        if (formData.item_type === 'music_kit' && !formattedItemName.startsWith('Music Kit | ')) {
          formattedItemName = `Music Kit | ${formattedItemName}`;
        }

        const dataToSend = {
          ...formData,
          item_name: formattedItemName,
          purchase_price: parseFloat(formData.purchase_price),
          quantity: parseInt(formData.quantity, 10)
        };

        await investmentAPI.update(investment.id, dataToSend);
        onUpdated();
        onClose();
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };

  const labelStyle = {
    display: 'block',
    fontSize: '16px',
    fontWeight: '600',
    color: '#f9fafb',
    marginBottom: '12px'
  };

  const inputStyle = {
    width: '100%',
    padding: '12px 16px',
    fontSize: '15px',
    border: '2px solid #4b5563',
    borderRadius: '8px',
    backgroundColor: '#374151',
    color: '#f9fafb'
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: '#1f2937',
        borderRadius: '12px',
        padding: '32px',
        maxWidth: '600px',
        width: '90%',
        maxHeight: '90vh',
        overflow: 'auto',
        border: '1px solid #374151'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#f9fafb', margin: 0 }}>
            Edit Investment
          </h2>
          <button
            onClick={onClose}
            style={{
              fontSize: '24px',
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer',
              padding: '4px 8px'
            }}
          >
            ×
          </button>
        </div>

        {error && (
          <div style={{
            backgroundColor: '#7f1d1d',
            border: '1px solid #991b1b',
            color: '#fecaca',
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '24px' }}>
            <label style={labelStyle}>Item Name</label>
            <input
              type="text"
              name="item_name"
              value={formData.item_name}
              onChange={handleChange}
              required
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={labelStyle}>Item Type</label>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
            <div>
              <label style={labelStyle}>Purchase Price (£)</label>
              <input
                type="number"
                name="purchase_price"
                value={formData.purchase_price}
                onChange={handleChange}
                required
                min="0"
                step="0.01"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Quantity</label>
              <input
                type="number"
                name="quantity"
                value={formData.quantity}
                onChange={handleChange}
                required
                min="1"
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                flex: 1,
                padding: '12px',
                fontSize: '16px',
                fontWeight: '600',
                backgroundColor: '#374151',
                color: '#f9fafb',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                flex: 1,
                padding: '12px',
                fontSize: '16px',
                fontWeight: '600',
                backgroundColor: loading ? '#4b5563' : '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EditInvestmentModal;
