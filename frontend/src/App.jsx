import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuth } from './contexts/AuthContext';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import InvestmentDetail from './pages/InvestmentDetail';
import GoogleCallback from './pages/GoogleCallback';
import Billing from './pages/Billing';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import Cookies from './pages/Cookies';
import Import from './pages/Import';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/" replace />;
}

function App() {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-400 text-sm font-mono">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
            fontFamily: 'system-ui, sans-serif',
          },
          success: { iconTheme: { primary: '#06b6d4', secondary: '#0f172a' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#0f172a' } },
        }}
      />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/auth/callback" element={<GoogleCallback />} />

        <Route path="/app/*" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/app/billing" element={<ProtectedRoute><Billing /></ProtectedRoute>} />
        <Route path="/app/import" element={<ProtectedRoute><Import /></ProtectedRoute>} />
        <Route path="/investments/:id" element={<ProtectedRoute><InvestmentDetail /></ProtectedRoute>} />

        {/* Legal pages */}
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/cookies" element={<Cookies />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default App;
