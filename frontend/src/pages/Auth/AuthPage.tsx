import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { login, register as registerUser, verify2FA, clear2FA, clearVerification } from '../../store/slices/authSlice';
import { api } from '../../utils/api';
import toast from 'react-hot-toast';
import { Mail, Lock, User, Instagram, ArrowRight, Shield, ArrowLeft, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

export const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    confirmPassword: '',
  });
  const [twoFACode, setTwoFACode] = useState('');

  // Username availability state
  const [usernameAvailable, setUsernameAvailable] = useState<boolean | null>(null);
  const [isCheckingUsername, setIsCheckingUsername] = useState(false);
  const [usernameError, setUsernameError] = useState('');

  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { loading, requires2FA, twoFAEmail, twoFAPassword, requiresVerification, verificationEmail } = useAppSelector(
    (state) => state.auth
  );

  // Real-time username check
  useEffect(() => {
    if (isLogin || !formData.username || formData.username.length < 3) {
      setUsernameAvailable(null);
      setIsCheckingUsername(false);
      setUsernameError('');
      return;
    }

    const checkAvailability = async () => {
      setIsCheckingUsername(true);
      try {
        const response = await api.checkUsername(formData.username);
        setUsernameAvailable(response.available);
        if (!response.available) {
          setUsernameError('Username is already taken');
        } else {
          setUsernameError('');
        }
      } catch (error) {
        console.error('Failed to check username', error);
      } finally {
        setIsCheckingUsername(false);
      }
    };

    const timer = setTimeout(checkAvailability, 500);
    return () => clearTimeout(timer);
  }, [formData.username, isLogin]);

  const handleGoogleLogin = async () => {
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!googleClientId) {
      toast.error('Google Login is not configured yet.');
      return;
    }
    // Use Google Identity Services to get an access token
    const client = (window as any).google?.accounts?.oauth2?.initTokenClient({
      client_id: googleClientId,
      scope: 'email profile',
      callback: async (tokenResponse: any) => {
        if (tokenResponse.error) {
          toast.error('Google Login failed');
          return;
        }
        try {
          const response = await api.googleAuth(tokenResponse.access_token);
          localStorage.setItem('access_token', response.tokens.access);
          localStorage.setItem('refresh_token', response.tokens.refresh);

          const profile = await api.getUserProfile();

          toast.success('Welcome back!');

          localStorage.setItem('onboarding_completed', String(profile.onboarding_completed));
          localStorage.setItem('onboarding_step', String(profile.onboarding_step || 0));

          if (!profile.onboarding_completed) {
            navigate('/onboarding');
          } else {
            navigate('/dashboard');
          }
        } catch (error: any) {
          toast.error(error?.response?.data?.error || error.message || 'Google Login failed');
        }
      },
    });
    if (client) {
      client.requestAccessToken();
    } else {
      toast.error('Google Login is not available. Please try again.');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isLogin) {
      try {
        const result = await dispatch(login({ email: formData.email, password: formData.password })).unwrap();

        if (result.requires_2fa) {
          // 2FA required — handled by authSlice, UI will switch to 2FA input
          toast('Two-factor authentication required');
          return;
        }

        const profile = await api.getUserProfile();

        toast.success('Welcome back!');

        localStorage.setItem('onboarding_completed', String(profile.onboarding_completed));
        localStorage.setItem('onboarding_step', String(profile.onboarding_step || 0));

        if (!profile.onboarding_completed) {
          navigate('/onboarding');
        } else {
          navigate('/dashboard');
        }
      } catch (error: any) {
        if (error?.requires_verification) {
          toast.error('Please verify your email before logging in.');
        } else {
          toast.error(error?.message || 'Login failed');
        }
      }
    } else {
      if (formData.password !== formData.confirmPassword) {
        toast.error('Passwords do not match');
        return;
      }

      try {
        await dispatch(
          registerUser({
            email: formData.email,
            username: formData.username,
            password: formData.password,
          })
        ).unwrap();

        localStorage.setItem('onboarding_completed', 'false');
        localStorage.setItem('onboarding_step', '0');

        toast.success('Account created! Please check your email to verify your account.');
        setIsLogin(true);
      } catch (error: any) {
        toast.error(error?.message || error || 'Registration failed');
      }
    }
  };

  const handle2FASubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!twoFAEmail || !twoFAPassword) return;

    try {
      await dispatch(verify2FA({ email: twoFAEmail, password: twoFAPassword, token: twoFACode })).unwrap();

      const profile = await api.getUserProfile();
      localStorage.setItem('onboarding_completed', String(profile.onboarding_completed));
      localStorage.setItem('onboarding_step', String(profile.onboarding_step || 0));

      toast.success('Welcome back!');
      if (!profile.onboarding_completed) {
        navigate('/onboarding');
      } else {
        navigate('/dashboard');
      }
    } catch (error: any) {
      toast.error(error || 'Invalid 2FA code');
    }
  };

  const handleResendVerification = async () => {
    try {
      await api.resendVerificationEmail();
      toast.success('Verification email sent!');
    } catch {
      toast.error('Failed to resend verification email');
    }
  };

  // ---- Email Verification Required Screen ----
  if (requiresVerification) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-3 mb-6 group">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-2xl border border-white/30 group-hover:scale-110 transition-transform">
              <Instagram className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold text-white">DmMe</span>
          </Link>
        </div>

        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-3xl blur-2xl transform translate-y-4 translate-x-2"></div>
          <div className="relative bg-white/95 dark:bg-neutral-900/95 backdrop-blur-xl rounded-3xl p-8 border border-white/20 shadow-2xl">
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mx-auto mb-6">
                <Mail className="w-8 h-8 text-amber-600 dark:text-amber-400" />
              </div>
              <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-2">
                Verify Your Email
              </h2>
              <p className="text-neutral-600 dark:text-neutral-400 mb-6">
                We've sent a verification link to <strong className="text-neutral-900 dark:text-white">{verificationEmail}</strong>. Please check your inbox and click the link to activate your account.
              </p>
              <button
                onClick={handleResendVerification}
                className="w-full px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white rounded-xl font-medium shadow-lg shadow-amber-500/30 transition-all hover:scale-[1.02] active:scale-[0.98] mb-4"
              >
                Resend Verification Email
              </button>
              <button
                onClick={() => dispatch(clearVerification())}
                className="text-sm text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors"
              >
                Back to Sign In
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---- 2FA Verification Screen ----
  if (requires2FA) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-3 mb-6 group">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-2xl border border-white/30 group-hover:scale-110 transition-transform">
              <Instagram className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold text-white">DmMe</span>
          </Link>
        </div>

        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-3xl blur-2xl transform translate-y-4 translate-x-2"></div>
          <div className="relative bg-white/95 dark:bg-neutral-900/95 backdrop-blur-xl rounded-3xl p-8 border border-white/20 shadow-2xl">
            <button
              onClick={() => {
                dispatch(clear2FA());
                setTwoFACode('');
              }}
              className="inline-flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 mb-6 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Sign In
            </button>

            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-2xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-2">
                Two-Factor Authentication
              </h2>
              <p className="text-neutral-600 dark:text-neutral-400">
                Enter the 6-digit code from your authenticator app or a backup code
              </p>
            </div>

            <form onSubmit={handle2FASubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                  Authentication Code
                </label>
                <div className="relative group">
                  <Shield className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
                  <input
                    type="text"
                    className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all text-center text-2xl tracking-[0.5em] font-mono"
                    placeholder="000000"
                    value={twoFACode}
                    onChange={(e) => setTwoFACode(e.target.value.replace(/\D/g, '').slice(0, 8))}
                    maxLength={8}
                    autoFocus
                    required
                  />
                </div>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2">
                  You can also use a backup code (8 characters)
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || twoFACode.length < 6}
                className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
              >
                {loading ? (
                  <span>Verifying...</span>
                ) : (
                  <>
                    <span>Verify & Sign In</span>
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // ---- Main Auth Form (Login / Register) ----
  return (
    <div className="w-full max-w-md mx-auto">
      {/* Logo */}
      <div className="text-center mb-8">
        <Link to="/" className="inline-flex items-center gap-3 mb-6 group">
          <div className="p-3 bg-white/20 backdrop-blur-sm rounded-2xl border border-white/30 group-hover:scale-110 transition-transform">
            <Instagram className="w-7 h-7 text-white" />
          </div>
          <span className="text-3xl font-bold text-white">
            DmMe
          </span>
        </Link>
      </div>

      {/* 3D Auth Card */}
      <div className="relative">
        {/* 3D shadow layers */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-3xl blur-2xl transform translate-y-4 translate-x-2"></div>

        <div className="relative bg-white/95 dark:bg-neutral-900/95 backdrop-blur-xl rounded-3xl p-8 border border-white/20 shadow-2xl">
          {/* Tab Switcher */}
          <div className="flex gap-2 mb-8 p-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-2xl">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all duration-300 ${isLogin
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg scale-105'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
                }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all duration-300 ${!isLogin
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg scale-105'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
                }`}
            >
              Sign Up
            </button>
          </div>

          {/* Header */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-2">
              {isLogin ? 'Welcome back' : 'Create your account'}
            </h2>
            <p className="text-neutral-600 dark:text-neutral-400">
              {isLogin
                ? 'Sign in to access your dashboard'
                : 'Start automating your Instagram engagement'}
            </p>
          </div>

          {/* Google OAuth Button */}
          {isLogin && (
            <div className="mb-6">
              <button
                type="button"
                onClick={() => handleGoogleLogin()}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 px-6 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                <span>{loading ? 'Connecting...' : 'Continue with Google'}</span>
              </button>

              <div className="flex items-center gap-4 my-6">
                <div className="flex-1 h-px bg-neutral-200 dark:bg-neutral-700"></div>
                <span className="text-sm text-neutral-500 dark:text-neutral-400">or</span>
                <div className="flex-1 h-px bg-neutral-200 dark:bg-neutral-700"></div>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <div className="animate-fadeIn">
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                  Username
                </label>
                <div className="relative group">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
                  <input
                    type="text"
                    className={`w-full pl-12 pr-12 py-3 bg-white dark:bg-neutral-800 border rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:border-transparent transition-all ${usernameAvailable === true
                      ? 'border-emerald-500/50 focus:ring-emerald-500'
                      : usernameAvailable === false
                        ? 'border-red-500/50 focus:ring-red-500'
                        : 'border-neutral-200 dark:border-neutral-700 focus:ring-purple-600'
                      }`}
                    placeholder="johndoe"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    required
                  />
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center">
                    {isCheckingUsername ? (
                      <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
                    ) : usernameAvailable === true ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500 animate-in zoom-in duration-300" />
                    ) : usernameAvailable === false ? (
                      <XCircle className="w-5 h-5 text-red-500 animate-in zoom-in duration-300" />
                    ) : null}
                  </div>
                </div>
                {usernameError && (
                  <p className="mt-1.5 text-xs text-red-500 flex items-center gap-1 animate-in fade-in slide-in-from-top-1">
                    <XCircle className="w-3 h-3" />
                    {usernameError}
                  </p>
                )}
                {usernameAvailable === true && (
                  <p className="mt-1.5 text-xs text-emerald-500 flex items-center gap-1 animate-in fade-in slide-in-from-top-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Username is available
                  </p>
                )}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Email address
              </label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
                <input
                  type="email"
                  className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Password
              </label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
                <input
                  type="password"
                  className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  minLength={6}
                />
              </div>
            </div>

            {!isLogin && (
              <div className="animate-fadeIn">
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                  Confirm Password
                </label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-purple-600 transition-colors" />
                  <input
                    type="password"
                    className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    required
                    minLength={6}
                  />
                </div>
              </div>
            )}

            {isLogin && (
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-neutral-300 dark:border-neutral-700 text-purple-600 focus:ring-purple-600"
                  />
                  <span className="text-neutral-600 dark:text-neutral-400">Remember me</span>
                </label>
                <Link
                  to="/auth/reset-password"
                  className="font-medium bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent hover:opacity-80 transition-opacity"
                >
                  Forgot password?
                </Link>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || (!isLogin && usernameAvailable === false) || isCheckingUsername}
              className={`relative w-full h-[56px] overflow-hidden rounded-xl font-semibold shadow-lg transition-all duration-300 ${loading
                  ? 'bg-neutral-200 dark:bg-neutral-800 cursor-not-allowed scale-[0.98]'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-purple-500/30 hover:scale-[1.01] active:scale-[0.99]'
                }`}
            >
              {loading ? (
                <div className="absolute inset-0 flex items-center justify-center bg-neutral-200 dark:bg-neutral-800">
                  {/* Shimmer Effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full animate-shimmer"></div>

                  {/* Pulsing Glow */}
                  <div className="absolute inset-0 bg-purple-500/10 animate-pulse"></div>

                  <div className="relative flex items-center gap-3 text-neutral-600 dark:text-neutral-400">
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                      <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                      <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce"></span>
                    </div>
                    <span className="text-sm tracking-wide font-medium animate-pulse">
                      {isLogin ? 'Authenticating' : 'Creating Account'}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2 animate-in fade-in zoom-in duration-500">
                  <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </div>
              )}
            </button>
          </form>

          {/* Footer */}
          {!isLogin && (
            <p className="text-xs text-neutral-500 text-center mt-6">
              By signing up, you agree to our{' '}
              <Link to="/terms" className="bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent hover:opacity-80 font-medium">
                Terms
              </Link>{' '}
              and{' '}
              <Link to="/privacy" className="bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent hover:opacity-80 font-medium">
                Privacy Policy
              </Link>
            </p>
          )}
        </div>
      </div>

      {/* Social Proof */}
      <div className="mt-8 text-center">
        <p className="text-sm text-white/80 mb-4">
          Trusted by 10,000+ Instagram businesses
        </p>
        <div className="flex items-center justify-center gap-8">
          <div>
            <div className="text-2xl font-bold text-white">10K+</div>
            <div className="text-xs text-white/70">Active Users</div>
          </div>
          <div className="w-px h-10 bg-white/20"></div>
          <div>
            <div className="text-2xl font-bold text-white">1M+</div>
            <div className="text-xs text-white/70">Messages Sent</div>
          </div>
          <div className="w-px h-10 bg-white/20"></div>
          <div>
            <div className="text-2xl font-bold text-white">99.9%</div>
            <div className="text-xs text-white/70">Uptime</div>
          </div>
        </div>
      </div>
    </div>
  );
};

