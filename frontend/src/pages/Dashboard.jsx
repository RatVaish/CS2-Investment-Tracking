import { useEffect, useState } from 'react';
import { investmentAPI } from '../api/investments';
import PortfolioValueChart from "../components/PortfolioValueChart.jsx";
import TopPerformers from '../components/TopPerformers';

function Dashboard() {
  const [investments, setInvestments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshingAll, setRefreshingAll] = useState(false);

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

  const handleRefreshAll = async () => {
    try {
      setRefreshingAll(true);
      const result = await investmentAPI.refreshAllPrices();

      // Show success message with details
      alert(
        `Price Refresh Complete!\n\n` +
        `Total Items: ${result.total}\n` +
        `Successfully Updated: ${result.updated}\n` +
        `Failed: ${result.failed}\n` +
        `Rate Limited: ${result.rate_limited || 0}\n\n` +
        `Note: This process takes time due to Steam's rate limiting (3 seconds per item).`
      );

      await fetchInvestments();
    } catch (err) {
      console.error('Refresh all error:', err);
      alert('Failed to refresh prices: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRefreshingAll(false);
    }
  };

  const totalInvested = investments.reduce((sum, inv) =>
    sum + (inv.purchase_price * inv.quantity), 0
  );

  const totalItems = investments.reduce((sum, inv) =>
    sum + inv.quantity, 0
  );

  const totalCurrentValue = investments.reduce((sum, inv) => {
    if (inv.current_price) {
      return sum + (inv.current_price * inv.quantity);
    }
    return sum + (inv.purchase_price * inv.quantity);
  }, 0);

  const totalProfitLoss = totalCurrentValue - totalInvested;
  const totalROI = totalInvested > 0 ? (totalProfitLoss / totalInvested) * 100 : 0;

  const typeBreakdown = investments.reduce((acc, inv) => {
    const type = inv.item_type;
    if (!acc[type]) {
      acc[type] = { count: 0, value: 0 };
    }
    acc[type].count += inv.quantity;
    acc[type].value += inv.purchase_price * inv.quantity;
    return acc;
  }, {});

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
        <p style={{ fontSize: '20px', color: '#9ca3af' }}>Loading dashboard...</p>
      </div>
    );
  }

  if (investments.length === 0) {
    return (
      <div>
        <div style={{ textAlign: 'center', marginBottom: '64px' }}>
          <h1 style={{
            fontSize: '56px',
            fontWeight: 'bold',
            color: '#f9fafb',
            marginBottom: '16px'
          }}>
            Portfolio Overview
          </h1>
          <p style={{ fontSize: '20px', color: '#9ca3af' }}>
            Track your CS2 investment performance
          </p>
        </div>

        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          padding: '80px',
          textAlign: 'center',
          border: '1px solid #374151'
        }}>
          <div style={{ fontSize: '96px', marginBottom: '32px' }}>📊</div>
          <h2 style={{
            fontSize: '32px',
            fontWeight: '600',
            color: '#f9fafb',
            marginBottom: '16px'
          }}>
            No Investments Yet
          </h2>
          <p style={{
            fontSize: '18px',
            color: '#9ca3af',
            marginBottom: '40px',
            maxWidth: '500px',
            margin: '0 auto 40px'
          }}>
            Start building your portfolio by adding your first investment
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '64px' }}>
        <h1 style={{
          fontSize: '56px',
          fontWeight: 'bold',
          color: '#f9fafb',
          marginBottom: '16px'
        }}>
          Portfolio Overview
        </h1>
        <p style={{ fontSize: '20px', color: '#9ca3af' }}>
          Track your CS2 investment performance
        </p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '32px' }}>
        <button
          onClick={handleRefreshAll}
          disabled={refreshingAll}
          style={{
            padding: '16px 32px',
            fontSize: '16px',
            fontWeight: '600',
            backgroundColor: refreshingAll ? '#4b5563' : '#10b981',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            cursor: refreshingAll ? 'not-allowed' : 'pointer'
          }}
          onMouseOver={(e) => {
            if (!refreshingAll) e.target.style.backgroundColor = '#059669';
          }}
          onMouseOut={(e) => {
            if (!refreshingAll) e.target.style.backgroundColor = '#10b981';
          }}
        >
          {refreshingAll ? '🔄 Refreshing... (This may take a while)' : '🔄 Refresh All Prices'}
        </button>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '24px',
        marginBottom: '48px'
      }}>
        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          padding: '32px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          border: '1px solid #374151'
        }}>
          <p style={{
            fontSize: '14px',
            color: '#9ca3af',
            fontWeight: '600',
            marginBottom: '16px'
          }}>
            TOTAL INVESTED
          </p>
          <p style={{
            fontSize: '36px',
            fontWeight: 'bold',
            color: '#2563eb'
          }}>
            £{totalInvested.toFixed(2)}
          </p>
        </div>

        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          padding: '32px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          border: '1px solid #374151'
        }}>
          <p style={{
            fontSize: '14px',
            color: '#9ca3af',
            fontWeight: '600',
            marginBottom: '16px'
          }}>
            CURRENT VALUE
          </p>
          <p style={{
            fontSize: '36px',
            fontWeight: 'bold',
            color: '#10b981'
          }}>
            £{totalCurrentValue.toFixed(2)}
          </p>
        </div>

        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          padding: '32px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          border: '1px solid #374151'
        }}>
          <p style={{
            fontSize: '14px',
            color: '#9ca3af',
            fontWeight: '600',
            marginBottom: '16px'
          }}>
            PROFIT/LOSS
          </p>
          <p style={{
            fontSize: '36px',
            fontWeight: 'bold',
            color: totalProfitLoss >= 0 ? '#10b981' : '#ef4444'
          }}>
            {totalProfitLoss >= 0 ? '+' : ''}£{totalProfitLoss.toFixed(2)}
          </p>
          <p style={{
            fontSize: '14px',
            color: totalProfitLoss >= 0 ? '#10b981' : '#ef4444',
            marginTop: '8px'
          }}>
            {totalProfitLoss >= 0 ? '+' : ''}{totalROI.toFixed(2)}%
          </p>
        </div>

        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          padding: '32px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          border: '1px solid #374151'
        }}>
          <p style={{
            fontSize: '14px',
            color: '#9ca3af',
            fontWeight: '600',
            marginBottom: '16px'
          }}>
            TOTAL ITEMS
          </p>
          <p style={{
            fontSize: '36px',
            fontWeight: 'bold',
            color: '#8b5cf6'
          }}>
            {totalItems}
          </p>
          <p style={{
            fontSize: '14px',
            color: '#9ca3af',
            marginTop: '8px'
          }}>
            {investments.length} unique
          </p>
        </div>
      </div>

      <TopPerformers />

      {Object.keys(typeBreakdown).length > 0 && (
        <div style={{
          backgroundColor: '#1f2937',
          borderRadius: '12px',
          padding: '40px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          border: '1px solid #374151'
        }}>
          <h3 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: '#f9fafb',
            marginBottom: '32px'
          }}>
            Breakdown by Type
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '24px'
          }}>
            {Object.entries(typeBreakdown).map(([type, data]) => (
              <div key={type} style={{
                border: '2px solid #374151',
                borderRadius: '8px',
                padding: '24px',
                backgroundColor: '#111827'
              }}>
                <p style={{
                  fontSize: '12px',
                  color: '#9ca3af',
                  textTransform: 'uppercase',
                  fontWeight: '600',
                  marginBottom: '12px'
                }}>
                  {type.replace('_', ' ')}
                </p>
                <p style={{
                  fontSize: '24px',
                  fontWeight: '600',
                  color: '#f9fafb',
                  marginBottom: '8px'
                }}>
                  {data.count} item{data.count !== 1 ? 's' : ''}
                </p>
                <p style={{ fontSize: '16px', color: '#9ca3af' }}>
                  £{data.value.toFixed(2)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>

     {/*Portfolio Value Chart */}
      <PortfolioValueChart />

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default Dashboard;
