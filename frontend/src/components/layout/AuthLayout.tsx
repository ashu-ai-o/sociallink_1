import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export const AuthLayout = ({ children }: AuthLayoutProps) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen relative overflow-hidden bg-transparent">
      {/* Grid pattern overlay */}
      <div className="absolute inset-0 opacity-[0.01] dark:opacity-[0.02] pointer-events-none text-neutral-900 dark:text-white" style={{
        backgroundImage: `linear-gradient(currentColor 1px, transparent 1px),
                         linear-gradient(90deg, currentColor 1px, transparent 1px)`,
        backgroundSize: '50px 50px'
      }}></div>

      {/* Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="absolute top-4 right-4 sm:top-8 sm:right-8 p-3 rounded-xl bg-neutral-900/5 dark:bg-white/10 backdrop-blur-md border border-neutral-900/10 dark:border-white/20 hover:bg-neutral-900/10 dark:hover:bg-white/20 text-neutral-900 dark:text-white transition-all z-20"
        title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
      >
        {theme === 'light' ? (
          <Moon className="w-5 h-5" />
        ) : (
          <Sun className="w-5 h-5" />
        )}
      </button>

      {/* Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4 sm:p-6 lg:p-8">
        {children}
      </div>
    </div>
  );
};
