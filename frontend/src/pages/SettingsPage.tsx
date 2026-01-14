import React, { useEffect, useState } from 'react';
import { Settings, Sparkles, Bell, Shield, CreditCard, Instagram, RefreshCw, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';

interface InstagramAccount {
  id: string;
  username: string;
  instagram_user_id: string;
  followers_count: number;
  profile_picture_url?: string;
  is_active: boolean;
  token_expires_at: string;
}

export const SettingsPage: React.FC = () => {
  const [accounts, setAccounts] = useState<InstagramAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState<string | null>(null);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const data = await api.getInstagramAccounts();
      setAccounts(data.results || data || []);
    } catch (error) {
      console.error('Failed to load accounts:', error);
      toast.error('Failed to load Instagram accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectInstagram = () => {
    // Redirect to OAuth flow
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/instagram/oauth/`;
  };

  const handleRefreshStats = async (accountId: string) => {
    try {
      setRefreshing(accountId);
      await api.refreshInstagramStats(accountId);
      await loadAccounts();
      toast.success('Stats refreshed successfully');
    } catch (error) {
      toast.error('Failed to refresh stats');
    } finally {
      setRefreshing(null);
    }
  };

  const handleDisconnect = async (accountId: string, username: string) => {
    if (confirm(`Are you sure you want to disconnect @${username}?`)) {
      try {
        await api.disconnectInstagram(accountId);
        await loadAccounts();
        toast.success('Account disconnected');
      } catch (error) {
        toast.error('Failed to disconnect account');
      }
    }
  };

  const isTokenExpiringSoon = (expiresAt: string) => {
    const daysUntilExpiry = Math.ceil(
      (new Date(expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    );
    return daysUntilExpiry < 7;
  };

  return (
    <div className="space-y-6 slide-in-up">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--text-primary)]">Settings</h1>
        <p className="text-[var(--text-secondary)] mt-1">
          Manage your Instagram accounts and platform preferences
        </p>
      </div>

      {/* Instagram Accounts Section */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Connected Instagram Accounts
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Manage your Instagram Business accounts for automation
            </p>
          </div>
          <button onClick={handleConnectInstagram} className="btn btn-primary">
            <Instagram className="w-4 h-4" />
            Connect Account
          </button>
        </div>

        {/* Important Info Banner */}
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
            <div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-1">
                Instagram Business Account Required
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                To use LinkPlease automations, you need an Instagram Business or Creator account
                connected to a Facebook Page. Personal accounts won't work due to Instagram API limitations.
              </p>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-24 bg-[var(--bg-secondary)] rounded-lg"></div>
              </div>
            ))}
          </div>
        ) : accounts.length > 0 ? (
          <div className="space-y-4">
            {accounts.map((account) => (
              <div
                key={account.id}
                className="flex items-center justify-between p-4 border border-[var(--border-primary)] rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
              >
                <div className="flex items-center gap-4">
                  {account.profile_picture_url ? (
                    <img
                      src={account.profile_picture_url}
                      alt={account.username}
                      className="w-12 h-12 rounded-full"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                      {account.username[0].toUpperCase()}
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-[var(--text-primary)]">
                        @{account.username}
                      </h3>
                      {account.is_active ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                          <CheckCircle2 className="w-3 h-3" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                          Disconnected
                        </span>
                      )}
                      {isTokenExpiringSoon(account.token_expires_at) && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400">
                          <AlertCircle className="w-3 h-3" />
                          Token Expiring Soon
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {account.followers_count.toLocaleString()} followers
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRefreshStats(account.id)}
                    disabled={refreshing === account.id}
                    className="btn btn-secondary text-sm"
                    title="Refresh stats"
                  >
                    <RefreshCw
                      className={`w-4 h-4 ${refreshing === account.id ? 'animate-spin' : ''}`}
                    />
                  </button>
                  <button
                    onClick={() => handleDisconnect(account.id, account.username)}
                    className="btn btn-secondary text-sm text-[var(--error)]"
                    title="Disconnect account"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Instagram className="w-16 h-16 text-[var(--text-tertiary)] mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
              No Instagram Accounts Connected
            </h3>
            <p className="text-[var(--text-secondary)] mb-6 max-w-md mx-auto">
              Connect your Instagram Business account to start automating DMs and growing your business
            </p>
            <button onClick={handleConnectInstagram} className="btn btn-primary">
              <Instagram className="w-4 h-4" />
              Connect Your First Account
            </button>
          </div>
        )}
      </div>

      {/* How it Works Section */}
      <div className="card">
        <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
          How Instagram Connection Works
        </h2>
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
              1
            </div>
            <div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-1">
                Connect via Facebook
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                Instagram requires authentication through Facebook. We'll redirect you to Facebook's secure OAuth flow.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
              2
            </div>
            <div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-1">
                Grant Permissions
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                We only request the minimum permissions needed: send messages, manage comments, and read basic profile info.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
              3
            </div>
            <div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-1">
                Start Automating
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                Once connected, you can create automations that monitor your posts and automatically engage with comments.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
