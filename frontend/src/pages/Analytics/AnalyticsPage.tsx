import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Calendar, Download } from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../../utils/api';

export const AnalyticsPage = () => {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [period]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboardStats(period);
      setStats(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 slide-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Analytics</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Track your automation performance and insights
          </p>
        </div>
        <div className="flex gap-2">
          {(['7d', '30d', '90d'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`btn ${
                period === p ? 'btn-primary' : 'btn-secondary'
              }`}
            >
              {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard
          label="Total DMs Sent"
          value={loading ? '...' : stats?.total_dms_sent?.toLocaleString() || '0'}
          change={12}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricCard
          label="Success Rate"
          value={loading ? '...' : `${Math.round(stats?.success_rate || 0)}%`}
          change={5}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricCard
          label="Total Triggers"
          value={loading ? '...' : stats?.total_triggers?.toLocaleString() || '0'}
          change={8}
          icon={<Calendar className="w-6 h-6" />}
        />
        <MetricCard
          label="AI Enhanced"
          value={loading ? '...' : `${Math.round(stats?.ai_enhancement_rate || 0)}%`}
          change={-3}
          icon={<TrendingUp className="w-6 h-6" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* DMs Over Time */}
        <div className="card">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
            DMs Sent Over Time
          </h3>
          {loading ? (
            <div className="h-[300px] bg-[var(--bg-secondary)] rounded animate-pulse"></div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats?.daily_breakdown || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" />
                <XAxis
                  dataKey="date"
                  stroke="var(--text-tertiary)"
                  tick={{ fill: 'var(--text-tertiary)' }}
                />
                <YAxis
                  stroke="var(--text-tertiary)"
                  tick={{ fill: 'var(--text-tertiary)' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--bg-primary)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="dms_sent"
                  stroke="var(--accent-primary)"
                  strokeWidth={2}
                  name="DMs Sent"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top Automations */}
        <div className="card">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
            Top Performing Automations
          </h3>
          {loading ? (
            <div className="h-[300px] bg-[var(--bg-secondary)] rounded animate-pulse"></div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  { name: 'Link Please', conversions: 145 },
                  { name: 'Product Info', conversions: 98 },
                  { name: 'FAQ Bot', conversions: 76 },
                  { name: 'Welcome DM', conversions: 54 },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" />
                <XAxis
                  dataKey="name"
                  stroke="var(--text-tertiary)"
                  tick={{ fill: 'var(--text-tertiary)' }}
                />
                <YAxis
                  stroke="var(--text-tertiary)"
                  tick={{ fill: 'var(--text-tertiary)' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--bg-primary)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="conversions" fill="var(--accent-primary)" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Conversion Funnel */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            Conversion Funnel
          </h3>
          <button className="btn btn-secondary text-sm">
            <Download className="w-4 h-4" />
            Export Report
          </button>
        </div>

        <div className="flex items-center justify-between">
          {[
            { label: 'Comments', value: 1000, color: 'bg-purple-500' },
            { label: 'DMs Sent', value: 850, color: 'bg-blue-500' },
            { label: 'Opened', value: 680, color: 'bg-green-500' },
            { label: 'Clicked', value: 340, color: 'bg-yellow-500' },
            { label: 'Converted', value: 170, color: 'bg-pink-500' },
          ].map((stage, index) => (
            <div key={stage.label} className="flex items-center flex-1">
              <div className="text-center flex-1">
                <div className="text-3xl font-bold text-[var(--text-primary)] mb-1">
                  {stage.value}
                </div>
                <div className="text-sm text-[var(--text-secondary)] mb-2">
                  {stage.label}
                </div>
                {index > 0 && (
                  <div className="text-xs text-green-600 dark:text-green-400">
                    {(
                      (stage.value /
                        [1000, 850, 680, 340][index - 1]) *
                      100
                    ).toFixed(0)}
                    %
                  </div>
                )}
                <div className={`h-2 ${stage.color} rounded-full mt-2`}></div>
              </div>
              {index < 4 && (
                <div className="flex-shrink-0 w-8 h-0.5 bg-[var(--border-primary)] mx-2"></div>
              )}
            </div>
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

const MetricCard = ({ label, value, change, icon }: MetricCardProps) => (
  <div className="card">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-[var(--text-secondary)]">{label}</span>
      <div className="p-2 bg-[var(--accent-light)] rounded-lg text-[var(--accent-primary)]">
        {icon}
      </div>
    </div>
    <div className="text-3xl font-bold text-[var(--text-primary)]">{value}</div>
    {change !== undefined && (
      <div
        className={`flex items-center gap-1 mt-2 text-sm ${
          change >= 0 ? 'text-green-600' : 'text-red-600'
        }`}
      >
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
