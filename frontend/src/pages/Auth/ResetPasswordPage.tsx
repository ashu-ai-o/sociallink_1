import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Lock, ShieldCheck, KeyRound } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../utils/api';

type Step = 'email' | 'otp' | 'newPassword' | 'success';

export const ResetPasswordPage = () => {
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // Step 1: Request OTP
  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.requestForgotPasswordOTP(email);
      toast.success('OTP code sent to your email!');
      setStep('otp');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.verifyForgotPasswordOTP({ email, otp_code: otpCode, verify_only: true });
      toast.success('OTP verified! Set your new password.');
      setStep('newPassword');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Invalid or expired OTP code');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Set new password
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      await api.verifyForgotPasswordOTP({ email, otp_code: otpCode, new_password: newPassword });
      toast.success('Password reset successfully!');
      setStep('success');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  // ---- Step Labels ----
  const steps = [
    { key: 'email', label: 'Email', icon: Mail },
    { key: 'otp', label: 'Verify OTP', icon: ShieldCheck },
    { key: 'newPassword', label: 'New Password', icon: Lock },
  ];

  const currentStepIndex = steps.findIndex((s) => s.key === step);

  // ---- Success Screen ----
  if (step === 'success') {
    return (
      <div className="text-center">
        <div className="w-16 h-16 rounded-2xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto mb-6">
          <ShieldCheck className="w-8 h-8 text-green-600 dark:text-green-400" />
        </div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-2">
          Password Reset Complete
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400 mb-8">
          Your password has been updated successfully. You can now sign in with your new password.
        </p>
        <Link
          to="/auth"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
        >
          Back to Sign In
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Link
        to="/auth"
        className="inline-flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Sign In
      </Link>

      <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-2">
        Reset your password
      </h2>
      <p className="text-neutral-600 dark:text-neutral-400 mb-6">
        We'll send a verification code to your email
      </p>

      {/* Step Progress Bar */}
      <div className="flex items-center gap-2 mb-8">
        {steps.map((s, index) => (
          <div key={s.key} className="flex items-center gap-2 flex-1">
            <div
              className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold transition-all ${index <= currentStepIndex
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-500/30'
                  : 'bg-neutral-200 dark:bg-neutral-700 text-neutral-500'
                }`}
            >
              {index + 1}
            </div>
            <span
              className={`text-xs font-medium hidden sm:block ${index <= currentStepIndex
                  ? 'text-purple-600 dark:text-purple-400'
                  : 'text-neutral-400'
                }`}
            >
              {s.label}
            </span>
            {index < steps.length - 1 && (
              <div
                className={`flex-1 h-0.5 rounded-full ${index < currentStepIndex
                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600'
                    : 'bg-neutral-200 dark:bg-neutral-700'
                  }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Email */}
      {step === 'email' && (
        <form onSubmit={handleRequestOTP} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Email Address
            </label>
            <div className="relative group">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
              <input
                type="email"
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
          >
            {loading ? 'Sending...' : 'Send Verification Code'}
          </button>
        </form>
      )}

      {/* Step 2: OTP Verification */}
      {step === 'otp' && (
        <form onSubmit={handleVerifyOTP} className="space-y-5">
          <div className="p-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-xl mb-4">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              A 6-digit verification code has been sent to <strong>{email}</strong>. It expires in 10 minutes.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Verification Code
            </label>
            <div className="relative group">
              <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
              <input
                type="text"
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all text-center text-2xl tracking-[0.5em] font-mono"
                placeholder="000000"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
                autoFocus
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || otpCode.length < 6}
            className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
          >
            {loading ? 'Verifying...' : 'Verify Code'}
          </button>

          <button
            type="button"
            onClick={() => setStep('email')}
            className="w-full text-sm text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors mt-2"
          >
            Didn't receive the code? Go back
          </button>
        </form>
      )}

      {/* Step 3: New Password */}
      {step === 'newPassword' && (
        <form onSubmit={handleResetPassword} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              New Password
            </label>
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
              <input
                type="password"
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                placeholder="••••••••"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                autoFocus
              />
            </div>
            <p className="text-xs text-neutral-500 mt-1">Must be at least 8 characters</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Confirm New Password
            </label>
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
              <input
                type="password"
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
          >
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>
      )}
    </div>
  );
};
