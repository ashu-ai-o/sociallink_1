import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/automations/';

export const useAutomations = () => {
  const [automations, setAutomations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'automations_list':
        setAutomations(message.data);
        setLoading(false);
        break;

      case 'automation_updated':
        setAutomations((prev) =>
          prev.map((a) =>
            a.id === message.automation_id
              ? { ...a, is_active: message.is_active }
              : a
          )
        );
        break;

      case 'automation_triggered':
        console.log('🔔 Automation triggered:', message.trigger_data);
        // Update UI or show notification
        break;

      case 'dm_sent':
        console.log('📨 DM sent to:', message.recipient);
        // Show success notification
        setAutomations((prev) =>
          prev.map((a) =>
            a.id === message.automation_id
              ? { ...a, total_dms_sent: a.total_dms_sent + 1 }
              : a
          )
        );
        break;

      case 'error':
        console.error('WebSocket error:', message.message);
        break;
    }
  };

  const { isConnected, sendMessage } = useWebSocket({
    url: WS_URL,
    onMessage: handleMessage,
    onConnect: () => {
      // Request initial data
      sendMessage({ action: 'get_automations' });
    },
  });

  const toggleAutomation = (automationId: string) => {
    sendMessage({
      action: 'toggle_automation',
      automation_id: automationId,
    });
  };

  const subscribeToAutomation = (automationId: string) => {
    sendMessage({
      action: 'subscribe_automation',
      automation_id: automationId,
    });
  };

  return {
    automations,
    loading,
    isConnected,
    toggleAutomation,
    subscribeToAutomation,
  };
};
