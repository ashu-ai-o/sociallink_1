import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { login, register } from '../../store/slices/authSlice';
import { api } from '../../utils/api';
import toast from 'react-hot-toast';
import { Mail, Lock, User, Chrome, ArrowRight, Check, Sparkles } from 'lucide-react';

export const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    confirmPassword: '',
  });

  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { loading } = useAppSelector((state) => state.auth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isLogin) {
      try {
        await dispatch(login({ email: formData.email, password: formData.password })).unwrap();

        // Check onboarding status
        const profile = await api.getUserProfile();
        const onboardingCompleted = profile.onboarding_completed || false;
        localStorage.setItem('onboarding_completed', String(onboardingCompleted));

        toast.success('Welcome back!');

        // Redirect based on onboarding status
        if (!onboardingCompleted) {
          navigate('/onboarding');
        } else {
          navigate('/dashboard');
        }
      } catch (error: any) {
        toast.error(error.message || 'Login failed');
      }
    } else {
      if (formData.password !== formData.confirmPassword) {
        toast.error('Passwords do not match');
        return;
      }

      try {
        await dispatch(
          register({
            email: formData.email,
            username: formData.username,
            password: formData.password,
          })
        ).unwrap();

        // New users always need onboarding
        localStorage.setItem('onboarding_completed', 'false');

        toast.success('Account created successfully!');
        navigate('/onboarding');
      } catch (error: any) {
        toast.error(error.message || 'Registration failed');
      }
    }
  };

  const handleGoogleLogin = () => {
    toast('Google OAuth coming soon!');
  };

  const benefits = [
    'Automate Instagram DM responses',
    'AI-powered message personalization',
    'Real-time analytics & insights',
    'Unlimited automations & contacts'
  ];

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-12 items-center">

        {/* Left Side - Branding & Benefits */}
        <div className="hidden lg:block space-y-8 fade-in">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-sm font-medium">
              <Sparkles className="w-4 h-4" />
              Welcome to LinkPlease
            </div>
            <h1 className="text-5xl font-bold text-[var(--text-primary)] leading-tight">
              Transform Your<br />
              Instagram Engagement
            </h1>
            <p className="text-xl text-[var(--text-secondary)] leading-relaxed">
              Automate responses, boost conversions, and never miss a customer opportunity.
            </p>
          </div>

          <div className="space-y-4">
            {benefits.map((benefit, index) => (
              <div
                key={index}
                className={`flex items-center gap-4 p-4 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm hover-lift stagger-${index + 1} fade-in`}
              >
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <Check className="w-5 h-5 text-white" />
                </div>
                <p className="text-[var(--text-primary)] font-medium">{benefit}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-8 pt-8">
            <div>
              <div className="text-3xl font-bold text-[var(--text-primary)]">10K+</div>
              <div className="text-sm text-[var(--text-secondary)]">Active Users</div>
            </div>
            <div className="w-px h-12 bg-gray-300 dark:bg-gray-700"></div>
            <div>
              <div className="text-3xl font-bold text-[var(--text-primary)]">1M+</div>
              <div className="text-sm text-[var(--text-secondary)]">Messages Sent</div>
            </div>
            <div className="w-px h-12 bg-gray-300 dark:bg-gray-700"></div>
            <div>
              <div className="text-3xl font-bold text-[var(--text-primary)]">99.9%</div>
              <div className="text-sm text-[var(--text-secondary)]">Uptime</div>
            </div>
          </div>
        </div>

        {/* Right Side - Auth Form */}
        <div className="w-full max-w-md mx-auto scale-in">
          <div className="card shadow-2xl">
            {/* Tab Switcher */}
            <div className="flex gap-2 mb-8 p-1 bg-[var(--bg-secondary)] rounded-xl">
              <button
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
                  isLogin
                    ? 'bg-white dark:bg-gray-700 text-[var(--text-primary)] shadow-sm transform scale-[1.02]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
                  !isLogin
                    ? 'bg-white dark:bg-gray-700 text-[var(--text-primary)] shadow-sm transform scale-[1.02]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                Sign Up
              </button>
            </div>

            <div className="mb-8">
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
                {isLogin ? 'Welcome back!' : 'Create your account'}
              </h2>
              <p className="text-[var(--text-secondary)]">
                {isLogin
                  ? 'Enter your credentials to access your account'
                  : 'Start automating your Instagram engagement today'}
              </p>
            </div>

            {/* Google Sign In */}
            <button
              onClick={handleGoogleLogin}
              className="w-full btn btn-secondary mb-6 justify-center hover-lift"
            >
              <Chrome className="w-5 h-5" />
              Continue with Google
            </button>

            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[var(--border-primary)]"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white dark:bg-gray-800 text-[var(--text-tertiary)] font-medium">
                  Or continue with email
                </span>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              {!isLogin && (
                <div className="fade-in">
                  <label className="label">Username</label>
                  <div className="relative group">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)] transition-colors group-focus-within:text-[var(--accent-primary)]" />
                    <input
                      type="text"
                      className="input pl-12"
                      placeholder="johndoe"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      required
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="label">Email address</label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)] transition-colors group-focus-within:text-[var(--accent-primary)]" />
                  <input
                    type="email"
                    className="input pl-12"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Password</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)] transition-colors group-focus-within:text-[var(--accent-primary)]" />
                  <input
                    type="password"
                    className="input pl-12"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required
                    minLength={6}
                  />
                </div>
              </div>

              {!isLogin && (
                <div className="fade-in">
                  <label className="label">Confirm Password</label>
                  <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)] transition-colors group-focus-within:text-[var(--accent-primary)]" />
                    <input
                      type="password"
                      className="input pl-12"
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
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      className="w-4 h-4 cursor-pointer"
                    />
                    <span className="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                      Remember me
                    </span>
                  </label>
                  <Link
                    to="/auth/reset-password"
                    className="text-sm font-medium text-[var(--accent-primary)] hover:text-[var(--accent-hover)] transition-colors"
                  >
                    Forgot password?
                  </Link>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full btn btn-primary btn-lg justify-center group"
              >
                {loading ? (
                  <>
                    <div className="spinner" />
                    <span>Please wait...</span>
                  </>
                ) : (
                  <>
                    <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                    <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                  </>
                )}
              </button>
            </form>

            {!isLogin && (
              <p className="text-xs text-[var(--text-tertiary)] text-center mt-6 leading-relaxed">
                By signing up, you agree to our{' '}
                <Link to="/terms" className="text-[var(--accent-primary)] hover:text-[var(--accent-hover)] font-medium transition-colors">
                  Terms of Service
                </Link>{' '}
                and{' '}
                <Link to="/privacy" className="text-[var(--accent-primary)] hover:text-[var(--accent-hover)] font-medium transition-colors">
                  Privacy Policy
                </Link>
              </p>
            )}

            {isLogin && (
              <p className="text-sm text-[var(--text-secondary)] text-center mt-6">
                Don't have an account?{' '}
                <button
                  onClick={() => setIsLogin(false)}
                  className="text-[var(--accent-primary)] hover:text-[var(--accent-hover)] font-medium transition-colors"
                >
                  Sign up for free
                </button>
              </p>
            )}
          </div>

          {/* Mobile Stats */}
          <div className="lg:hidden flex items-center justify-center gap-8 mt-8 text-center fade-in">
            <div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">10K+</div>
              <div className="text-xs text-[var(--text-secondary)]">Users</div>
            </div>
            <div className="w-px h-10 bg-gray-300 dark:bg-gray-700"></div>
            <div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">1M+</div>
              <div className="text-xs text-[var(--text-secondary)]">Messages</div>
            </div>
            <div className="w-px h-10 bg-gray-300 dark:bg-gray-700"></div>
            <div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">99.9%</div>
              <div className="text-xs text-[var(--text-secondary)]">Uptime</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
