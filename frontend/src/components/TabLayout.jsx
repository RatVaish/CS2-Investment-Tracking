import { NavLink, Outlet, useLocation } from 'react-router-dom';

function TabLayout() {
  const location = useLocation();
  const isHome = location.pathname === '/';

  const tabStyle = (isActive) => ({
    padding: '16px 48px',
    fontSize: '20px',
    fontWeight: '600',
    borderRadius: '8px',
    textDecoration: 'none',
    transition: 'all 0.2s',
    backgroundColor: isActive ? '#2563eb' : '#374151',
    color: '#ffffff'
  });

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#111827' }}>
      {/* Top Navigation Bar */}
      {!isHome && (
        <nav style={{
          backgroundColor: '#1f2937',
          borderBottom: '2px solid #374151',
          padding: '24px 0'
        }}>
          <div style={{
            maxWidth: '1280px',
            margin: '0 auto',
            padding: '0 64px'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '32px'
            }}>
              <NavLink
                to="/dashboard"
                style={({ isActive }) => tabStyle(isActive)}
                onMouseOver={(e) => {
                  if (e.target.style.backgroundColor !== 'rgb(37, 99, 235)') {
                    e.target.style.backgroundColor = '#4b5563';
                  }
                }}
                onMouseOut={(e) => {
                  if (e.target.style.backgroundColor !== 'rgb(37, 99, 235)') {
                    e.target.style.backgroundColor = '#374151';
                  }
                }}
              >
                Dashboard
              </NavLink>

              <NavLink
                to="/manage"
                style={({ isActive }) => tabStyle(isActive)}
                onMouseOver={(e) => {
                  if (e.target.style.backgroundColor !== 'rgb(37, 99, 235)') {
                    e.target.style.backgroundColor = '#4b5563';
                  }
                }}
                onMouseOut={(e) => {
                  if (e.target.style.backgroundColor !== 'rgb(37, 99, 235)') {
                    e.target.style.backgroundColor = '#374151';
                  }
                }}
              >
                Manage
              </NavLink>

              <NavLink
                to="/portfolio"
                style={({ isActive }) => tabStyle(isActive)}
                onMouseOver={(e) => {
                  if (e.target.style.backgroundColor !== 'rgb(37, 99, 235)') {
                    e.target.style.backgroundColor = '#4b5563';
                  }
                }}
                onMouseOut={(e) => {
                  if (e.target.style.backgroundColor !== 'rgb(37, 99, 235)') {
                    e.target.style.backgroundColor = '#374151';
                  }
                }}
              >
                Portfolio
              </NavLink>
            </div>
          </div>
        </nav>
      )}

      {/* Main Content */}
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: isHome ? '80px 64px' : '64px 64px'
      }}>
        <Outlet />
      </div>
    </div>
  );
}

export default TabLayout;
