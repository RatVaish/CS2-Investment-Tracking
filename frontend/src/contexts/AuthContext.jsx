import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../api/auth';
import { getCookie, setCookie, getUserCurrency } from '../api/client';

const AuthContext = createContext(null);

const storeTokens = (accessToken, refreshToken, remember = true) => {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
  if (remember) {
    setCookie('access_token', accessToken, 7);
    setCookie('refresh_token', refreshToken, 30);
  }
};

const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
};

const getStoredToken = () =>
  localStorage.getItem('access_token') || getCookie('access_token');

const getStoredRefreshToken = () =>
  localStorage.getItem('refresh_token') || getCookie('refresh_token');

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

  useEffect(() => {
    const checkAuth = async () => {
      const cookieToken = getCookie('access_token');
      if (cookieToken && !localStorage.getItem('access_token')) {
        localStorage.setItem('access_token', cookieToken);
      }
      const cookieRefresh = getCookie('refresh_token');
      if (cookieRefresh && !localStorage.getItem('refresh_token')) {
        localStorage.setItem('refresh_token', cookieRefresh);
      }

      const token = getStoredToken();
      if (token) await fetchAndSetUser();

      setLoading(false);

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
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  // Called after OAuth (Google/Steam) — tokens already stored by callback page
  const loginWithTokens = async (accessToken, refreshToken, remember = true) => {
    storeTokens(accessToken, refreshToken, remember);
    const userData = await fetchAndSetUser();
    return { success: !!userData, user: userData };
  };

  // Register: does NOT auto-login. Returns needsVerification so modal shows OTP step.
  const register = async (email, username, password) => {
    try {
      await authAPI.register(email, username, password);
      // Now log in to get tokens (user exists but unverified — that's fine)
      const loginResp = await authAPI.login(email, password);
      storeTokens(loginResp.access_token, loginResp.refresh_token, true);
      await fetchAndSetUser();
      return { success: true, needsVerification: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  // After OTP verified — refresh user object so email_verified flips to true
  const completeVerification = async (accessToken, refreshToken) => {
    storeTokens(accessToken, refreshToken, true);
    await fetchAndSetUser();
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
      completeVerification,
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
