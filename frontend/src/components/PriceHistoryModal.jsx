import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { investmentAPI } from "../api/investments";

function PriceHistoryModal({ investment, onClose }) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState("all");
    const [stats, setStats] = useState({ min: 0, max: 0, avg: 0 });

    useEffect(() => {
        fetchHistory();
    }, [investment.id, timeRange]);

    const fetchHistory = async () => {
        try {
            setLoading(true);
            const days = timeRange === "all" ? null : parseInt(timeRange);
            const data = await investmentAPI.getPriceHistory(investment.id, days);

            const sortedData = data.sort((a, b) =>
                new Date(a.timestamp) - new Date(b.timestamp)
            );

            const formattedData = sortedData.map(item => ({
                date: new Date(item.timestamp).toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: 'short',
                    year: timeRange === 'all' ? '2-digit' : undefined
                }),
                price: item.price,
                fullDate: new Date(item.timestamp).toLocaleString('en-GB')
            }));

            setHistory(formattedData);

            if (data.length > 0) {
                const prices = data.map(d => d.price);
                setStats({
                    min: Math.min(...prices),
                    max: Math.max(...prices),
                    avg: prices.reduce((a, b) => a + b, 0) / prices.length
                });
            }
        } catch (err) {
            console.error("Error fetching price history:", err);
        } finally {
            setLoading(false);
        }
    };

    const calculateChange = () => {
        if (history.length < 2) return { value: 0, percentage: 0 };
        const oldest = history[0].price;
        const newest = history[history.length - 1].price;
        const change = newest - oldest;
        const percentage = ((change / oldest) * 100);
        return { value: change, percentage };
    };

    const change = calculateChange();

    return (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}
        onClick={onClose}
        >
          <div style={{
            backgroundColor: '#1f2937',
            borderRadius: '16px',
            padding: '32px',
            maxWidth: '1000px',
            width: '100%',
            maxHeight: '90vh',
            overflow: 'auto',
            border: '2px solid #374151'
          }}
          onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '24px'
            }}>
              <div>
                <h2 style={{
                  fontSize: '28px',
                  fontWeight: 'bold',
                  color: '#f9fafb',
                  marginBottom: '8px'
                }}>
                  {investment.item_name}
                </h2>
                <p style={{
                  fontSize: '16px',
                  color: '#9ca3af',
                  textTransform: 'capitalize'
                }}>
                  {investment.item_type.replace('_', ' ')} • Qty: {investment.quantity}
                </p>
              </div>
              <button
                onClick={onClose}
                style={{
                  padding: '8px 16px',
                  fontSize: '24px',
                  backgroundColor: '#374151',
                  color: '#f9fafb',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  lineHeight: 1
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#4b5563'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#374151'}
              >
                ×
              </button>
            </div>

            {/* Time Range Selector */}
            <div style={{
              display: 'flex',
              gap: '8px',
              marginBottom: '24px'
            }}>
              {['7', '30', 'all'].map(range => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  style={{
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: '500',
                    backgroundColor: timeRange === range ? '#3b82f6' : '#374151',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                  onMouseOver={(e) => {
                    if (timeRange !== range) e.target.style.backgroundColor = '#4b5563';
                  }}
                  onMouseOut={(e) => {
                    if (timeRange !== range) e.target.style.backgroundColor = '#374151';
                  }}
                >
                  {range === 'all' ? 'All Time' : `${range} Days`}
                </button>
              ))}
            </div>

            {loading ? (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '400px'
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
            ) : history.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '80px 20px',
                color: '#9ca3af'
              }}>
                <p style={{ fontSize: '18px', marginBottom: '8px' }}>No price history yet</p>
                <p style={{ fontSize: '14px' }}>Refresh the price to start tracking history</p>
              </div>
            ) : (
              <>
                {/* Stats Cards */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '16px',
                  marginBottom: '32px'
                }}>
                  <div style={{
                    backgroundColor: '#111827',
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid #374151'
                  }}>
                    <p style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>CURRENT</p>
                    <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
                      £{investment.current_price?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div style={{
                    backgroundColor: '#111827',
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid #374151'
                  }}>
                    <p style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>CHANGE</p>
                    <p style={{
                      fontSize: '24px',
                      fontWeight: 'bold',
                      color: change.value >= 0 ? '#10b981' : '#ef4444'
                    }}>
                      {change.value >= 0 ? '+' : ''}£{change.value.toFixed(2)}
                    </p>
                    <p style={{
                      fontSize: '12px',
                      color: change.value >= 0 ? '#10b981' : '#ef4444'
                    }}>
                      {change.percentage >= 0 ? '+' : ''}{change.percentage.toFixed(1)}%
                    </p>
                  </div>
                  <div style={{
                    backgroundColor: '#111827',
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid #374151'
                  }}>
                    <p style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>MIN</p>
                    <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>
                      £{stats.min.toFixed(2)}
                    </p>
                  </div>
                  <div style={{
                    backgroundColor: '#111827',
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid #374151'
                  }}>
                    <p style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>MAX</p>
                    <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
                      £{stats.max.toFixed(2)}
                    </p>
                  </div>
                </div>

                {/* Chart */}
                <div style={{
                  backgroundColor: '#111827',
                  padding: '24px',
                  borderRadius: '12px',
                  border: '1px solid #374151'
                }}>
                  <h3 style={{
                    fontSize: '18px',
                    fontWeight: '600',
                    color: '#f9fafb',
                    marginBottom: '24px'
                  }}>
                    Price History
                  </h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="date"
                        stroke="#9ca3af"
                        style={{ fontSize: '12px' }}
                      />
                      <YAxis
                        stroke="#9ca3af"
                        style={{ fontSize: '12px' }}
                        tickFormatter={(value) => `£${value.toFixed(2)}`}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                          color: '#f9fafb'
                        }}
                        formatter={(value) => [`£${value.toFixed(2)}`, 'Price']}
                        labelFormatter={(label) => {
                          const item = history.find(h => h.date === label);
                          return item ? item.fullDate : label;
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="price"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={{ fill: '#3b82f6', r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}

            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        </div>
      );
}

export default PriceHistoryModal;
