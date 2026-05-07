import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getUserCurrency, setUserCurrency, SUPPORTED_CURRENCIES } from '../utils/currency';
import { notificationsAPI } from '../api/notifications';

const NAV_TABS = [
  { label: 'Dashboard', path: '/app' },
  { label: 'Portfolio', path: '/app/portfolio' },
  { label: 'Add Investment', path: '/app/add' },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [currency, setCurrencyState] = useState(getUserCurrency());
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const menuRef = useRef(null);
  const notifRef = useRef(null);

  const isPro = user?.tier === 'pro';

  // Poll unread count every 60 seconds
  const fetchUnreadCount = useCallback(async () => {
    if (!user) return;
    try {
      const count = await notificationsAPI.unreadCount();
      setUnreadCount(count);
    } catch {}
  }, [user]);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  const handleOpenNotifications = async () => {
    setShowNotifications(v => !v);
    setShowUserMenu(false);
    if (!showNotifications) {
      try {
        const data = await notificationsAPI.list();
        setNotifications(data);
        if (unreadCount > 0) {
          await notificationsAPI.markAllRead();
          setUnreadCount(0);
        }
      } catch {}
    }
  };

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setShowUserMenu(false);
      if (notifRef.current && !notifRef.current.contains(e.target)) setShowNotifications(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleCurrencyChange = (c) => {
    setUserCurrency(c);
    setCurrencyState(c);
    window.dispatchEvent(new CustomEvent('currencychange', { detail: c }));
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => {
    if (path === '/app') return location.pathname === '/app';
    return location.pathname.startsWith(path);
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-950/95 backdrop-blur border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <button onClick={() => navigate('/app')} className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-md flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <span className="font-bold text-white tracking-tight">
            Float<span className="text-cyan-400">base</span>
          </span>
        </button>

        <div className="flex items-center gap-1">
          {NAV_TABS.map(tab => (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive(tab.path)
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          {!isPro && (
            <button
              onClick={() => navigate('/app/billing')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm font-medium hover:bg-cyan-500/20 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3l14 9-14 9V3z" />
              </svg>
              Upgrade
            </button>
          )}

          <select
            value={currency}
            onChange={(e) => handleCurrencyChange(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            {SUPPORTED_CURRENCIES.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          {/* Notification bell */}
          <div className="relative" ref={notifRef}>
            <button
              onClick={handleOpenNotifications}
              className="relative w-9 h-9 flex items-center justify-center rounded-lg bg-gray-800 border border-gray-700 hover:border-gray-600 transition-colors"
            >
              <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-cyan-500 text-black text-[10px] font-bold rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-gray-900 border border-gray-700 rounded-xl shadow-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
                  <p className="text-white text-sm font-semibold">Notifications</p>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="px-4 py-8 text-center">
                      <svg className="w-8 h-8 text-gray-700 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                      </svg>
                      <p className="text-gray-600 text-sm">No notifications yet</p>
                    </div>
                  ) : (
                    notifications.map(n => (
                      <div
                        key={n.id}
                        onClick={() => {
                          if (n.metadata_?.item_id) {
                            navigate(`/investments/${n.metadata_.item_id}`);
                            setShowNotifications(false);
                          }
                        }}
                        className={`px-4 py-3 border-b border-gray-800/50 hover:bg-gray-800/50 transition-colors ${n.metadata_?.item_id ? 'cursor-pointer' : ''}`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 flex items-center justify-center shrink-0 mt-0.5">
                            <svg className="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                            </svg>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-white text-sm font-medium">{n.title}</p>
                            {n.body && <p className="text-gray-400 text-xs mt-0.5 leading-relaxed">{n.body}</p>}
                            <p className="text-gray-600 text-xs mt-1">{timeAgo(n.created_at)}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifications(false); }}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800 border border-gray-700 hover:border-gray-600 transition-colors"
            >
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="" className="w-6 h-6 rounded-full" />
              ) : (
                <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center">
                  <span className="text-cyan-400 text-xs font-bold">
                    {user?.username?.[0]?.toUpperCase() || 'U'}
                  </span>
                </div>
              )}
              <span className="text-gray-300 text-sm">{user?.username || 'User'}</span>
              <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showUserMenu && (
              <div className="absolute right-0 top-full mt-2 w-52 bg-gray-900 border border-gray-700 rounded-xl shadow-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-800">
                  <p className="text-white text-sm font-medium">{user?.username}</p>
                  <p className="text-gray-500 text-xs truncate">{user?.email}</p>
                  <span className={`inline-block mt-1.5 px-2 py-0.5 text-xs rounded-full border capitalize font-medium ${
                    isPro
                      ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                      : 'bg-gray-800 text-gray-400 border-gray-700'
                  }`}>
                    {isPro ? '⚡ Pro' : 'Free'}
                  </span>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => { navigate('/app/billing'); setShowUserMenu(false); }}
                    className="w-full px-4 py-2.5 text-left text-sm text-gray-300 hover:bg-gray-800 transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                    {isPro ? 'Manage Billing' : 'Upgrade to Pro'}
                  </button>
                  <button
                    onClick={() => { navigate('/app/settings'); setShowUserMenu(false); }}
                    className="w-full px-4 py-2.5 text-left text-sm text-gray-300 hover:bg-gray-800 transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Settings
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-2.5 text-left text-sm text-red-400 hover:bg-red-500/10 transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
