// ============================================================================
// src/components/Layout/AuthLayout.tsx

import { Link } from 'react-router-dom';
import { Instagram, Moon, Sun } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export const AuthLayout = ({ children }: AuthLayoutProps) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-[var(--bg-secondary)] flex">
      {/* Left Side - Hero */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-purple-600 to-pink-600 p-12 flex-col justify-between text-white">
        <div>
          <Link to="/" className="flex items-center gap-2 mb-12">
            <Instagram className="w-8 h-8" />
            <span className="text-2xl font-bold">LinkPlease Pro</span>
          </Link>

          <h1 className="text-5xl font-bold mb-6">
            Automate Your Instagram DMs with AI
          </h1>
          <p className="text-xl opacity-90 mb-8">
            Turn comments into conversations. Send personalized DMs automatically when users engage with your posts.
          </p>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-2xl">
                ✓
              </div>
              <div>
                <div className="font-semibold">AI-Powered Messages</div>
                <div className="text-sm opacity-80">
                  Claude AI personalizes every DM
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-2xl">
                ✓
              </div>
              <div>
                <div className="font-semibold">Instant Responses</div>
                <div className="text-sm opacity-80">
                  Reply to comments in seconds
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-2xl">
                ✓
              </div>
              <div>
                <div className="font-semibold">Increase Conversions</div>
                <div className="text-sm opacity-80">
                  67% higher conversion rates
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="text-sm opacity-75">
          Trusted by 10,000+ Instagram businesses worldwide
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="absolute top-8 right-8 p-3 rounded-lg hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] transition-colors"
        >
          {theme === 'light' ? (
            <Moon className="w-5 h-5" />
          ) : (
            <Sun className="w-5 h-5" />
          )}
        </button>

        {/* Mobile Logo */}
        <div className="lg:hidden absolute top-8 left-8">
          <Link to="/" className="flex items-center gap-2">
            <Instagram className="w-6 h-6 text-[var(--accent-primary)]" />
            <span className="text-lg font-bold text-[var(--text-primary)]">
              LinkPlease
            </span>
          </Link>
        </div>

        <div className="w-full max-w-md">
          {children}
        </div>
      </div>
    </div>
  );
};