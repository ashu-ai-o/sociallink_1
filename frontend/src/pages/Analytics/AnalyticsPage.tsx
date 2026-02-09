// ============================================================================
// ANALYTICS PAGE - Clean performance metrics with ZapDM-inspired design
// ============================================================================

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Calendar, MessageCircle, Send, Zap } from 'lucide-react';
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
      const data = await api.getDashboardOverview(period);
      setStats(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const periodLabels = {
    '7d': 'Last 7 days',
    '30d': 'Last 30 days',
    '90d': 'Last 90 days',
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white">
            Analytics
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            Track your automation performance and engagement
          </p>
        </div>

        {/* Period Selector */}
        <div className="flex gap-2 bg-neutral-100 dark:bg-neutral-900 rounded-lg p-1">
          {(['7d', '30d', '90d'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                period === p
                  ? 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white shadow-sm'
                  : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
              }`}
            >
              {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Period Label */}
      <div className="text-sm text-neutral-600 dark:text-neutral-400">
        Showing data for {periodLabels[period]}
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          label="Messages Sent"
          value={loading ? '...' : stats?.total_dms_sent?.toLocaleString() || '0'}
          subtitle="Total automated DMs"
          icon={<Send className="w-5 h-5" />}
          iconBgColor="bg-blue-50 dark:bg-blue-900/20"
          iconColor="text-blue-600 dark:text-blue-400"
        />
        <MetricCard
          label="Success Rate"
          value={loading ? '...' : `${Math.round(stats?.success_rate || 0)}%`}
          subtitle="Delivered successfully"
          icon={<TrendingUp className="w-5 h-5" />}
          iconBgColor="bg-green-50 dark:bg-green-900/20"
          iconColor="text-green-600 dark:text-green-400"
        />
        <MetricCard
          label="Total Triggers"
          value={loading ? '...' : stats?.total_triggers?.toLocaleString() || '0'}
          subtitle="Comments processed"
          icon={<MessageCircle className="w-5 h-5" />}
          iconBgColor="bg-amber-50 dark:bg-amber-900/20"
          iconColor="text-amber-600 dark:text-amber-400"
        />
        <MetricCard
          label="Active Automations"
          value={loading ? '...' : stats?.active_automations?.toString() || '0'}
          subtitle={`${stats?.total_automations || 0} total`}
          icon={<Zap className="w-5 h-5" />}
          iconBgColor="bg-neutral-100 dark:bg-neutral-800"
          iconColor="text-neutral-700 dark:text-neutral-300"
        />
      </div>

      {/* Performance Overview */}
      <div className="group relative">
        <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-2xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300"></div>
        <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
        <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-6">
          Performance Overview
        </h2>

        <div className="space-y-6">
          {/* Success Rate Bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                Delivery Success Rate
              </span>
              <span className="text-lg font-semibold text-neutral-900 dark:text-white">
                {loading ? '...' : `${Math.round(stats?.success_rate || 0)}%`}
              </span>
            </div>
            <div className="w-full h-3 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-500"
                style={{ width: `${stats?.success_rate || 0}%` }}
              ></div>
            </div>
            <p className="text-xs text-neutral-500 mt-2">
              Messages delivered successfully to recipients
            </p>
          </div>

          {/* Engagement Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-neutral-200 dark:border-neutral-800">
            <div>
              <div className="text-2xl font-semibold text-neutral-900 dark:text-white">
                {loading ? '...' : stats?.total_dms_sent || 0}
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Total DMs Sent
              </div>
            </div>
            <div>
              <div className="text-2xl font-semibold text-neutral-900 dark:text-white">
                {loading ? '...' : stats?.total_triggers || 0}
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Comments Triggered
              </div>
            </div>
            <div>
              <div className="text-2xl font-semibold text-neutral-900 dark:text-white">
                {loading ? '...' : stats?.today_triggers || 0}
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Today's Activity
              </div>
            </div>
          </div>
        </div>
        </div>
      </div>

      {/* Quick Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-2xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300"></div>
          <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">
              Automation Status
            </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Active</span>
              <span className="text-sm font-medium text-neutral-900 dark:text-white">
                {loading ? '...' : stats?.active_automations || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Total</span>
              <span className="text-sm font-medium text-neutral-900 dark:text-white">
                {loading ? '...' : stats?.total_automations || 0}
              </span>
            </div>
          </div>
          </div>
        </div>

        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300"></div>
          <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">
              Engagement
            </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                Avg. per day
              </span>
              <span className="text-sm font-medium text-neutral-900 dark:text-white">
                {loading
                  ? '...'
                  : Math.round(
                      (stats?.total_triggers || 0) /
                        (period === '7d' ? 7 : period === '30d' ? 30 : 90)
                    ) || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                Today's triggers
              </span>
              <span className="text-sm font-medium text-neutral-900 dark:text-white">
                {loading ? '...' : stats?.today_triggers || 0}
              </span>
            </div>
          </div>
          </div>
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 rounded-2xl p-6 border border-blue-100 dark:border-blue-900/50">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-2">
          About Your Analytics
        </h3>
        <p className="text-neutral-700 dark:text-neutral-300">
          Analytics data updates every hour. Track how your automations perform over time and
          optimize your messaging strategy for better engagement. Your success rate indicates
          how many messages were successfully delivered to recipients.
        </p>
      </div>
    </div>
  );
};

// Metric Card Component
interface MetricCardProps {
  label: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  iconBgColor: string;
  iconColor: string;
}

const MetricCard = ({
  label,
  value,
  subtitle,
  icon,
  iconBgColor,
  iconColor,
}: MetricCardProps) => {
  return (
    <div className="group relative">
      {/* 3D floating shadow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-neutral-500/10 to-neutral-500/5 rounded-2xl blur-lg transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300"></div>

      <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
        <div className={`inline-flex p-3 rounded-xl ${iconBgColor} ${iconColor} mb-4 group-hover:scale-110 transition-transform`}>
          {icon}
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">{label}</p>
          <p className="text-3xl font-semibold text-neutral-900 dark:text-white">{value}</p>
          <p className="text-xs text-neutral-500">{subtitle}</p>
        </div>
      </div>
    </div>
  );
};
