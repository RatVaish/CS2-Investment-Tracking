import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import GoogleCallback from './pages/GoogleCallback';

function App() {
  const { isAuthenticated, loading } = useAuth();

  // Show loading screen while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public route */}
      <Route path="/" element={<Landing />} />

      {/* Protected route */}
      <Route
        path="/app/*"
        element={
          isAuthenticated ? <Dashboard /> : <Navigate to="/" replace />
        }
      />

      <Route
          path="/auth/callback"
          element={<GoogleCallback />}
      />


      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;