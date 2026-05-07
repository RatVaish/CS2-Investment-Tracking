import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar';
import client from '../api/client';
import toast from 'react-hot-toast';
import { alertsAPI } from '../api/alerts';

export default function Settings() {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState(user?.username || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [alerts, setAlerts] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [saving, setSaving] = useState(false);

  const isSteamOnly = !user?.password_hash && user?.steam_id;

  const loadAlerts = async () => {
    if (alerts !== null) return;
    try {
      const data = await alertsAPI.list();
      setAlerts(data);
    } catch {}
  };

  const handleSaveUsername = async () => {
    if (!username.trim() || username === user.username) return;
    setSaving(true);
    try {
      await client.put('/users/me', { username });
      await refreshUser();
      toast.success('Username updated');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update username');
    }
    setSaving(false);
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) return toast.error('Passwords do not match');
    if (newPassword.length < 8) return toast.error('Password must be at least 8 characters');
    setSaving(true);
    try {
      await client.post('/users/me/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      toast.success('Password updated');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update password');
    }
    setSaving(false);
  };

  const handleDeleteAlert = async (id) => {
    try {
      await alertsAPI.delete(id);
      setAlerts(prev => prev.filter(a => a.id !== id));
      toast.success('Alert deleted');
    } catch {
      toast.error('Failed to delete alert');
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE') return;
    try {
      await client.delete('/users/me');
      logout();
      navigate('/');
      toast.success('Account deleted');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete account');
    }
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 pt-28 pb-16">
        <h1 className="text-2xl font-bold text-white mb-8">Settings</h1>

        {/* ── Account ── */}
        <section className="mb-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Account</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl divide-y divide-gray-800">

            {/* Username */}
            <div className="p-5">
              <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
              <div className="flex gap-2">
                <input
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  minLength={3} maxLength={50}
                />
                <button
                  onClick={handleSaveUsername}
                  disabled={saving || username === user?.username}
                  className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-500 text-black text-sm font-semibold rounded-lg transition-colors"
                >
                  Save
                </button>
              </div>
            </div>

            {/* Email — read only */}
            <div className="p-5">
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <div className="flex items-center gap-2">
                <p className="text-gray-400 text-sm flex-1">{user?.email || 'No email added'}</p>
                {user?.email_verified ? (
                  <span className="px-2 py-0.5 text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">Verified</span>
                ) : (
                  <span className="px-2 py-0.5 text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full">Unverified</span>
                )}
              </div>
            </div>

            {/* Plan */}
            <div className="p-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-300">Plan</p>
                <p className="text-xs text-gray-500 mt-0.5">{user?.tier === 'pro' ? 'Floatbase Pro' : 'Free tier — 10 investment limit'}</p>
              </div>
              {user?.tier !== 'pro' && (
                <button
                  onClick={() => navigate('/app/billing')}
                  className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm font-medium rounded-lg hover:bg-cyan-500/20 transition-colors"
                >
                  Upgrade
                </button>
              )}
            </div>
          </div>
        </section>

        {/* ── Password ── */}
        {!isSteamOnly && (
          <section className="mb-6">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Password</h2>
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1.5">Current password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1.5">New password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1.5">Confirm new password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>
              <button
                onClick={handleChangePassword}
                disabled={saving || !currentPassword || !newPassword || !confirmPassword}
                className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-500 text-black text-sm font-semibold rounded-lg transition-colors"
              >
                Update Password
              </button>
            </div>
          </section>
        )}

        {/* ── Price Alerts ── */}
        {user?.tier === 'pro' && (
          <section className="mb-6">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Price Alerts</h2>
            <div
              className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden"
              onClick={loadAlerts}
            >
              {alerts === null ? (
                <div className="p-5 text-gray-500 text-sm cursor-pointer hover:text-gray-400 transition-colors">
                  Click to load your alerts
                </div>
              ) : alerts.length === 0 ? (
                <div className="p-5 text-gray-500 text-sm">
                  No active alerts. Set them from any investment detail page.
                </div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {alerts.map(a => (
                    <div key={a.id} className="px-5 py-3.5 flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <p className="text-white text-sm font-medium truncate">{a.item_name}</p>
                        <p className="text-gray-500 text-xs mt-0.5">
                          {a.market.toUpperCase()} · {a.direction === 'above' ? '↑ above' : '↓ below'} ${a.target_price.toFixed(2)}
                          {a.is_triggered && <span className="ml-2 text-amber-400">· triggered</span>}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteAlert(a.id)}
                        className="shrink-0 text-gray-600 hover:text-red-400 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {/* ── Danger Zone ── */}
        <section>
          <h2 className="text-xs font-semibold text-red-500/70 uppercase tracking-wider mb-3">Danger Zone</h2>
          <div className="bg-gray-900 border border-red-500/20 rounded-2xl p-5">
            {!showDeleteConfirm ? (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-300">Delete Account</p>
                  <p className="text-xs text-gray-500 mt-0.5">Permanently delete your account and all data. This cannot be undone.</p>
                </div>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-medium rounded-lg hover:bg-red-500/20 transition-colors shrink-0"
                >
                  Delete Account
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-300">Type <span className="font-mono text-red-400 font-bold">DELETE</span> to confirm</p>
                <input
                  value={deleteConfirmText}
                  onChange={e => setDeleteConfirmText(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-red-500/30 rounded-lg text-white text-sm focus:outline-none focus:border-red-500 transition-colors"
                  placeholder="DELETE"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleDeleteAccount}
                    disabled={deleteConfirmText !== 'DELETE'}
                    className="px-4 py-2 bg-red-500 hover:bg-red-400 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-semibold rounded-lg transition-colors"
                  >
                    Permanently Delete
                  </button>
                  <button
                    onClick={() => { setShowDeleteConfirm(false); setDeleteConfirmText(''); }}
                    className="px-4 py-2 bg-gray-800 text-gray-400 text-sm rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
