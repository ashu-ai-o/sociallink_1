// ============================================================================
// ANALYTICS PAGE - Performance metrics + Instagram profile stats
// ============================================================================

import { useState, useEffect } from 'react';
import {
  TrendingUp,
  MessageCircle,
  Send,
  Zap,
  Users,
  Image,
  RefreshCw,
  Instagram,
} from 'lucide-react';
import { api } from '../../utils/api';

interface ProfileStats {
  username: string;
  profile_picture_url: string;
  followers_count: number;
  following_count: number;
  media_count: number;
  last_synced: string;
}

interface IgAccount {
  id: string;
  username: string;
  profile_picture_url: string;
  followers_count: number;
  media_count: number;
  is_active: boolean;
}

export const AnalyticsPage = () => {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  /* Instagram accounts */
  const [igAccounts, setIgAccounts] = useState<IgAccount[]>([]);
  const [profileStats, setProfileStats] = useState<ProfileStats | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileRefreshing, setProfileRefreshing] = useState(false);

  /* Derived */
  const firstAccount: IgAccount | undefined =
    igAccounts.find((a) => a.is_active) ?? igAccounts[0];

  useEffect(() => {
    loadAnalytics();
    loadIgAccounts();
  }, []);

  useEffect(() => {
    loadAnalytics();
  }, [period]);

  const loadIgAccounts = async () => {
    try {
      const data = await api.getInstagramAccounts();
      const accounts: IgAccount[] = Array.isArray(data) ? data : data.results || [];
      setIgAccounts(accounts);
      const first = accounts.find((a) => a.is_active) ?? accounts[0];
      if (first) loadProfileStats(first.id, false);
    } catch (err) {
      console.error('Failed to load Instagram accounts:', err);
    }
  };

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

  const loadProfileStats = async (accountId: string, live: boolean) => {
    if (live) setProfileRefreshing(true);
    else setProfileLoading(true);
    try {
      const data = await api.getInstagramProfileStats(accountId);
      setProfileStats(data);
    } catch (error) {
      console.error('Failed to load profile stats:', error);
    } finally {
      setProfileLoading(false);
      setProfileRefreshing(false);
    }
  };

  const periodLabels = { '7d': 'Last 7 days', '30d': 'Last 30 days', '90d': 'Last 90 days' };

  const fmt = (n?: number) =>
    n == null
      ? '—'
      : n >= 1_000_000
        ? `${(n / 1_000_000).toFixed(1)}M`
        : n >= 1_000
          ? `${(n / 1_000).toFixed(1)}K`
          : n.toLocaleString();

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white">Analytics</h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            Track your automation performance and Instagram profile stats
          </p>
        </div>

        <div className="flex gap-2 bg-neutral-100 dark:bg-neutral-900 rounded-lg p-1">
          {(['7d', '30d', '90d'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${period === p
                ? 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white shadow-sm'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
                }`}
            >
              {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      <div className="text-sm text-neutral-600 dark:text-neutral-400">
        Showing data for {periodLabels[period]}
      </div>

      {/* ── Instagram Profile Stats ──────────────────────────────────────────── */}
      {firstAccount && (
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-br from-pink-500/10 to-purple-500/10 rounded-2xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300" />
          <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">

            {/* Card header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                {(profileStats?.profile_picture_url || firstAccount.profile_picture_url) ? (
                  <img
                    src={profileStats?.profile_picture_url || firstAccount.profile_picture_url}
                    alt={profileStats?.username || firstAccount.username}
                    className="w-10 h-10 rounded-full object-cover ring-2 ring-pink-300 dark:ring-pink-700"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center">
                    <Instagram className="w-5 h-5 text-white" />
                  </div>
                )}
                <div>
                  <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                    @{profileStats?.username || firstAccount.username}
                  </h2>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">Instagram Profile</p>
                </div>
              </div>

              <button
                onClick={() => loadProfileStats(firstAccount.id, true)}
                disabled={profileRefreshing}
                title="Refresh live stats from Instagram"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${profileRefreshing ? 'animate-spin' : ''}`} />
                {profileRefreshing ? 'Refreshing…' : 'Refresh'}
              </button>
            </div>

            {/* Stats grid */}
            {profileLoading ? (
              <div className="grid grid-cols-3 gap-4">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-24 bg-neutral-100 dark:bg-neutral-800 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Followers */}
                <div className="p-5 bg-gradient-to-br from-pink-50 to-rose-50 dark:from-pink-950/30 dark:to-rose-950/30 rounded-xl border border-pink-100 dark:border-pink-900/40">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="p-1.5 bg-pink-100 dark:bg-pink-900/40 rounded-lg">
                      <Users className="w-4 h-4 text-pink-600 dark:text-pink-400" />
                    </div>
                    <span className="text-xs font-medium text-pink-700 dark:text-pink-300 uppercase tracking-wide">
                      Followers
                    </span>
                  </div>
                  <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                    {fmt(profileStats?.followers_count ?? firstAccount.followers_count)}
                  </p>
                </div>

                {/* Posts */}
                <div className="p-5 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 rounded-xl border border-amber-100 dark:border-amber-900/40">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="p-1.5 bg-amber-100 dark:bg-amber-900/40 rounded-lg">
                      <Image className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                    </div>
                    <span className="text-xs font-medium text-amber-700 dark:text-amber-300 uppercase tracking-wide">
                      Posts
                    </span>
                  </div>
                  <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                    {fmt(profileStats?.media_count ?? firstAccount.media_count)}
                  </p>
                </div>
              </div>
            )}

            {profileStats?.last_synced && (
              <p className="text-xs text-neutral-400 mt-4">
                Last synced: {new Date(profileStats.last_synced).toLocaleString()}
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── Key Metrics Grid ─────────────────────────────────────────────────── */}
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

      {/* ── Performance Overview ─────────────────────────────────────────────── */}
      <div className="group relative">
        <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-2xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300" />
        <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-6">Performance Overview</h2>

          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Delivery Success Rate</span>
                <span className="text-lg font-semibold text-neutral-900 dark:text-white">
                  {loading ? '...' : `${Math.round(stats?.success_rate || 0)}%`}
                </span>
              </div>
              <div className="w-full h-3 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${stats?.success_rate || 0}%` }}
                />
              </div>
              <p className="text-xs text-neutral-500 mt-2">Messages delivered successfully to recipients</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-neutral-200 dark:border-neutral-800">
              <div>
                <div className="text-2xl font-semibold text-neutral-900 dark:text-white">
                  {loading ? '...' : stats?.total_dms_sent || 0}
                </div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">Total DMs Sent</div>
              </div>
              <div>
                <div className="text-2xl font-semibold text-neutral-900 dark:text-white">
                  {loading ? '...' : stats?.total_triggers || 0}
                </div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">Comments Triggered</div>
              </div>
              <div>
                <div className="text-2xl font-semibold text-neutral-900 dark:text-white">
                  {loading ? '...' : stats?.today_triggers || 0}
                </div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">Today's Activity</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Quick Insights ───────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-2xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300" />
          <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">Automation Status</h3>
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
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300" />
          <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">Engagement</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-600 dark:text-neutral-400">Avg. per day</span>
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
                <span className="text-sm text-neutral-600 dark:text-neutral-400">Today's triggers</span>
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
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-2">About Your Analytics</h3>
        <p className="text-neutral-700 dark:text-neutral-300">
          Analytics data updates every hour. Instagram profile stats (followers, following, posts) are fetched live
          from the Graph API when you click Refresh, and cached for quick loading.
        </p>
      </div>
    </div>
  );
};

// ─── Metric Card ─────────────────────────────────────────────────────────────
interface MetricCardProps {
  label: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  iconBgColor: string;
  iconColor: string;
}

const MetricCard = ({ label, value, subtitle, icon, iconBgColor, iconColor }: MetricCardProps) => (
  <div className="group relative">
    <div className="absolute inset-0 bg-gradient-to-br from-neutral-500/10 to-neutral-500/5 rounded-2xl blur-lg transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300" />
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
