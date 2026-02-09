import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { login, register } from '../../store/slices/authSlice';
import { api } from '../../utils/api';
import toast from 'react-hot-toast';
import { Mail, Lock, User, Instagram, ArrowRight } from 'lucide-react';

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

        const profile = await api.getUserProfile();
        const onboardingCompleted = profile.onboarding_completed || false;
        localStorage.setItem('onboarding_completed', String(onboardingCompleted));

        toast.success('Welcome back!');

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

        localStorage.setItem('onboarding_completed', 'false');

        toast.success('Account created successfully!');
        navigate('/onboarding');
      } catch (error: any) {
        toast.error(error.message || 'Registration failed');
      }
    }
  };

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
              className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all duration-300 ${
                isLogin
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg scale-105'
                  : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all duration-300 ${
                !isLogin
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
                    className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                    placeholder="johndoe"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    required
                  />
                </div>
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
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
            >
              {loading ? (
                <span>Please wait...</span>
              ) : (
                <>
                  <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                  <ArrowRight className="w-5 h-5" />
                </>
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
