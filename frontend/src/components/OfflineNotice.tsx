import React, { useState, useEffect } from 'react';
import { WifiOff } from 'lucide-react';

export const OfflineNotice: React.FC = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  if (isOnline) return null;
  
  return (
    <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white px-4 py-3 z-50">
      <div className="flex items-center justify-center gap-2">
        <WifiOff className="w-5 h-5" />
        <span className="font-medium">You're offline. Some features may be unavailable.</span>
      </div>
    </div>
  );
};
