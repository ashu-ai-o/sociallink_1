// ============================================================================
// DASHBOARD PAGE - Clean, spacious overview with ZapDM-inspired design
// ============================================================================

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  Zap,
  Send,
  MessageCircle,
  Plus,
  ArrowRight,
  Sparkles,
  Activity,
} from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { fetchAutomations } from '../../store/slices/automationsSlice';
import { api } from '../../utils/api';

interface Stats {
  total_automations: number;
  active_automations: number;
  total_dms_sent: number;
  total_triggers: number;
  today_triggers: number;
  success_rate: number;
}

export const DashboardPage = () => {
  const dispatch = useAppDispatch();
  const automations = useAppSelector((state) => state.automations.items);
  const user = useAppSelector((state) => state.auth.user);
  const [stats, setStats] = useState<Stats>({
    total_automations: 0,
    active_automations: 0,
    total_dms_sent: 0,
    total_triggers: 0,
    today_triggers: 0,
    success_rate: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await dispatch(fetchAutomations()).unwrap();
      const dashboardData = await api.getDashboardOverview('30d');
      setStats(dashboardData);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const recentAutomations = automations.slice(0, 3);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Section */}
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white">
          Welcome back{user?.username ? `, ${user.username}` : ''}
        </h1>
        <p className="text-neutral-600 dark:text-neutral-400">
          Here's what's happening with your automations today
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          label="Active Automations"
          value={loading ? '...' : stats.active_automations.toString()}
          subtitle={`${stats.total_automations} total`}
          iconBgColor="bg-neutral-100 dark:bg-neutral-800"
          iconColor="text-neutral-700 dark:text-neutral-300"
        />

        <StatCard
          icon={<Send className="w-5 h-5" />}
          label="Messages Sent"
          value={loading ? '...' : stats.total_dms_sent.toLocaleString()}
          subtitle="All time"
          iconBgColor="bg-blue-50 dark:bg-blue-900/20"
          iconColor="text-blue-600 dark:text-blue-400"
        />

        <StatCard
          icon={<MessageCircle className="w-5 h-5" />}
          label="Comments Processed"
          value={loading ? '...' : stats.total_triggers.toLocaleString()}
          subtitle="Total engagements"
          iconBgColor="bg-green-50 dark:bg-green-900/20"
          iconColor="text-green-600 dark:text-green-400"
        />

        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="Today's Activity"
          value={loading ? '...' : stats.today_triggers.toString()}
          subtitle="Interactions"
          iconBgColor="bg-amber-50 dark:bg-amber-900/20"
          iconColor="text-amber-600 dark:text-amber-400"
        />
      </div>

      {/* Quick Tip Card */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 rounded-2xl p-6 border border-blue-100 dark:border-blue-900/50">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-100 dark:bg-blue-900/50 rounded-xl">
            <Sparkles className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-2">
              Quick Tip
            </h3>
            <p className="text-neutral-700 dark:text-neutral-300 mb-4 leading-relaxed">
              {automations.length === 0
                ? 'Get started by creating your first automation. Set up triggers to automatically respond to comments and send personalized DMs to grow your Instagram engagement.'
                : 'Pro tip: Use specific trigger words in your automations to target the right audience. Generic responses get less engagement than personalized ones.'}
            </p>
            {automations.length === 0 && (
              <Link
                to="/automations/create"
                className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                <Plus className="w-4 h-4" />
                Create Your First Automation
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Recent Automations */}
      {automations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
              Recent Automations
            </h2>
            <Link
              to="/automations"
              className="text-sm font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white flex items-center gap-1 group"
            >
              View all
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          <div className="space-y-3">
            {loading ? (
              // Loading skeletons
              [...Array(3)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-neutral-900 rounded-xl p-6 border border-neutral-200 dark:border-neutral-800 animate-pulse">
                  <div className="h-5 bg-neutral-200 dark:bg-neutral-800 rounded w-1/3 mb-3"></div>
                  <div className="h-4 bg-neutral-200 dark:bg-neutral-800 rounded w-1/2"></div>
                </div>
              ))
            ) : recentAutomations.length > 0 ? (
              recentAutomations.map((automation) => (
                <Link
                  key={automation.id}
                  to={`/automations/${automation.id}/edit`}
                  className="block bg-white dark:bg-neutral-900 rounded-xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-soft-lg transition-all duration-200 hover:border-neutral-300 dark:hover:border-neutral-700 group"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-medium text-neutral-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {automation.name}
                    </h3>
                    <div className="flex items-center gap-2">
                      {automation.is_active ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-neutral-200 dark:border-neutral-700">
                          <span className="w-1.5 h-1.5 rounded-full bg-neutral-400"></span>
                          Inactive
                        </span>
                      )}
                      <ArrowRight className="w-5 h-5 text-neutral-400 group-hover:text-neutral-600 dark:group-hover:text-neutral-300 group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                  <div className="flex items-center gap-6 text-sm text-neutral-600 dark:text-neutral-400">
                    <div className="flex items-center gap-1.5">
                      <MessageCircle className="w-4 h-4" />
                      <span>{automation.total_triggers} triggers</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Send className="w-4 h-4" />
                      <span>{automation.total_dms_sent} DMs sent</span>
                    </div>
                    {automation.total_comment_replies > 0 && (
                      <div className="flex items-center gap-1.5">
                        <TrendingUp className="w-4 h-4" />
                        <span>{automation.total_comment_replies} replies</span>
                      </div>
                    )}
                  </div>
                </Link>
              ))
            ) : (
              <div className="bg-white dark:bg-neutral-900 rounded-xl p-12 border border-neutral-200 dark:border-neutral-800 text-center">
                <Zap className="w-12 h-12 text-neutral-300 dark:text-neutral-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-neutral-900 dark:text-white mb-2">
                  No automations yet
                </h3>
                <p className="text-neutral-600 dark:text-neutral-400 mb-6">
                  Create your first automation to start engaging with your audience
                </p>
                <Link
                  to="/automations/create"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Plus className="w-4 h-4" />
                  Create Automation
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Performance Overview */}
      {stats.success_rate > 0 && (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-6">
            Performance Overview
          </h2>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  Success Rate
                </span>
                <span className="text-2xl font-semibold text-neutral-900 dark:text-white">
                  {Math.round(stats.success_rate)}%
                </span>
              </div>
              <div className="w-full h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${stats.success_rate}%` }}
                ></div>
              </div>
              <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-2">
                Messages delivered successfully
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Stat Card Component
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtitle?: string;
  iconBgColor: string;
  iconColor: string;
}

const StatCard = ({
  icon,
  label,
  value,
  subtitle,
  iconBgColor,
  iconColor,
}: StatCardProps) => {
  return (
    <div className="bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-soft-lg transition-all duration-200">
      <div className={`inline-flex p-3 rounded-xl ${iconBgColor} ${iconColor} mb-4`}>
        {icon}
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
          {label}
        </p>
        <p className="text-3xl font-semibold text-neutral-900 dark:text-white">
          {value}
        </p>
        {subtitle && (
          <p className="text-xs text-neutral-500 dark:text-neutral-500">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
};
