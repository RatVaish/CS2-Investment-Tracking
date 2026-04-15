import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { authAPI } from '../../api/auth';

/**
 * VerifyEmailModal — shown for:
 * 1. Existing unverified email/password users (has email, not verified)
 * 2. Steam users who need to add + verify an email
 */
export default function VerifyEmailModal({ onClose }) {
  const { user, completeVerification, refreshUser } = useAuth();

  // Steam users have no real email yet
  const needsEmailEntry = !user?.email || user.email.endsWith('@steam.placeholder');

  const [step, setStep] = useState(needsEmailEntry ? 'add-email' : 'verify');
  const [email, setEmail] = useState(needsEmailEntry ? '' : (user?.email || ''));
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const codeRefs = useRef([]);

  // Auto-send code when modal opens for users who already have an email
  useEffect(() => {
    if (step === 'verify' && !needsEmailEntry) {
      handleSendCode();
    }
  }, []);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setTimeout(() => setResendCooldown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [resendCooldown]);

  const handleSendCode = async () => {
    setError('');
    try {
      await authAPI.sendVerificationCode();
      setResendCooldown(60);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send code.');
    }
  };

  const handleAddEmail = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authAPI.addEmail(email);
      setStep('verify');
      setResendCooldown(60);
      setTimeout(() => codeRefs.current[0]?.focus(), 100);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add email.');
    }
    setLoading(false);
  };

  const handleCodeInput = (index, value) => {
    if (!/^\d?$/.test(value)) return;
    const next = [...code];
    next[index] = value;
    setCode(next);
    if (value && index < 5) codeRefs.current[index + 1]?.focus();
  };

  const handleCodeKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      codeRefs.current[index - 1]?.focus();
    }
  };

  const handleCodePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      setCode(pasted.split(''));
      codeRefs.current[5]?.focus();
    }
  };

  const handleVerify = async () => {
    const fullCode = code.join('');
    if (fullCode.length !== 6) return setError('Enter the 6-digit code');
    setError('');
    setLoading(true);
    try {
      const result = await authAPI.verifyCode(fullCode);
      await completeVerification(result.access_token, result.refresh_token);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid code. Please try again.');
    }
    setLoading(false);
  };

  const handleResend = async () => {
    if (resendCooldown > 0) return;
    setError('');
    try {
      await authAPI.sendVerificationCode();
      setResendCooldown(60);
      setCode(['', '', '', '', '', '']);
      codeRefs.current[0]?.focus();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to resend.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-md bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="p-8">
          {step === 'add-email' ? (
            <>
              <div className="text-center mb-8">
                <div className="w-14 h-14 bg-cyan-500/10 border border-cyan-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-7 h-7 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Add your email</h2>
                <p className="text-gray-400 text-sm">
                  Add an email address to enable price alerts and account notifications.
                </p>
              </div>

              {error && (
                <div className="mb-5 p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
                  <p className="text-red-400 text-sm text-center">{error}</p>
                </div>
              )}

              <form onSubmit={handleAddEmail} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Email address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="you@example.com"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg font-semibold transition-all"
                >
                  {loading ? 'Sending code...' : 'Send verification code'}
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="text-center mb-8">
                <div className="w-14 h-14 bg-cyan-500/10 border border-cyan-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-7 h-7 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Check your email</h2>
                <p className="text-gray-400 text-sm">
                  We sent a 6-digit code to<br />
                  <span className="text-white font-medium">{email}</span>
                </p>
              </div>

              {error && (
                <div className="mb-5 p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
                  <p className="text-red-400 text-sm text-center">{error}</p>
                </div>
              )}

              <div className="flex gap-2 justify-center mb-6" onPaste={handleCodePaste}>
                {code.map((digit, i) => (
                  <input
                    key={i}
                    ref={el => codeRefs.current[i] = el}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={e => handleCodeInput(i, e.target.value)}
                    onKeyDown={e => handleCodeKeyDown(i, e)}
                    className="w-12 h-14 text-center text-xl font-bold bg-gray-800 border border-gray-700 rounded-xl text-white focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                ))}
              </div>

              <button
                onClick={handleVerify}
                disabled={loading || code.join('').length !== 6}
                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg font-semibold transition-all mb-4"
              >
                {loading ? 'Verifying...' : 'Verify Email'}
              </button>

              <p className="text-center text-sm text-gray-500">
                Didn't get it?{' '}
                <button
                  onClick={handleResend}
                  disabled={resendCooldown > 0}
                  className="text-cyan-400 hover:text-cyan-300 disabled:text-gray-600 transition-colors"
                >
                  {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
                </button>
              </p>

              {needsEmailEntry && (
                <p className="text-center text-xs text-gray-600 mt-3">
                  Wrong email?{' '}
                  <button onClick={() => setStep('add-email')} className="text-gray-500 hover:text-gray-400 underline">
                    Change it
                  </button>
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
