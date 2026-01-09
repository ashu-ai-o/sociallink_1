import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { login, register } from '../../store/slices/authSlice';
import toast from 'react-hot-toast';
import { Mail, Lock, User, Chrome } from 'lucide-react';

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
        toast.success('Welcome back!');
        navigate('/dashboard');
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
        toast.success('Account created successfully!');
        navigate('/dashboard');
      } catch (error: any) {
        toast.error(error.message || 'Registration failed');
      }
    }
  };

  const handleGoogleLogin = () => {
    toast('Google OAuth coming soon!', { icon: '🚀' });
  };

  return (
    <div className="slide-in-up">
      {/* Tab Switcher */}
      <div className="flex gap-2 mb-8 p-1 bg-[var(--bg-secondary)] rounded-lg">
        <button
          onClick={() => setIsLogin(true)}
          className={`flex-1 py-2.5 rounded-lg font-medium transition-all ${
            isLogin
              ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm'
              : 'text-[var(--text-secondary)]'
          }`}
        >
          Sign In
        </button>
        <button
          onClick={() => setIsLogin(false)}
          className={`flex-1 py-2.5 rounded-lg font-medium transition-all ${
            !isLogin
              ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm'
              : 'text-[var(--text-secondary)]'
          }`}
        >
          Sign Up
        </button>
      </div>

      <h2 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
        {isLogin ? 'Welcome back' : 'Create account'}
      </h2>
      <p className="text-[var(--text-secondary)] mb-8">
        {isLogin
          ? 'Sign in to continue to your account'
          : 'Get started with LinkPlease Pro'}
      </p>

      {/* Google Sign In */}
      <button
        onClick={handleGoogleLogin}
        className="w-full btn btn-secondary mb-6 justify-center"
      >
        <Chrome className="w-5 h-5" />
        Continue with Google
      </button>

      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[var(--border-primary)]"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-[var(--bg-secondary)] text-[var(--text-tertiary)]">
            Or continue with email
          </span>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {!isLogin && (
          <div>
            <label className="label">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)]" />
              <input
                type="text"
                className="input pl-10"
                placeholder="johndoe"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
              />
            </div>
          </div>
        )}

        <div>
          <label className="label">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)]" />
            <input
              type="email"
              className="input pl-10"
              placeholder="you@example.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>
        </div>

        <div>
          <label className="label">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)]" />
            <input
              type="password"
              className="input pl-10"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
          </div>
        </div>

        {!isLogin && (
          <div>
            <label className="label">Confirm Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)]" />
              <input
                type="password"
                className="input pl-10"
                placeholder="••••••••"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                required
              />
            </div>
          </div>
        )}

        {isLogin && (
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2">
              <input type="checkbox" className="w-4 h-4" />
              <span className="text-sm text-[var(--text-secondary)]">Remember me</span>
            </label>
            <Link
              to="/auth/reset-password"
              className="text-sm text-[var(--accent-primary)] hover:underline"
            >
              Forgot password?
            </Link>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full btn btn-primary justify-center"
        >
          {loading ? (
            <>
              <div className="spinner" />
              <span>Please wait...</span>
            </>
          ) : isLogin ? (
            'Sign In'
          ) : (
            'Create Account'
          )}
        </button>
      </form>

      {!isLogin && (
        <p className="text-xs text-[var(--text-tertiary)] text-center mt-6">
          By signing up, you agree to our{' '}
          <a href="#" className="text-[var(--accent-primary)] hover:underline">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="#" className="text-[var(--accent-primary)] hover:underline">
            Privacy Policy
          </a>
        </p>
      )}
    </div>
  );
};
