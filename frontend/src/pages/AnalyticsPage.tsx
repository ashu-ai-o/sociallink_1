import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import { api } from '../lib/api';

export const AnalyticsPage: React.FC = () => {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  const { data: stats } = useQuery(['analytics', period], () =>
    api.getDashboardStats(period)
  );

  const { data: performance } = useQuery('automation-performance', () =>
    api.getAutomationPerformance()
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <div className="flex gap-2">
          {(['7d', '30d', '90d'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                period === p
                  ? 'bg-purple-600 text-white'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <MetricCard
          label="Total DMs Sent"
          value={stats?.total_dms_sent || 0}
          change={stats?.dms_change || 0}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricCard
          label="Success Rate"
          value={`${stats?.success_rate || 0}%`}
          change={stats?.success_change || 0}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricCard
          label="Avg Response Time"
          value={`${stats?.avg_response_time || 0}s`}
          change={stats?.response_change || 0}
          icon={<Calendar className="w-6 h-6" />}
        />
        <MetricCard
          label="Active Automations"
          value={stats?.active_automations || 0}
          icon={<TrendingUp className="w-6 h-6" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* DMs Over Time */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            DMs Sent Over Time
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats?.daily_breakdown || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="dms_sent"
                stroke="#8b5cf6"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Automation Performance */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top Performing Automations
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performance?.top_automations || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="conversions" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Conversion Funnel */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Conversion Funnel
        </h3>
        <div className="flex items-center justify-between">
          {[
            { label: 'Comments', value: 1000 },
            { label: 'DMs Sent', value: 850 },
            { label: 'Opened', value: 680 },
            { label: 'Clicked', value: 340 },
            { label: 'Converted', value: 170 },
          ].map((stage, index) => (
            <React.Fragment key={stage.label}>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">
                  {stage.value}
                </div>
                <div className="text-sm text-gray-600 mt-1">{stage.label}</div>
                {index > 0 && (
                  <div className="text-xs text-green-600 mt-1">
                    {((stage.value / [1000, 850, 680, 340][index - 1]) * 100).toFixed(0)}%
                  </div>
                )}
              </div>
              {index < 4 && (
                <div className="flex-1 h-1 bg-gray-200 mx-4" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, change, icon }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600">{label}</span>
        <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
          {icon}
        </div>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
      {change !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-sm ${
          change >= 0 ? 'text-green-600' : 'text-red-600'
        }`}>
          {change >= 0 ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span>{Math.abs(change)}% vs last period</span>
        </div>
      )}
    </div>
  );
};
