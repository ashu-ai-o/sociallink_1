import React from 'react';
import { useDashboard } from '../../hooks/useDashboard';
import { TrendingUp, Zap, Send, Activity } from 'lucide-react';

export const RealTimeDashboard: React.FC = () => {
  const { stats, isConnected } = useDashboard();

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Live Updates' : 'Reconnecting...'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<Zap className="w-6 h-6" />}
          label="Active Automations"
          value={stats.active_automations}
          total={stats.total_automations}
          color="purple"
        />

        <StatCard
          icon={<Send className="w-6 h-6" />}
          label="Total DMs Sent"
          value={stats.total_dms_sent}
          color="blue"
          animated
        />

        <StatCard
          icon={<Activity className="w-6 h-6" />}
          label="Total Triggers"
          value={stats.total_triggers}
          color="green"
        />

        <StatCard
          icon={<TrendingUp className="w-6 h-6" />}
          label="Today's Triggers"
          value={stats.today_triggers}
          color="orange"
          animated
        />
      </div>
    </div>
  );
};

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  total?: number;
  color: 'purple' | 'blue' | 'green' | 'orange';
  animated?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  icon,
  label,
  value,
  total,
  color,
  animated,
}) => {
  const colorClasses = {
    purple: 'bg-purple-50 text-purple-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>{icon}</div>
      </div>
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p
        className={`text-3xl font-bold text-gray-900 ${
          animated ? 'animate-pulse' : ''
        }`}
      >
        {value.toLocaleString()}
      </p>
      {total !== undefined && (
        <p className="text-sm text-gray-500 mt-1">of {total}</p>
      )}
    </div>
  );
};
