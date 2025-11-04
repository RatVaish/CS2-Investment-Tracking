import { useEffect, useState } from 'react';
import { investmentAPI } from '../api/investments';

function TopPerformers() {
  const [performers, setPerformers] = useState({ gainers: [], losers: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTopPerformers();
  }, []);

  const fetchTopPerformers = async () => {
    try {
      setLoading(true);
      const data = await investmentAPI.getTopPerformers(3);
      setPerformers(data);
    } catch (err) {
      console.error('Error fetching top performers:', err);
    } finally {
      setLoading(false);
    }
  };

  const PerformerCard = ({ item, isGainer }) => (
    <div style={{
      backgroundColor: '#111827',
      borderRadius: '8px',
      padding: '20px',
      border: `2px solid ${isGainer ? '#10b981' : '#ef4444'}`,
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background gradient */}
      <div style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '100px',
        height: '100px',
        background: `radial-gradient(circle, ${isGainer ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'} 0%, transparent 70%)`,
        pointerEvents: 'none'
      }}></div>

      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* Item name */}
        <h4 style={{
          fontSize: '16px',
          fontWeight: '600',
          color: '#f9fafb',
          marginBottom: '8px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {item.item_name}
        </h4>

        {/* Item type */}
        <p style={{
          fontSize: '12px',
          color: '#9ca3af',
          textTransform: 'capitalize',
          marginBottom: '12px'
        }}>
          {item.item_type.replace('_', ' ')} • Qty: {item.quantity}
        </p>

        {/* Price change */}
        <div style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: '8px',
          marginBottom: '8px'
        }}>
          <span style={{
            fontSize: '28px',
            fontWeight: 'bold',
            color: isGainer ? '#10b981' : '#ef4444'
          }}>
            {isGainer ? '+' : ''}{item.price_change_pct.toFixed(1)}%
          </span>
          <span style={{
            fontSize: '14px',
            color: '#9ca3af'
          }}>
            {isGainer ? '↑' : '↓'}
          </span>
        </div>

        {/* Profit/Loss */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: '12px',
          borderTop: '1px solid #374151'
        }}>
          <span style={{ fontSize: '12px', color: '#9ca3af' }}>
            P/L:
          </span>
          <span style={{
            fontSize: '16px',
            fontWeight: '600',
            color: isGainer ? '#10b981' : '#ef4444'
          }}>
            {isGainer ? '+' : ''}£{item.total_profit_loss.toFixed(2)}
          </span>
        </div>

        {/* Price range */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: '#9ca3af',
          marginTop: '8px'
        }}>
          <span>£{item.purchase_price.toFixed(2)}</span>
          <span>→</span>
          <span>£{item.current_price.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div style={{
        backgroundColor: '#1f2937',
        borderRadius: '12px',
        padding: '40px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
        border: '1px solid #374151',
        marginBottom: '48px'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '200px'
        }}>
          <div style={{
            width: '60px',
            height: '60px',
            border: '4px solid #374151',
            borderTop: '4px solid #3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
        </div>
      </div>
    );
  }

  if (performers.gainers.length === 0 && performers.losers.length === 0) {
    return null;
  }

  return (
    <div style={{
      backgroundColor: '#1f2937',
      borderRadius: '12px',
      padding: '40px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
      border: '1px solid #374151',
      marginBottom: '48px'
    }}>
      <h3 style={{
        fontSize: '24px',
        fontWeight: '600',
        color: '#f9fafb',
        marginBottom: '32px'
      }}>
        Top Performers
      </h3>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '32px'
      }}>
        {/* Gainers Section */}
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '24px' }}>🚀</span>
            <h4 style={{
              fontSize: '18px',
              fontWeight: '600',
              color: '#10b981'
            }}>
              Top Gainers
            </h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {performers.gainers.length > 0 ? (
              performers.gainers.map(item => (
                <PerformerCard key={item.id} item={item} isGainer={true} />
              ))
            ) : (
              <p style={{ color: '#9ca3af', fontSize: '14px', textAlign: 'center', padding: '40px' }}>
                No gainers yet
              </p>
            )}
          </div>
        </div>

        {/* Losers Section */}
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '16px'
          }}>
            <span style={{ fontSize: '24px' }}>📉</span>
            <h4 style={{
              fontSize: '18px',
              fontWeight: '600',
              color: '#ef4444'
            }}>
              Top Losers
            </h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {performers.losers.length > 0 ? (
              performers.losers.map(item => (
                <PerformerCard key={item.id} item={item} isGainer={false} />
              ))
            ) : (
              <p style={{ color: '#9ca3af', fontSize: '14px', textAlign: 'center', padding: '40px' }}>
                No losers yet
              </p>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default TopPerformers;
