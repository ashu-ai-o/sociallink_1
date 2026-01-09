// ============================================================================
// src/components/Layout/MainLayout.tsx

import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { SettingsPopup } from './SettingsPopup';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout = ({ children }: MainLayoutProps) => {
  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-secondary)]">
      <Sidebar />
      
      <div className="flex-1 flex flex-col md:ml-64">
        <Header />
        
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>

      <SettingsPopup />
    </div>
  );
};
