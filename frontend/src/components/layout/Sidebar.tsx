// src/components/Layout/Sidebar.tsx
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Zap,
  BarChart3,
  Users,
  Settings,
  Moon,
  Sun,
  Menu,
  X,
  LogOut,
  Instagram,
} from 'lucide-react';
import { useAppDispatch, useAppSelector, useTheme } from '../../hooks/';
import { openSettings, toggleSidebar } from '../../store/slices/uiSlice';
import { logout } from '../../store/slices/authSlice';
import toast from 'react-hot-toast';


interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Automations', path: '/automations', icon: Zap },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'Contacts', path: '/contacts', icon: Users },
];

export const Sidebar = () => {
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { theme, toggleTheme } = useTheme();
  const { isOpen } = useAppSelector((state) => state.ui.sidebar);
  const user = useAppSelector((state) => state.auth.user);

  const handleLogout = () => {
    dispatch(logout());
    toast.success('Logged out successfully');
  };

  const handleSettingsClick = () => {
    dispatch(openSettings());
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden fade-in"
          onClick={() => dispatch(toggleSidebar())}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed left-0 top-0 h-screen w-64 z-50
          flex flex-col
          bg-[var(--bg-primary)] border-r border-[var(--border-primary)]
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-[var(--border-primary)]">
          <Link to="/dashboard" className="flex items-center gap-2">
            <Instagram className="w-6 h-6 text-[var(--accent-primary)]" />
            <span className="text-lg font-bold text-[var(--text-primary)]">
              LinkPlease
            </span>
          </Link>
          
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="md:hidden p-2 rounded-lg hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 overflow-y-auto">
          <div className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || 
                               location.pathname.startsWith(item.path + '/');
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => window.innerWidth < 768 && dispatch(toggleSidebar())}
                  className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-lg
                    text-sm font-medium transition-all
                    ${
                      isActive
                        ? 'bg-[var(--accent-light)] text-[var(--accent-primary)]'
                        : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-[var(--border-primary)] space-y-1">
          {/* User Info */}
          {user && (
            <div className="px-3 py-2 mb-2">
              <div className="text-sm font-medium text-[var(--text-primary)] truncate">
                {user.username}
              </div>
              <div className="text-xs text-[var(--text-tertiary)] truncate">
                {user.email}
              </div>
              <div className="mt-1">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--accent-light)] text-[var(--accent-primary)]">
                  {user.plan.toUpperCase()}
                </span>
              </div>
            </div>
          )}

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-all"
          >
            {theme === 'light' ? (
              <>
                <Moon className="w-5 h-5" />
                <span>Dark Mode</span>
              </>
            ) : (
              <>
                <Sun className="w-5 h-5" />
                <span>Light Mode</span>
              </>
            )}
          </button>

          {/* Settings */}
          <button
            onClick={handleSettingsClick}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-all"
          >
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </button>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--error)] hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
          >
            <LogOut className="w-5 h-5" />
            <span>Log Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};