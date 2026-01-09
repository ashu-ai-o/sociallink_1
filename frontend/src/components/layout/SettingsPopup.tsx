// ============================================================================
// COMPLETE SETTINGS PAGE WITH INSTAGRAM OAUTH
// ============================================================================

// FILE: src/components/Layout/SettingsPopup.tsx

import React, { useState, useEffect } from 'react';
import { X, User, Instagram, Sparkles, Bell, Shield, CreditCard, Check, AlertCircle, Loader2, Trash2, RefreshCw } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { closeSettings, setSettingsTab } from '../../store/slices/uiSlice';
import { api } from '../../utils/api';
import toast from 'react-hot-toast';

interface InstagramAccount {
  id: string;
  username: string;
  instagram_user_id: string;
  profile_picture_url: string;
  followers_count: number;
  is_active: boolean;
  last_synced: string;
  created_at: string;
}

export const SettingsPopup: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isOpen, activeTab } = useAppSelector((state) => state.ui.settings);
  const { user } = useAppSelector((state) => state.auth);

  const [loading, setLoading] = useState(false);
  const [instagramAccounts, setInstagramAccounts] = useState<InstagramAccount[]>([]);
  const [aiProviders, setAIProviders] = useState<any>(null);

  // Form states
  const [profileData, setProfileData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    first_name: '',
    last_name: '',
  });

  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  const tabs = [
    { id: 'general', label: 'General', icon: User },
    { id: 'instagram', label: 'Instagram', icon: Instagram },
    { id: 'ai', label: 'AI Providers', icon: Sparkles },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'billing', label: 'Billing', icon: CreditCard },
  ];

  useEffect(() => {
    if (isOpen && activeTab === 'instagram') {
      fetchInstagramAccounts();
    }
    if (isOpen && activeTab === 'ai') {
      fetchAIProviders();
    }
  }, [isOpen, activeTab]);

  const fetchInstagramAccounts = async () => {
    try {
      setLoading(true);
      const data = await api.getInstagramAccounts();
      setInstagramAccounts(data.results || data);
    } catch (error) {
      toast.error('Failed to fetch Instagram accounts');
    } finally {
      setLoading(false);
    }
  };

  const fetchAIProviders = async () => {
    try {
      setLoading(true);
      const data = await api.getAIProviders();
      setAIProviders(data);
    } catch (error) {
      toast.error('Failed to fetch AI providers');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // INSTAGRAM OAUTH HANDLER
  // ============================================================================
  
  const handleConnectInstagram = () => {
    // Open OAuth popup
    const width = 600;
    const height = 700;
    const left = window.screen.width / 2 - width / 2;
    const top = window.screen.height / 2 - height / 2;

    const popup = window.open(
      `${import.meta.env.VITE_API_URL}/auth/instagram/oauth/`,
      'Instagram OAuth',
      `width=${width},height=${height},left=${left},top=${top}`
    );

    // Listen for OAuth completion
    const checkPopup = setInterval(() => {
      if (!popup || popup.closed) {
        clearInterval(checkPopup);
        fetchInstagramAccounts(); // Refresh list
      }
    }, 500);
  };

  const handleDisconnectInstagram = async (accountId: string) => {
    if (!confirm('Are you sure you want to disconnect this Instagram account?')) {
      return;
    }

    try {
      await api.disconnectInstagramAccount(accountId);
      toast.success('Instagram account disconnected');
      fetchInstagramAccounts();
    } catch (error) {
      toast.error('Failed to disconnect account');
    }
  };

  const handleRefreshAccount = async (accountId: string) => {
    try {
      setLoading(true);
      // Call refresh endpoint
      await api.client.post(`/instagram-accounts/${accountId}/refresh_stats/`);
      toast.success('Account refreshed');
      fetchInstagramAccounts();
    } catch (error) {
      toast.error('Failed to refresh account');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // PROFILE UPDATE
  // ============================================================================

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await api.client.patch('/auth/profile/', profileData);
      toast.success('Profile updated successfully');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // PASSWORD CHANGE
  // ============================================================================

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }

    try {
      setLoading(true);
      await api.client.post('/auth/change-password/', {
        old_password: passwordData.old_password,
        new_password: passwordData.new_password,
        new_password_confirm: passwordData.confirm_password,
      });
      toast.success('Password changed successfully');
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (error: any) {
      toast.error(error.response?.data?.old_password?.[0] || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity"
        onClick={() => dispatch(closeSettings())}
      />

      {/* Popup */}
      <div className="absolute right-0 top-0 h-full w-full max-w-2xl bg-white dark:bg-gray-900 shadow-2xl transform transition-transform duration-300 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h2>
          <button
            onClick={() => dispatch(closeSettings())}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar Tabs */}
          <div className="w-48 border-r border-gray-200 dark:border-gray-800 p-4">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => dispatch(setSettingsTab(tab.id))}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'general' && (
              <GeneralTab
                profileData={profileData}
                setProfileData={setProfileData}
                onSubmit={handleUpdateProfile}
                loading={loading}
                user={user}
              />
            )}

            {activeTab === 'instagram' && (
              <InstagramTab
                accounts={instagramAccounts}
                loading={loading}
                onConnect={handleConnectInstagram}
                onDisconnect={handleDisconnectInstagram}
                onRefresh={handleRefreshAccount}
              />
            )}

            {activeTab === 'ai' && (
              <AIProvidersTab providers={aiProviders} loading={loading} />
            )}

            {activeTab === 'notifications' && <NotificationsTab />}

            {activeTab === 'security' && (
              <SecurityTab
                passwordData={passwordData}
                setPasswordData={setPasswordData}
                onSubmit={handleChangePassword}
                loading={loading}
              />
            )}

            {activeTab === 'billing' && <BillingTab user={user} />}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// GENERAL TAB
// ============================================================================

const GeneralTab: React.FC<any> = ({ profileData, setProfileData, onSubmit, loading, user }) => (
  <div>
    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">General Settings</h3>
    
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            First Name
          </label>
          <input
            type="text"
            value={profileData.first_name}
            onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Last Name
          </label>
          <input
            type="text"
            value={profileData.last_name}
            onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Username
        </label>
        <input
          type="text"
          value={profileData.username}
          onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Email
        </label>
        <input
          type="email"
          value={profileData.email}
          disabled
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-500 cursor-not-allowed"
        />
        <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading && <Loader2 className="w-5 h-5 animate-spin" />}
        Save Changes
      </button>
    </form>
  </div>
);

// ============================================================================
// INSTAGRAM TAB WITH OAUTH
// ============================================================================

const InstagramTab: React.FC<any> = ({ accounts, loading, onConnect, onDisconnect, onRefresh }) => (
  <div>
    <div className="flex items-center justify-between mb-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">Instagram Accounts</h3>
      <button
        onClick={onConnect}
        className="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors flex items-center gap-2"
      >
        <Instagram className="w-5 h-5" />
        Connect Account
      </button>
    </div>

    {/* Info Box */}
    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
      <div className="flex gap-3">
        <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800 dark:text-blue-200">
          <p className="font-medium mb-1">Requirements:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Instagram account must be Business or Creator</li>
            <li>Account must be linked to a Facebook Page</li>
            <li>You'll need to grant permissions for DMs and comments</li>
          </ul>
        </div>
      </div>
    </div>

    {/* Loading State */}
    {loading && accounts.length === 0 && (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    )}

    {/* Empty State */}
    {!loading && accounts.length === 0 && (
      <div className="text-center py-12">
        <Instagram className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No Instagram Accounts Connected
        </h4>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Connect your Instagram account to start automating DMs
        </p>
        <button
          onClick={onConnect}
          className="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors inline-flex items-center gap-2"
        >
          <Instagram className="w-5 h-5" />
          Connect Your First Account
        </button>
      </div>
    )}

    {/* Connected Accounts */}
    {accounts.length > 0 && (
      <div className="space-y-4">
        {accounts.map((account: InstagramAccount) => (
          <div
            key={account.id}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                {/* Profile Picture */}
                {account.profile_picture_url ? (
                  <img
                    src={account.profile_picture_url}
                    alt={account.username}
                    className="w-16 h-16 rounded-full"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                    <Instagram className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                  </div>
                )}

                {/* Account Info */}
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                      @{account.username}
                    </h4>
                    {account.is_active && (
                      <span className="px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-xs font-medium rounded-full flex items-center gap-1">
                        <Check className="w-3 h-3" />
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {account.followers_count.toLocaleString()} followers
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Connected {new Date(account.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onRefresh(account.id)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="Refresh"
                >
                  <RefreshCw className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </button>
                <button
                  onClick={() => onDisconnect(account.id)}
                  className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  title="Disconnect"
                >
                  <Trash2 className="w-5 h-5 text-red-600 dark:text-red-400" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);

// ============================================================================
// AI PROVIDERS TAB
// ============================================================================

const AIProvidersTab: React.FC<any> = ({ providers, loading }) => (
  <div>
    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">AI Providers</h3>

    {loading && (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    )}

    {!loading && providers && (
      <div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <Sparkles className="w-6 h-6 text-purple-600" />
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
              {providers.provider || 'OpenRouter'}
            </h4>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600 dark:text-gray-400">Models Available</p>
              <p className="font-semibold text-gray-900 dark:text-white">
                {providers.models_configured || 0}
              </p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Status</p>
              <p className="font-semibold text-green-600 dark:text-green-400">Active</p>
            </div>
          </div>
        </div>

        {/* Models List */}
        {providers.models && providers.models.length > 0 && (
          <div>
            <h5 className="font-medium text-gray-900 dark:text-white mb-4">Available Models</h5>
            <div className="space-y-3">
              {providers.models.map((model: any, index: number) => (
                <div
                  key={index}
                  className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h6 className="font-medium text-gray-900 dark:text-white">{model.name}</h6>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{model.id}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-gray-600 dark:text-gray-400 capitalize">
                        {model.speed} • {model.cost} cost
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )}
  </div>
);

// ============================================================================
// NOTIFICATIONS TAB
// ============================================================================

const NotificationsTab: React.FC = () => {
  const [settings, setSettings] = useState({
    email_notifications: true,
    automation_alerts: true,
    weekly_report: false,
    dm_alerts: true,
  });

  return (
    <div>
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Notifications</h3>
      
      <div className="space-y-4">
        {Object.entries(settings).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-800">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white capitalize">
                {key.replace(/_/g, ' ')}
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Get notified about {key.replace(/_/g, ' ').toLowerCase()}
              </p>
            </div>
            <button
              onClick={() => setSettings({ ...settings, [key]: !value })}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                value ? 'bg-purple-600' : 'bg-gray-300 dark:bg-gray-700'
              }`}
            >
              <div
                className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  value ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// SECURITY TAB
// ============================================================================

const SecurityTab: React.FC<any> = ({ passwordData, setPasswordData, onSubmit, loading }) => (
  <div>
    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Security</h3>
    
    <form onSubmit={onSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Current Password
        </label>
        <input
          type="password"
          value={passwordData.old_password}
          onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          New Password
        </label>
        <input
          type="password"
          value={passwordData.new_password}
          onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Confirm New Password
        </label>
        <input
          type="password"
          value={passwordData.confirm_password}
          onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
          required
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading && <Loader2 className="w-5 h-5 animate-spin" />}
        Change Password
      </button>
    </form>
  </div>
);

// ============================================================================
// BILLING TAB
// ============================================================================

const BillingTab: React.FC<any> = ({ user }) => (
  <div>
    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Billing & Plan</h3>
    
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
            {user?.plan || 'Free'} Plan
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {user?.plan === 'free' && 'Limited features'}
            {user?.plan === 'pro' && 'All features unlocked'}
            {user?.plan === 'enterprise' && 'Unlimited everything'}
          </p>
        </div>
        {user?.plan === 'free' && (
          <button className="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors">
            Upgrade to Pro
          </button>
        )}
      </div>
    </div>

    {/* Usage Stats */}
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">DMs This Month</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {user?.plan === 'free' ? '450 / 1,000' : 'Unlimited'}
        </p>
      </div>
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">Automations</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {user?.plan === 'free' ? '3 / 5' : 'Unlimited'}
        </p>
      </div>
    </div>
  </div>
);

export default SettingsPopup;