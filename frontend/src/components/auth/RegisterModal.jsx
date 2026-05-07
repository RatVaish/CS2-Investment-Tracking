import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { authAPI } from '../../api/auth';

function RegisterModal({ onClose, onSwitchToLogin }) {
  const [step, setStep] = useState('register'); // 'register' | 'verify'
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [verified, setVerified] = useState(false);
  const { register, completeVerification } = useAuth();
  const navigate = useNavigate();
  const codeRefs = useRef([]);

  // Cooldown timer for resend
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setTimeout(() => setResendCooldown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [resendCooldown]);

  // Auto-close after success
  useEffect(() => {
    if (!verified) return;
    const t = setTimeout(() => { onClose(); navigate('/app'); }, 2000);
    return () => clearTimeout(t);
  }, [verified]);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) return setError('Passwords do not match');
    if (password.length < 8) return setError('Password must be at least 8 characters');

    setLoading(true);
    const result = await register(email, username, password);
    setLoading(false);

    if (result.success) {
      setStep('verify');
      setResendCooldown(60);
      setTimeout(() => codeRefs.current[0]?.focus(), 100);
    } else {
      setError(result.error);
    }
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
      setVerified(true);
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
      setError(err.response?.data?.detail || 'Failed to resend. Try again.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-md bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="p-8">
          {verified ? (
            <div className="text-center py-4">
              <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/30 rounded-full flex items-center justify-center mx-auto mb-5">
                <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Email verified!</h2>
              <p className="text-gray-400 text-sm">Taking you to your dashboard...</p>
            </div>
          ) : step === 'register' ? (            <>
              <h2 className="text-3xl font-bold text-white mb-2">Create Account</h2>
              <p className="text-gray-400 mb-8">Start tracking your CS2 investments</p>

              {error && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}

              <form onSubmit={handleRegister} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="you@example.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="trader123"
                    minLength={3}
                    maxLength={50}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="••••••••"
                    minLength={8}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Confirm Password</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="••••••••"
                    minLength={8}
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg font-semibold transition-all"
                >
                  {loading ? 'Creating account...' : 'Create Account'}
                </button>
              </form>

              <div className="mt-5 text-center">
                <p className="text-gray-400 text-sm">
                  Already have an account?{' '}
                  <button onClick={onSwitchToLogin} className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors">
                    Sign in
                  </button>
                </p>
              </div>

              <p className="mt-4 text-center text-gray-600 text-xs leading-relaxed">
                By creating an account, you agree to our{' '}
                <a href="/terms" className="text-gray-500 hover:text-gray-400 underline" target="_blank" rel="noopener noreferrer">Terms of Service</a>
                {' '}and{' '}
                <a href="/privacy" className="text-gray-500 hover:text-gray-400 underline" target="_blank" rel="noopener noreferrer">Privacy Policy</a>.
              </p>
            </>
          ) : (
            <>
              {/* OTP verification step */}
              <div className="text-center mb-8">
                <div className="w-14 h-14 bg-cyan-500/10 border border-cyan-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-7 h-7 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
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

              {/* 6-digit input */}
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
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default RegisterModal;
