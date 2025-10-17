import { useEffect, useState } from 'react';
import { investmentAPI } from '../api/investments';
import EditInvestmentModal from '../components/EditInvestmentModal';

function Portfolio() {
  const [investments, setInvestments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [refreshing, setRefreshing] = useState(null);
  const [lastRefreshTime, setLastRefreshTime] = useState({});
  const [cooldowns, setCooldowns] = useState({});
  const [editingInvestment, setEditingInvestment] = useState(null);
  const [filterType, setFilterType] = useState('all');

  const fetchInvestments = async () => {
    try {
      setLoading(true);
      const data = await investmentAPI.getAll();
      setInvestments(data);
    } catch (err) {
      console.error('Error fetching investments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvestments();
  }, []);

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleRefreshPrice = async (id) => {
    // Check if on cooldown
    const now = Date.now();
    const lastRefresh = lastRefreshTime[id] || 0;
    const timeSinceRefresh = now - lastRefresh;
    const cooldownMs = 5000; // 5 second cooldown

    if (timeSinceRefresh < cooldownMs) {
      alert(`Please wait ${Math.ceil((cooldownMs - timeSinceRefresh) / 1000)} seconds before refreshing again`);
      return;
    }

    try {
      setRefreshing(id);
      const result = await investmentAPI.refreshPrice(id);

      // Set last refresh time
      setLastRefreshTime(prev => ({ ...prev, [id]: Date.now() }));

      // Start cooldown timer
      setCooldowns(prev => ({ ...prev, [id]: 5 }));
      const countdown = setInterval(() => {
        setCooldowns(prev => {
          const newCooldown = (prev[id] || 0) - 1;
          if (newCooldown <= 0) {
            clearInterval(countdown);
            const { [id]: _, ...rest } = prev;
            return rest;
          }
          return { ...prev, [id]: newCooldown };
        });
      }, 1000);

      // Check if the refresh was successful
      if (result.success === false) {
        alert(result.message || 'Failed to fetch price from Steam Market');
      }

      await fetchInvestments();
    } catch (err) {
      console.error('Refresh error:', err);
      alert('Failed to refresh price: ' + (err.response?.data?.message || err.message));
    } finally {
      setRefreshing(null);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"?`)) return;
    
    try {
      await investmentAPI.delete(id);
      setInvestments(investments.filter(inv => inv.id !== id));
    } catch (err) {
      alert('Failed to delete: ' + err.message);
    }
  };

  const getSortedInvestments = () => {
    // First filter by type
    let filtered = investments;
    if (filterType !== 'all') {
      filtered = investments.filter(inv => inv.item_type === filterType);
    }

    // Then sort
    return [...filtered].sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];

      if (sortBy === 'profit_loss') {
        aVal = a.current_price ? (a.current_price - a.purchase_price) * a.quantity : 0;
        bVal = b.current_price ? (b.current_price - b.purchase_price) * b.quantity : 0;
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
  };

  const calculateProfitLoss = (inv) => {
    if (!inv.current_price) return null;
    return (inv.current_price - inv.purchase_price) * inv.quantity;
  };

  const calculateROI = (inv) => {
    if (!inv.current_price || inv.purchase_price === 0) return null;
    return ((inv.current_price - inv.purchase_price) / inv.purchase_price) * 100;
  };

  const getItemImageUrl = (inv) => {
      // Color-coded placeholders with emoji icons
      const typeConfig = {
        'skin': { bg: '2563eb', text: 'ffffff', icon: 'GUN' },
        'sticker': { bg: '10b981', text: 'ffffff', icon: 'STICKER' },
        'knife': { bg: 'ef4444', text: 'ffffff', icon: 'KNIFE' },
        'case': { bg: 'f59e0b', text: 'ffffff', icon: 'CASE' },
        'gloves': { bg: '8b5cf6', text: 'ffffff', icon: 'GLOVES' },
        'agent': { bg: 'ec4899', text: 'ffffff', icon: 'AGENT' },
        'patch': { bg: '06b6d4', text: 'ffffff', icon: 'PATCH' },
        'music_kit': { bg: '84cc16', text: 'ffffff', icon: 'MUSIC' },
        'graffiti': { bg: 'f97316', text: 'ffffff', icon: 'ART' },
      };

      const config = typeConfig[inv.item_type] || { bg: '6b7280', text: 'ffffff', icon: 'ITEM' };
      return `https://via.placeholder.com/80/${config.bg}/${config.text}?text=${config.icon}`;
  };

  const handleEdit = (investment) => {
    setEditingInvestment(investment);
  };

  const handleEditClose = () => {
    setEditingInvestment(null);
  };

  const handleEditUpdated = async () => {
    await fetchInvestments();
    setEditingInvestment(null);
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        paddingTop: '120px',
        paddingBottom: '120px'
      }}>
        <div style={{
          width: '80px',
          height: '80px',
          border: '4px solid #374151',
          borderTop: '4px solid #2563eb',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '32px'
        }}></div>
        <p style={{ fontSize: '20px', color: '#9ca3af' }}>Loading portfolio...</p>
      </div>
    );
  }

  const sortedInvestments = getSortedInvestments();

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '64px' }}>
        <h1 style={{
          fontSize: '56px',
          fontWeight: 'bold',
          color: '#f9fafb',
          marginBottom: '16px'
        }}>
          Portfolio Details
        </h1>
        <p style={{ fontSize: '20px', color: '#9ca3af' }}>
          Detailed view of all investments
        </p>
      </div>

      {investments.length > 0 && (
        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          padding: '20px 24px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          border: '1px solid #374151'
        }}>
          <label style={{
            fontSize: '16px',
            fontWeight: '600',
            color: '#f9fafb',
            minWidth: '120px'
          }}>
            Filter by Type:
          </label>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              padding: '10px 16px',
              fontSize: '15px',
              border: '2px solid #4b5563',
              borderRadius: '8px',
              backgroundColor: '#374151',
              color: '#f9fafb',
              cursor: 'pointer',
              minWidth: '200px'
            }}
          >
            <option value="all">All Types ({investments.length})</option>
            <option value="skin">
              Skins ({investments.filter(i => i.item_type === 'skin').length})
            </option>
            <option value="sticker">
              Stickers ({investments.filter(i => i.item_type === 'sticker').length})
            </option>
            <option value="knife">
              Knives ({investments.filter(i => i.item_type === 'knife').length})
            </option>
            <option value="gloves">
              Gloves ({investments.filter(i => i.item_type === 'gloves').length})
            </option>
            <option value="case">
              Cases ({investments.filter(i => i.item_type === 'case').length})
            </option>
            <option value="agent">
              Agents ({investments.filter(i => i.item_type === 'agent').length})
            </option>
            <option value="patch">
              Patches ({investments.filter(i => i.item_type === 'patch').length})
            </option>
            <option value="music_kit">
              Music Kits ({investments.filter(i => i.item_type === 'music_kit').length})
            </option>
            <option value="graffiti">
              Graffiti ({investments.filter(i => i.item_type === 'graffiti').length})
            </option>
            <option value="other">
              Other ({investments.filter(i => i.item_type === 'other').length})
            </option>
          </select>

          {filterType !== 'all' && (
            <button
              onClick={() => setFilterType('all')}
              style={{
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '500',
                backgroundColor: '#374151',
                color: '#9ca3af',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
              onMouseOver={(e) => {
                e.target.style.backgroundColor = '#4b5563';
                e.target.style.color = '#f9fafb';
              }}
              onMouseOut={(e) => {
                e.target.style.backgroundColor = '#374151';
                e.target.style.color = '#9ca3af';
              }}
            >
              Clear Filter
            </button>
          )}

          <div style={{ marginLeft: 'auto', color: '#9ca3af', fontSize: '14px' }}>
            Showing {getSortedInvestments().length} of {investments.length} items
          </div>
        </div>
      )}

      {investments.length === 0 ? (
        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          padding: '80px',
          textAlign: 'center',
          border: '1px solid #374151'
        }}>
          <div style={{ fontSize: '96px', marginBottom: '32px' }}>📦</div>
          <h2 style={{
            fontSize: '32px',
            fontWeight: '600',
            color: '#f9fafb',
            marginBottom: '16px'
          }}>
            No Investments
          </h2>
          <p style={{ fontSize: '18px', color: '#9ca3af' }}>
            Add investments from the Manage tab
          </p>
        </div>
      ) : (
        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          overflow: 'hidden',
          border: '1px solid #374151'
        }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ backgroundColor: '#374151', borderBottom: '2px solid #4b5563' }}>
                <tr>
                  <th style={{
                    padding: '20px 24px',
                    textAlign: 'left',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#f9fafb',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Image
                  </th>
                  <th
                    onClick={() => handleSort('item_name')}
                    style={{
                      padding: '20px 24px',
                      textAlign: 'left',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#f9fafb',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      cursor: 'pointer'
                    }}
                  >
                    Item Name {sortBy === 'item_name' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    onClick={() => handleSort('item_type')}
                    style={{
                      padding: '20px 24px',
                      textAlign: 'left',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#f9fafb',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      cursor: 'pointer'
                    }}
                  >
                    Type {sortBy === 'item_type' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    onClick={() => handleSort('purchase_price')}
                    style={{
                      padding: '20px 24px',
                      textAlign: 'right',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#f9fafb',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      cursor: 'pointer'
                    }}
                  >
                    Purchase £ {sortBy === 'purchase_price' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    onClick={() => handleSort('current_price')}
                    style={{
                      padding: '20px 24px',
                      textAlign: 'right',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#f9fafb',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      cursor: 'pointer'
                    }}
                  >
                    Current £ {sortBy === 'current_price' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    onClick={() => handleSort('profit_loss')}
                    style={{
                      padding: '20px 24px',
                      textAlign: 'right',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#f9fafb',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      cursor: 'pointer'
                    }}
                  >
                    P/L £ {sortBy === 'profit_loss' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th style={{
                    padding: '20px 24px',
                    textAlign: 'center',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#f9fafb',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedInvestments.map((inv) => {
                  const profitLoss = calculateProfitLoss(inv);
                  const roi = calculateROI(inv);
                  const isProfit = profitLoss && profitLoss > 0;

                  return (
                    <tr key={inv.id} style={{ borderBottom: '1px solid #374151' }}>
                      <td style={{ padding: '20px 24px' }}>
                        <img
                          src={getItemImageUrl(inv)}
                          alt={inv.item_name}
                          style={{
                            width: '80px',
                            height: '80px',
                            objectFit: 'contain',
                            borderRadius: '8px',
                            backgroundColor: '#111827'
                          }}
                        />
                      </td>
                      <td style={{ padding: '20px 24px' }}>
                        <div style={{ fontWeight: '500', color: '#f9fafb', marginBottom: '4px' }}>
                          {inv.item_name}
                        </div>
                        <div style={{ fontSize: '14px', color: '#9ca3af' }}>
                          Qty: {inv.quantity}
                        </div>
                      </td>
                      <td style={{ padding: '20px 24px' }}>
                        <span style={{
                          padding: '4px 12px',
                          fontSize: '12px',
                          fontWeight: '500',
                          borderRadius: '9999px',
                          backgroundColor: '#1e40af',
                          color: '#dbeafe',
                          textTransform: 'capitalize'
                        }}>
                          {inv.item_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td style={{
                        padding: '20px 24px',
                        textAlign: 'right',
                        fontWeight: '500',
                        color: '#f9fafb'
                      }}>
                        £{inv.purchase_price.toFixed(2)}
                      </td>
                      <td style={{ padding: '20px 24px', textAlign: 'right' }}>
                        {inv.current_price ? (
                          <span style={{ fontWeight: '500', color: '#3b82f6' }}>
                            £{inv.current_price.toFixed(2)}
                          </span>
                        ) : (
                          <span style={{ color: '#6b7280', fontSize: '14px' }}>—</span>
                        )}
                      </td>
                      <td style={{ padding: '20px 24px', textAlign: 'right' }}>
                        {profitLoss !== null ? (
                          <div>
                            <div style={{
                              fontWeight: '600',
                              color: isProfit ? '#10b981' : '#ef4444'
                            }}>
                              {isProfit ? '+' : ''}£{Math.abs(profitLoss).toFixed(2)}
                            </div>
                            <div style={{
                              fontSize: '12px',
                              color: isProfit ? '#10b981' : '#ef4444'
                            }}>
                              ({isProfit ? '+' : ''}{roi.toFixed(1)}%)
                            </div>
                          </div>
                        ) : (
                          <span style={{ color: '#6b7280', fontSize: '14px' }}>—</span>
                        )}
                      </td>
                      <td style={{ padding: '20px 24px' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                          <button
                            onClick={() => handleEdit(inv)}
                            style={{
                              padding: '8px 16px',
                              backgroundColor: '#8b5cf6',
                              color: '#ffffff',
                              fontSize: '14px',
                              fontWeight: '500',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: 'pointer'
                            }}
                            onMouseOver={(e) => e.target.style.backgroundColor = '#7c3aed'}
                            onMouseOut={(e) => e.target.style.backgroundColor = '#8b5cf6'}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleRefreshPrice(inv.id)}
                            disabled={refreshing === inv.id || cooldowns[inv.id]}
                            style={{
                              padding: '8px 16px',
                              backgroundColor: (refreshing === inv.id || cooldowns[inv.id]) ? '#4b5563' : '#3b82f6',
                              color: '#ffffff',
                              fontSize: '14px',
                              fontWeight: '500',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: (refreshing === inv.id || cooldowns[inv.id]) ? 'not-allowed' : 'pointer'
                            }}
                            onMouseOver={(e) => {
                              if (refreshing !== inv.id && !cooldowns[inv.id]) e.target.style.backgroundColor = '#2563eb';
                            }}
                            onMouseOut={(e) => {
                              if (refreshing !== inv.id && !cooldowns[inv.id]) e.target.style.backgroundColor = '#3b82f6';
                            }}
                          >
                            {refreshing === inv.id ? '...' : cooldowns[inv.id] ? `${cooldowns[inv.id]}s` : '🔄'}
                          </button>
                          <button
                            onClick={() => handleDelete(inv.id, inv.item_name)}
                            style={{
                              padding: '8px 16px',
                              backgroundColor: '#ef4444',
                              color: '#ffffff',
                              fontSize: '14px',
                              fontWeight: '500',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: 'pointer'
                            }}
                            onMouseOver={(e) => e.target.style.backgroundColor = '#dc2626'}
                            onMouseOut={(e) => e.target.style.backgroundColor = '#ef4444'}
                          >
                            Delete
                          </button>
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

      {editingInvestment && (
        <EditInvestmentModal
          investment={editingInvestment}
          onClose={handleEditClose}
          onUpdated={handleEditUpdated}
        />
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default Portfolio;
