import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

export const ResetPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      setSent(true);
      setLoading(false);
      toast.success('Password reset email sent!');
    }, 1500);
  };

  if (sent) {
    return (
      <div className="text-center slide-in-up">
        <div className="w-16 h-16 rounded-full bg-[var(--accent-light)] flex items-center justify-center mx-auto mb-6">
          <Mail className="w-8 h-8 text-[var(--accent-primary)]" />
        </div>
        <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
          Check your email
        </h2>
        <p className="text-[var(--text-secondary)] mb-8">
          We've sent a password reset link to <strong>{email}</strong>
        </p>
        <Link to="/auth" className="btn btn-primary">
          Back to Sign In
        </Link>
      </div>
    );
  }

  return (
    <div className="slide-in-up">
      <Link
        to="/auth"
        className="inline-flex items-center gap-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] mb-8"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Sign In
      </Link>

      <h2 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
        Reset your password
      </h2>
      <p className="text-[var(--text-secondary)] mb-8">
        Enter your email and we'll send you a reset link
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)]" />
            <input
              type="email"
              className="input pl-10"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full btn btn-primary justify-center"
        >
          {loading ? (
            <>
              <div className="spinner" />
              <span>Sending...</span>
            </>
          ) : (
            'Send Reset Link'
          )}
        </button>
      </form>
    </div>
  );
};
