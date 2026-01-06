import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Settings, Sparkles, Bell, Shield, CreditCard } from 'lucide-react';

const settingsSections = [
  { name: 'General', href: '/dashboard/settings', icon: Settings },
  { name: 'AI Providers', href: '/dashboard/settings/ai-providers', icon: Sparkles },
  { name: 'Notifications', href: '/dashboard/settings/notifications', icon: Bell },
  { name: 'Security', href: '/dashboard/settings/security', icon: Shield },
  { name: 'Billing', href: '/dashboard/settings/billing', icon: CreditCard },
];

export const SettingsPage: React.FC = () => {
  const location = useLocation();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Sidebar */}
      <div className="lg:col-span-1">
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <nav className="space-y-1">
            {settingsSections.map((section) => {
              const isActive = location.pathname === section.href;
              return (
                <Link
                  key={section.name}
                  to={section.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-purple-50 text-purple-600'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <section.icon className="w-5 h-5" />
                  <span className="font-medium">{section.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="lg:col-span-3">
        <Outlet />
      </div>
    </div>
  );
};
