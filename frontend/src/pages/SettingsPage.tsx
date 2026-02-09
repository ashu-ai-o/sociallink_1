import React, { useEffect, useState } from 'react';
import { Instagram, RefreshCw, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';
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
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white">Settings</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mt-1">
          Manage your Instagram accounts and automation preferences
        </p>
      </div>

      {/* Instagram Accounts Section */}
      <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
              Instagram Accounts
            </h2>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
              Connect your Instagram Business accounts
            </p>
          </div>
          <button onClick={handleConnectInstagram} className="inline-flex items-center gap-2 px-4 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all hover:scale-[1.02] active:scale-[0.98]">
            <Instagram className="w-4 h-4" />
            Connect Account
          </button>
        </div>

        {/* Info Banner */}
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-xl">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">
                Business Account Required
              </h3>
              <p className="text-sm text-neutral-700 dark:text-neutral-300">
                You need an Instagram Business or Creator account connected to a Facebook Page.
                Personal accounts won't work due to Instagram API limitations.
              </p>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-24 bg-neutral-200 dark:bg-neutral-800 rounded-xl"></div>
              </div>
            ))}
          </div>
        ) : accounts.length > 0 ? (
          <div className="space-y-4">
            {accounts.map((account) => (
              <div key={account.id} className="group relative">
                {/* 3D floating shadow effect */}
                <div className={`absolute inset-0 bg-gradient-to-br ${
                  account.is_active
                    ? 'from-green-500/15 to-emerald-500/15'
                    : 'from-neutral-500/10 to-neutral-500/5'
                } rounded-xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300`}></div>

                <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1"
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
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <h3 className="font-semibold text-neutral-900 dark:text-white">
                        @{account.username}
                      </h3>
                      {account.is_active ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                          <CheckCircle2 className="w-3 h-3" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400">
                          Disconnected
                        </span>
                      )}
                      {isTokenExpiringSoon(account.token_expires_at) && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                          <AlertCircle className="w-3 h-3" />
                          Expires Soon
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      {account.followers_count.toLocaleString()} followers
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRefreshStats(account.id)}
                    disabled={refreshing === account.id}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg text-sm font-medium hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
                    title="Refresh stats"
                  >
                    <RefreshCw
                      className={`w-4 h-4 ${refreshing === account.id ? 'animate-spin' : ''}`}
                    />
                  </button>
                  <button
                    onClick={() => handleDisconnect(account.id, account.username)}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                    title="Disconnect account"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Instagram className="w-16 h-16 text-neutral-300 dark:text-neutral-700 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 dark:text-white mb-2">
              No Accounts Connected
            </h3>
            <p className="text-neutral-600 dark:text-neutral-400 mb-6 max-w-md mx-auto">
              Connect your Instagram Business account to start automating DMs
            </p>
            <button onClick={handleConnectInstagram} className="inline-flex items-center gap-2 px-5 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all hover:scale-[1.02] active:scale-[0.98]">
              <Instagram className="w-4 h-4" />
              Connect Your First Account
            </button>
          </div>
        )}
      </div>

      {/* How it Works */}
      <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
        <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-6">
          How Instagram Connection Works
        </h2>
        <div className="space-y-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white flex items-center justify-center font-bold text-sm">
              1
            </div>
            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">
                Connect via Facebook
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Instagram requires authentication through Facebook. We'll redirect you to Facebook's secure OAuth flow.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white flex items-center justify-center font-bold text-sm">
              2
            </div>
            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">
                Grant Permissions
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                We only request the minimum permissions: send messages, manage comments, and read basic profile info.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white flex items-center justify-center font-bold text-sm">
              3
            </div>
            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">
                Start Automating
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Once connected, you can create automations that monitor your posts and automatically engage with comments.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
