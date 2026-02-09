import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, Zap, BarChart3, Users, Settings, Menu, X 
} from 'lucide-react';

export const MobileNav: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  
  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Dashboard' },
    { path: '/dashboard/automations', icon: Zap, label: 'Automations' },
    { path: '/dashboard/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/dashboard/contacts', icon: Users, label: 'Contacts' },
    { path: '/dashboard/settings', icon: Settings, label: 'Settings' },
  ];
  
  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 bg-white border-b border-gray-200 px-4 py-3 z-50">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">DmMe</h1>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg active:scale-95 min-h-[44px] min-w-[44px] flex items-center justify-center"
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>
      
      {/* Mobile Menu Overlay */}
      {isOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      {/* Mobile Menu */}
      <div className={`
        lg:hidden fixed top-[57px] right-0 w-64 bg-white border-l border-gray-200 h-full z-40
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
      `}>
        <nav className="p-4 space-y-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                  min-h-[48px] touch-manipulation active:scale-98
                  ${isActive
                    ? 'bg-purple-50 text-purple-600'
                    : 'text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
      
      {/* Bottom Navigation (Alternative) */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
        <nav className="flex items-center justify-around px-2 py-2">
          {navItems.slice(0, 5).map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex flex-col items-center gap-1 px-3 py-2 rounded-lg
                  min-w-[60px] min-h-[56px] touch-manipulation active:scale-95
                  ${isActive ? 'text-purple-600' : 'text-gray-600'}
                `}
              >
                <item.icon className={`w-6 h-6 ${isActive ? 'stroke-2' : ''}`} />
                <span className="text-xs">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </>
  );
};
