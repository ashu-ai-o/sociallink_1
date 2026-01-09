// ============================================================================
// DASHBOARD PAGE - Real-time stats and overview
// ============================================================================

// src/pages/Dashboard/DashboardPage.tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  TrendingUp, 
  Zap, 
  Send, 
  Activity, 
  Plus,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  AlertCircle
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
      const dashboardData = await api.getDashboardStats('30d');
      setStats(dashboardData);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const recentAutomations = automations.slice(0, 5);

  return (
    <div className="space-y-6 slide-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">
            Dashboard
          </h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Welcome back! Here's what's happening with your automations.
          </p>
        </div>
        <Link to="/automations/create" className="btn btn-primary">
          <Plus className="w-4 h-4" />
          New Automation
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<Zap className="w-6 h-6" />}
          label="Active Automations"
          value={stats.active_automations}
          total={stats.total_automations}
          color="purple"
          loading={loading}
        />

        <StatCard
          icon={<Send className="w-6 h-6" />}
          label="Total DMs Sent"
          value={stats.total_dms_sent}
          change="+12% vs last month"
          color="blue"
          loading={loading}
        />

        <StatCard
          icon={<Activity className="w-6 h-6" />}
          label="Total Triggers"
          value={stats.total_triggers}
          color="green"
          loading={loading}
        />

        <StatCard
          icon={<TrendingUp className="w-6 h-6" />}
          label="Today's Activity"
          value={stats.today_triggers}
          subtitle="triggers"
          color="orange"
          loading={loading}
        />
      </div>

      {/* Recent Automations & Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Automations */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                Recent Automations
              </h2>
              <Link
                to="/automations"
                className="text-sm text-[var(--accent-primary)] hover:underline flex items-center gap-1"
              >
                View All
                <ArrowUpRight className="w-4 h-4" />
              </Link>
            </div>

            {loading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-16 bg-[var(--bg-secondary)] rounded-lg"></div>
                  </div>
                ))}
              </div>
            ) : recentAutomations.length > 0 ? (
              <div className="space-y-3">
                {recentAutomations.map((automation) => (
                  <Link
                    key={automation.id}
                    to={`/automations/${automation.id}/edit`}
                    className="block p-4 rounded-lg border border-[var(--border-primary)] hover:bg-[var(--bg-hover)] transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-medium text-[var(--text-primary)]">
                            {automation.name}
                          </h3>
                          {automation.is_active ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                              <div className="w-1.5 h-1.5 rounded-full bg-green-600 dark:bg-green-400"></div>
                              Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                              <div className="w-1.5 h-1.5 rounded-full bg-gray-400"></div>
                              Inactive
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-[var(--text-secondary)]">
                          <span>{automation.total_triggers} triggers</span>
                          <span>•</span>
                          <span>{automation.total_dms_sent} DMs sent</span>
                          {automation.total_comment_replies > 0 && (
                            <>
                              <span>•</span>
                              <span>{automation.total_comment_replies} replies</span>
                            </>
                          )}
                        </div>
                      </div>
                      <ArrowUpRight className="w-5 h-5 text-[var(--text-tertiary)]" />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Zap className="w-12 h-12 text-[var(--text-tertiary)] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">
                  No automations yet
                </h3>
                <p className="text-[var(--text-secondary)] mb-4">
                  Create your first automation to get started
                </p>
                <Link to="/automations/create" className="btn btn-primary">
                  <Plus className="w-4 h-4" />
                  Create Automation
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="space-y-6">
          {/* Success Rate */}
          <div className="card">
            <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-4">
              Success Rate
            </h3>
            <div className="text-4xl font-bold text-[var(--text-primary)] mb-2">
              {loading ? '...' : `${Math.round(stats.success_rate)}%`}
            </div>
            <p className="text-sm text-[var(--text-secondary)]">
              DMs delivered successfully
            </p>
            <div className="mt-4 w-full h-2 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--accent-primary)] transition-all duration-500"
                style={{ width: `${stats.success_rate}%` }}
              ></div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-4">
              Quick Actions
            </h3>
            <div className="space-y-2">
              <Link
                to="/automations/create"
                className="block p-3 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[var(--accent-light)] text-[var(--accent-primary)]">
                    <Plus className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    New Automation
                  </span>
                </div>
              </Link>
              <Link
                to="/analytics"
                className="block p-3 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    View Analytics
                  </span>
                </div>
              </Link>
              <Link
                to="/contacts"
                className="block p-3 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                    <Activity className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    View Contacts
                  </span>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-6">
          Recent Activity
        </h2>
        <div className="space-y-4">
          <ActivityItem
            icon={<CheckCircle2 className="w-5 h-5 text-green-600" />}
            title="DM sent successfully"
            description="@username received your automated message"
            time="2 minutes ago"
          />
          <ActivityItem
            icon={<Zap className="w-5 h-5 text-purple-600" />}
            title="Automation triggered"
            description="New comment detected on your post"
            time="5 minutes ago"
          />
          <ActivityItem
            icon={<CheckCircle2 className="w-5 h-5 text-green-600" />}
            title="Comment reply sent"
            description="Public reply posted successfully"
            time="8 minutes ago"
          />
          <ActivityItem
            icon={<Clock className="w-5 h-5 text-blue-600" />}
            title="Automation paused"
            description="Rate limit reached, waiting 5 minutes"
            time="12 minutes ago"
          />
        </div>
      </div>
    </div>
  );
};

// Helper Components
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  total?: number;
  subtitle?: string;
  change?: string;
  color: 'purple' | 'blue' | 'green' | 'orange';
  loading?: boolean;
}

const StatCard = ({
  icon,
  label,
  value,
  total,
  subtitle,
  change,
  color,
  loading,
}: StatCardProps) => {
  const colorClasses = {
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
  };

  return (
    <div className="card card-hover">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>{icon}</div>
      </div>
      <p className="text-sm text-[var(--text-secondary)] mb-1">{label}</p>
      {loading ? (
        <div className="h-9 w-24 bg-[var(--bg-secondary)] rounded animate-pulse"></div>
      ) : (
        <>
          <p className="text-3xl font-bold text-[var(--text-primary)]">
            {value.toLocaleString()}
            {subtitle && (
              <span className="text-lg font-normal text-[var(--text-secondary)] ml-2">
                {subtitle}
              </span>
            )}
          </p>
          {total !== undefined && (
            <p className="text-sm text-[var(--text-tertiary)] mt-1">
              of {total.toLocaleString()}
            </p>
          )}
          {change && (
            <p className="text-sm text-green-600 dark:text-green-400 mt-1">
              {change}
            </p>
          )}
        </>
      )}
    </div>
  );
};

interface ActivityItemProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  time: string;
}

const ActivityItem = ({ icon, title, description, time }: ActivityItemProps) => (
  <div className="flex items-start gap-4 p-3 rounded-lg hover:bg-[var(--bg-hover)] transition-colors">
    <div className="p-2 rounded-lg bg-[var(--bg-secondary)]">{icon}</div>
    <div className="flex-1 min-w-0">
      <p className="font-medium text-[var(--text-primary)]">{title}</p>
      <p className="text-sm text-[var(--text-secondary)] truncate">{description}</p>
    </div>
    <p className="text-xs text-[var(--text-tertiary)] whitespace-nowrap">{time}</p>
  </div>
);