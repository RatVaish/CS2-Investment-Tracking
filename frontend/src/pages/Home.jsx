import { Link } from 'react-router-dom';

function Home() {
  const cardStyle = {
    backgroundColor: '#1f2937',
    borderRadius: '12px',
    padding: '32px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    border: '1px solid #374151'
  };

  return (
    <div>
      {/* Hero Section */}
      <div style={{ textAlign: 'center', marginBottom: '80px' }}>
        <h1 style={{
          fontSize: '64px',
          fontWeight: 'bold',
          color: '#f9fafb',
          marginBottom: '24px'
        }}>
          CS2 Investment Tracker
        </h1>
        <p style={{
          fontSize: '24px',
          color: '#9ca3af',
          marginBottom: '48px'
        }}>
          Track, manage, and analyze your Counter-Strike 2 investments
        </p>
        <Link
          to="/dashboard"
          style={{
            display: 'inline-block',
            padding: '20px 48px',
            fontSize: '20px',
            fontWeight: '600',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            borderRadius: '8px',
            textDecoration: 'none'
          }}
          onMouseOver={(e) => e.target.style.backgroundColor = '#1d4ed8'}
          onMouseOut={(e) => e.target.style.backgroundColor = '#2563eb'}
        >
          Get Started
        </Link>
      </div>

      {/* Feature Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '32px',
        marginTop: '64px'
      }}>
        <Link to="/dashboard" style={{ textDecoration: 'none' }}>
          <div
            style={cardStyle}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';
            }}
          >
            <div style={{ fontSize: '64px', marginBottom: '24px' }}>📊</div>
            <h2 style={{
              fontSize: '28px',
              fontWeight: '600',
              color: '#f9fafb',
              marginBottom: '16px'
            }}>
              Dashboard
            </h2>
            <p style={{ fontSize: '16px', color: '#9ca3af' }}>
              View your portfolio overview and performance metrics
            </p>
          </div>
        </Link>

        <Link to="/manage" style={{ textDecoration: 'none' }}>
          <div
            style={cardStyle}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';
            }}
          >
            <div style={{ fontSize: '64px', marginBottom: '24px' }}>➕</div>
            <h2 style={{
              fontSize: '28px',
              fontWeight: '600',
              color: '#f9fafb',
              marginBottom: '16px'
            }}>
              Manage
            </h2>
            <p style={{ fontSize: '16px', color: '#9ca3af' }}>
              Add new investments to your portfolio
            </p>
          </div>
        </Link>

        <Link to="/portfolio" style={{ textDecoration: 'none' }}>
          <div
            style={cardStyle}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';
            }}
          >
            <div style={{ fontSize: '64px', marginBottom: '24px' }}>📋</div>
            <h2 style={{
              fontSize: '28px',
              fontWeight: '600',
              color: '#f9fafb',
              marginBottom: '16px'
            }}>
              Portfolio
            </h2>
            <p style={{ fontSize: '16px', color: '#9ca3af' }}>
              Detailed table view with sorting and filtering
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
}

export default Home;
