import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../api/auth';
import { getCookie, setCookie, getUserCurrency } from '../api/client';

const AuthContext = createContext(null);

// Token storage helpers — use both localStorage AND a long-lived cookie
// so sessions survive browser restarts
const storeTokens = (accessToken, refreshToken, remember = true) => {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
  if (remember) {
    setCookie('access_token', accessToken, 7);    // 7 days
    setCookie('refresh_token', refreshToken, 30); // 30 days
  }
};

const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  // Clear cookies too
  document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
};

const getStoredToken = () => {
  // Check localStorage first, then cookie fallback
  return localStorage.getItem('access_token') || getCookie('access_token');
};

const getStoredRefreshToken = () => {
  return localStorage.getItem('refresh_token') || getCookie('refresh_token');
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAndSetUser = useCallback(async () => {
    try {
      const userData = await authAPI.getProfile();
      setUser(userData);
      return userData;
    } catch {
      return null;
    }
  }, []);

  // On mount: restore session from stored tokens, dispatch currency event
  useEffect(() => {
    const checkAuth = async () => {
      // Restore token from cookie if localStorage is empty (new tab/browser restart)
      const cookieToken = getCookie('access_token');
      if (cookieToken && !localStorage.getItem('access_token')) {
        localStorage.setItem('access_token', cookieToken);
      }
      const cookieRefresh = getCookie('refresh_token');
      if (cookieRefresh && !localStorage.getItem('refresh_token')) {
        localStorage.setItem('refresh_token', cookieRefresh);
      }

      const token = getStoredToken();
      if (token) {
        await fetchAndSetUser();
      }

      setLoading(false);

      // Dispatch currency event so Navbar updates without refresh
      const currency = getUserCurrency();
      window.dispatchEvent(new CustomEvent('currencychange', { detail: currency }));
    };

    checkAuth();
  }, [fetchAndSetUser]);

  const login = async (email, password, remember = true) => {
    try {
      const response = await authAPI.login(email, password);
      storeTokens(response.access_token, response.refresh_token, remember);
      const userData = await fetchAndSetUser();
      return { success: true, user: userData };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  };

  // Called after OAuth (Google/Steam) — tokens already stored by callback page
  const loginWithTokens = async (accessToken, refreshToken, remember = true) => {
    storeTokens(accessToken, refreshToken, remember);
    const userData = await fetchAndSetUser();
    return { success: !!userData, user: userData };
  };

  const register = async (email, username, password) => {
    try {
      await authAPI.register(email, username, password);
      return await login(email, password);
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      };
    }
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      loginWithTokens,
      register,
      logout,
      isAuthenticated: !!user,
      loading,
      refreshUser: fetchAndSetUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
