import React from 'react';
import { useAutomations } from '../../hooks/useAutomations';
import { AutomationCard } from './AutomationCard';
import { Plus, RefreshCw } from 'lucide-react';

export const AutomationsPageRealTime: React.FC = () => {
  const { automations, loading, isConnected, toggleAutomation } = useAutomations();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Automations</h1>
          <div className="flex items-center gap-2 mt-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <p className="text-sm text-gray-600">
              {isConnected ? 'Real-time updates active' : 'Reconnecting...'}
            </p>
          </div>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors">
          <Plus className="w-5 h-5" />
          New Automation
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {automations.map((automation) => (
          <AutomationCard
            key={automation.id}
            automation={automation}
            onToggle={() => toggleAutomation(automation.id)}
            onEdit={() => {}}
            onDelete={() => {}}
          />
        ))}
      </div>
    </div>
  );
};

