import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/dashboard/';

interface DashboardStats {
  total_automations: number;
  active_automations: number;
  total_dms_sent: number;
  total_triggers: number;
  today_triggers: number;
}

export const useDashboard = () => {
  const [stats, setStats] = useState<DashboardStats>({
    total_automations: 0,
    active_automations: 0,
    total_dms_sent: 0,
    total_triggers: 0,
    today_triggers: 0,
  });

  const handleMessage = (message: any) => {
    if (message.type === 'stats_update') {
      setStats(message.data);
    }
  };

  const { isConnected } = useWebSocket({
    url: WS_URL,
    onMessage: handleMessage,
  });

  return { stats, isConnected };
};
