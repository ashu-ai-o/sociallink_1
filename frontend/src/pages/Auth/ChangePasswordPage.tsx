import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, KeyRound, ArrowLeft, ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../utils/api';

type Step = 'request' | 'verify';

export const ChangePasswordPage = () => {
  const [step, setStep] = useState<Step>('request');
  const [otpCode, setOtpCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const navigate = useNavigate();

  // Step 1: Request OTP
  const handleRequestOTP = async () => {
    setLoading(true);
    try {
      await api.requestPasswordChangeOTP();
      setOtpSent(true);
      setStep('verify');
      toast.success('OTP sent to your email!');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP & Change Password
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await api.verifyOTPAndChangePassword({
        otp_code: otpCode,
        new_password: newPassword,
      });
      toast.success('Password changed successfully!');
      navigate('/settings');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white mb-2">
        Change Password
      </h1>
      <p className="text-neutral-600 dark:text-neutral-400 mb-8">
        We'll send a verification code to your email to confirm the change
      </p>

      {step === 'request' ? (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800 max-w-md">
          <div className="text-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mx-auto mb-4">
              <ShieldCheck className="w-7 h-7 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-2">
              Verify Your Identity
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              For security, we'll send a one-time code to your registered email address.
            </p>
          </div>

          <button
            onClick={handleRequestOTP}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
          >
            {loading ? 'Sending...' : 'Send Verification Code'}
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800 max-w-md space-y-5">
          {otpSent && (
            <div className="p-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-xl">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                A verification code has been sent to your email. It expires in 10 minutes.
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Verification Code
            </label>
            <div className="relative group">
              <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
              <input
                type="text"
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all text-center text-xl tracking-[0.4em] font-mono"
                placeholder="000000"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
                autoFocus
                required
              />
            </div>
          </div>

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
              />
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              Must be at least 8 characters
            </p>
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
            disabled={loading || otpCode.length < 6}
            className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
          >
            {loading ? 'Changing...' : 'Change Password'}
          </button>

          <button
            type="button"
            onClick={handleRequestOTP}
            disabled={loading}
            className="w-full text-sm text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors"
          >
            Resend verification code
          </button>
        </form>
      )}
    </div>
  );
};
