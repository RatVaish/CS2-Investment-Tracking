import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { investmentAPI } from '../api/investments';

function PortfolioValueChart() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    fetchPortfolioHistory();
  }, [timeRange]);

  const fetchPortfolioHistory = async () => {
    try {
      setLoading(true);
      const history = await investmentAPI.getPortfolioValueHistory(timeRange);

      // Format data for chart
      const formattedData = history.map(item => ({
        date: new Date(item.timestamp).toLocaleDateString('en-GB', {
          day: '2-digit',
          month: 'short',
          ...(timeRange > 30 ? { year: '2-digit' } : {})
        }),
        value: item.value,
        fullDate: new Date(item.timestamp).toLocaleString('en-GB')
      }));

      setData(formattedData);
    } catch (err) {
      console.error('Error fetching portfolio history:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateChange = () => {
    if (data.length < 2) return { value: 0, percentage: 0 };
    const oldest = data[0].value;
    const newest = data[data.length - 1].value;
    const change = newest - oldest;
    const percentage = ((change / oldest) * 100);
    return { value: change, percentage };
  };

  const change = calculateChange();

  return (
    <div style={{
      backgroundColor: '#1f2937',
      borderRadius: '12px',
      padding: '40px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
      border: '1px solid #374151',
      marginTop: '48px'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '32px'
      }}>
        <div>
          <h3 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: '#f9fafb',
            marginBottom: '8px'
          }}>
            Portfolio Value Over Time
          </h3>
          {data.length > 0 && (
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              <span style={{ fontSize: '14px', color: '#9ca3af' }}>
                Current: £{data[data.length - 1].value.toFixed(2)}
              </span>
              <span style={{
                fontSize: '14px',
                fontWeight: '600',
                color: change.value >= 0 ? '#10b981' : '#ef4444'
              }}>
                {change.value >= 0 ? '↑' : '↓'} {change.value >= 0 ? '+' : ''}£{Math.abs(change.value).toFixed(2)} ({change.value >= 0 ? '+' : ''}{change.percentage.toFixed(1)}%)
              </span>
            </div>
          )}
        </div>

        {/* Time Range Selector */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {[7, 30, 90].map(days => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              style={{
                padding: '8px 16px',
                fontSize: '14px',
                fontWeight: '500',
                backgroundColor: timeRange === days ? '#3b82f6' : '#374151',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
              onMouseOver={(e) => {
                if (timeRange !== days) e.target.style.backgroundColor = '#4b5563';
              }}
              onMouseOut={(e) => {
                if (timeRange !== days) e.target.style.backgroundColor = '#374151';
              }}
            >
              {days}D
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      {loading ? (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '300px'
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
      ) : data.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '80px 20px',
          color: '#9ca3af'
        }}>
          <p style={{ fontSize: '18px', marginBottom: '8px' }}>No portfolio history yet</p>
          <p style={{ fontSize: '14px' }}>Price data will appear here as your investments are tracked over time</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="date"
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => `£${value.toFixed(0)}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#f9fafb'
              }}
              formatter={(value) => [`£${value.toFixed(2)}`, 'Portfolio Value']}
              labelFormatter={(label) => {
                const item = data.find(d => d.date === label);
                return item ? item.fullDate : label;
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#10b981"
              strokeWidth={3}
              dot={{ fill: '#10b981', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
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

export default PortfolioValueChart;
