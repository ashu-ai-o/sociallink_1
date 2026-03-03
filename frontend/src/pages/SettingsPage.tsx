import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Instagram, RefreshCw, Trash2, CheckCircle2, AlertCircle, User, Mail,
  Shield, Bell, Lock, LogOut, ChevronRight, Camera, KeyRound, MessageSquare
} from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';
import { TwoFactorSetup } from '../components/Security/TwoFactorSetup';
import { ActiveSessions } from '../components/Security/ActiveSessions';
import { DeleteAccountModal } from '../components/DeleteAccountModal';
import { ConfirmModal } from '../components/ConfirmModal';

interface InstagramAccount {
  id: string;
  username: string;
  instagram_user_id: string;
  followers_count: number;
  profile_picture_url?: string;
  is_active: boolean;
  token_expires_at: string;
}

interface UserProfile {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  phone: string;
  bio: string;
  profile_picture: string | null;
  is_email_verified: boolean;
}

type SettingsTab = 'instagram' | 'profile' | 'security' | 'account';

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('instagram');
  const [accounts, setAccounts] = useState<InstagramAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileForm, setProfileForm] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    bio: '',
  });
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [disconnectTarget, setDisconnectTarget] = useState<{ id: string; username: string } | null>(null);
  const [verificationLoading, setVerificationLoading] = useState(false);
  const [notifPreferences, setNotifPreferences] = useState({
    weekly_reports: true,
    automation_alerts: true,
    dm_failures: true,
    account_issues: true,
  });
  const [notifLoading, setNotifLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadAccounts();
    loadProfile();
    loadNotifPreferences();
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

  const loadProfile = async () => {
    try {
      const data = await api.getUserProfile();
      setProfile(data);
      setProfileForm({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        phone: data.phone || '',
        bio: data.bio || '',
      });
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const loadNotifPreferences = async () => {
    try {
      const response = await api.getNotificationPreferences();
      if (response?.preferences) {
        setNotifPreferences(prev => ({ ...prev, ...response.preferences }));
      } else if (response) {
        setNotifPreferences(prev => ({ ...prev, ...response }));
      }
    } catch (error) {
      console.error('Failed to load notification preferences:', error);
    }
  };

  const handleNotifToggle = async (key: string) => {
    const newPrefs = { ...notifPreferences, [key]: !(notifPreferences as any)[key] };
    setNotifPreferences(newPrefs);
    setNotifLoading(true);
    try {
      await api.updateNotificationPreferences(newPrefs);
    } catch (error) {
      console.error('Failed to update preference:', error);
      setNotifPreferences(notifPreferences);
      toast.error('Failed to update preference');
    } finally {
      setNotifLoading(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileLoading(true);
    try {
      const updated = await api.updateUserProfile(profileForm);
      setProfile(updated);
      toast.success('Profile updated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to update profile');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleResendVerification = async () => {
    setVerificationLoading(true);
    try {
      await api.resendVerificationEmail();
      toast.success('Verification email sent!');
    } catch (error) {
      toast.error('Failed to send verification email');
    } finally {
      setVerificationLoading(false);
    }
  };

  const handleConnectInstagram = async (method: 'facebook_graph' | 'instagram_platform' = 'facebook_graph') => {
    try {
      const response = method === 'instagram_platform'
        ? await api.client.get('/auth/instagram-direct/oauth/').then(res => res.data)
        : await api.initiateInstagramOAuth();

      const oauthUrl = response.oauth_url;
      if (!oauthUrl) {
        toast.error('Failed to get OAuth URL');
        return;
      }

      const width = 600;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;

      const popup = window.open(
        oauthUrl,
        'Instagram OAuth',
        `width=${width},height=${height},left=${left},top=${top}`
      );

      const handleMessage = (event: MessageEvent) => {
        if (event.data?.type === 'instagram_oauth') {
          window.removeEventListener('message', handleMessage);
          if (event.data.status === 'success') {
            toast.success('Instagram account connected!');
          } else {
            toast.error('Failed to connect Instagram');
          }
          loadAccounts();
        }
      };
      window.addEventListener('message', handleMessage);

      const checkPopup = setInterval(() => {
        if (!popup || popup.closed) {
          clearInterval(checkPopup);
          window.removeEventListener('message', handleMessage);
          loadAccounts();
        }
      }, 1000);
    } catch (error) {
      toast.error('Failed to start Instagram connection');
    }
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

  const handleDisconnect = (accountId: string, username: string) => {
    setDisconnectTarget({ id: accountId, username });
  };

  const confirmDisconnect = async () => {
    if (!disconnectTarget) return;
    try {
      await api.disconnectInstagram(disconnectTarget.id);
      await loadAccounts();
      toast.success('Account disconnected');
    } catch (error) {
      toast.error('Failed to disconnect account');
    } finally {
      setDisconnectTarget(null);
    }
  };

  const isTokenExpiringSoon = (expiresAt: string) => {
    const daysUntilExpiry = Math.ceil(
      (new Date(expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    );
    return daysUntilExpiry < 7;
  };

  const tabs = [
    { key: 'instagram' as const, label: 'Instagram', icon: Instagram },
    { key: 'profile' as const, label: 'Profile', icon: User },
    { key: 'security' as const, label: 'Security', icon: Shield },
    { key: 'account' as const, label: 'Account', icon: KeyRound },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white">Settings</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mt-1">
          Manage your account, security, and preferences
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 p-1.5 bg-neutral-100 dark:bg-neutral-800/50 rounded-2xl overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm whitespace-nowrap transition-all ${activeTab === tab.key
              ? 'bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white shadow-sm'
              : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
              }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Link
          to="/settings/change-password"
          className="flex items-center gap-3 p-4 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl hover:border-purple-300 dark:hover:border-purple-800 transition-all group"
        >
          <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
            <Lock className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-neutral-900 dark:text-white">Change Password</p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">Update your password via OTP</p>
          </div>
          <ChevronRight className="w-4 h-4 text-neutral-400 group-hover:text-purple-600 transition-colors" />
        </Link>



        <Link
          to="/feedback"
          className="flex items-center gap-3 p-4 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl hover:border-purple-300 dark:hover:border-purple-800 transition-all group"
        >
          <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-neutral-900 dark:text-white">Feedback</p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">Report bugs & request features</p>
          </div>
          <ChevronRight className="w-4 h-4 text-neutral-400 group-hover:text-purple-600 transition-colors" />
        </Link>
      </div>

      {/* ==================== Instagram Tab ==================== */}
      {activeTab === 'instagram' && (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
                Instagram Accounts
              </h2>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                Choose a connection method to link your Instagram account.
              </p>
            </div>
          </div>

          {/* Connection Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* Option 1: Direct Instagram Login */}
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-xl p-5 flex flex-col items-start gap-3">
              <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
                <Instagram className="w-5 h-5 flex-shrink-0" />
                <h4 className="font-bold">Connect via Instagram</h4>
              </div>
              <div className="text-sm text-purple-900/80 dark:text-purple-200/80 flex-1">
                <p className="mb-2"><strong>Recommended.</strong> Fastest way to automate DMs.</p>
                <ul className="list-disc list-inside space-y-1 ml-1 text-xs">
                  <li>No Facebook Page required</li>
                  <li>Direct login via Instagram App</li>
                </ul>
              </div>
              <button
                onClick={() => handleConnectInstagram('instagram_platform')}
                className="w-full py-2.5 mt-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
              >
                <Instagram className="w-4 h-4" />
                Connect Instagram
              </button>
            </div>

            {/* Option 2: Facebook Graph API */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-5 flex flex-col items-start gap-3">
              <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
                <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path fillRule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clipRule="evenodd" />
                </svg>
                <h4 className="font-bold">Connect via Facebook</h4>
              </div>
              <div className="text-sm text-blue-900/80 dark:text-blue-200/80 flex-1">
                <p className="mb-2"><strong>Legacy Method.</strong> Useful if you manage multiple tools.</p>
                <ul className="list-disc list-inside space-y-1 ml-1 text-xs">
                  <li>Requires a linked Facebook Page</li>
                  <li>Connects via Meta Business Suite</li>
                </ul>
              </div>
              <button
                onClick={() => handleConnectInstagram('facebook_graph')}
                className="w-full py-2.5 mt-2 bg-[#1877F2] text-white rounded-lg font-medium hover:bg-[#166FE5] transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path fillRule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clipRule="evenodd" />
                </svg>
                Connect Facebook
              </button>
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
                  <div className={`absolute inset-0 bg-gradient-to-br ${account.is_active ? 'from-green-500/15 to-emerald-500/15' : 'from-neutral-500/10 to-neutral-500/5'} rounded-xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300`}></div>
                  <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
                    <div className="flex items-center gap-4">
                      {account.profile_picture_url ? (
                        <img src={account.profile_picture_url} alt={account.username} className="w-12 h-12 rounded-full" />
                      ) : (
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                          {account.username[0].toUpperCase()}
                        </div>
                      )}
                      <div>
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <h3 className="font-semibold text-neutral-900 dark:text-white">@{account.username}</h3>
                          {account.is_active ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                              <CheckCircle2 className="w-3 h-3" /> Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400">
                              Disconnected
                            </span>
                          )}
                          {isTokenExpiringSoon(account.token_expires_at) && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                              <AlertCircle className="w-3 h-3" /> Expires Soon
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
                      >
                        <RefreshCw className={`w-4 h-4 ${refreshing === account.id ? 'animate-spin' : ''}`} />
                      </button>
                      <button
                        onClick={() => handleDisconnect(account.id, account.username)}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
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
              <h3 className="text-lg font-medium text-neutral-900 dark:text-white mb-2">No Accounts Connected</h3>
              <p className="text-neutral-600 dark:text-neutral-400 mb-6 max-w-md mx-auto">
                Choose a connection method from the options above.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ==================== Profile Tab ==================== */}
      {activeTab === 'profile' && (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 rounded-xl bg-purple-100 dark:bg-purple-900/30">
              <User className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">Profile Information</h2>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">Update your personal details</p>
            </div>
          </div>

          {/* Profile Picture */}
          {profile && (
            <div className="flex items-center gap-5 mb-8 pb-6 border-b border-neutral-200 dark:border-neutral-800">
              <div className="relative">
                {profile.profile_picture ? (
                  <img src={profile.profile_picture} alt="Profile" className="w-20 h-20 rounded-2xl object-cover" />
                ) : (
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold">
                    {(profile.first_name?.[0] || profile.email[0]).toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900 dark:text-white">
                  {profile.first_name} {profile.last_name}
                </h3>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">{profile.email}</p>
                <p className="text-xs text-neutral-400 dark:text-neutral-500">@{profile.username}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleUpdateProfile} className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">First Name</label>
                <input
                  type="text"
                  className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                  value={profileForm.first_name}
                  onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Last Name</label>
                <input
                  type="text"
                  className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                  value={profileForm.last_name}
                  onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Phone</label>
              <input
                type="tel"
                className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                placeholder="+1 (555) 000-0000"
                value={profileForm.phone}
                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Bio</label>
              <textarea
                className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all resize-none"
                placeholder="Tell us about yourself..."
                rows={3}
                value={profileForm.bio}
                onChange={(e) => setProfileForm({ ...profileForm, bio: e.target.value })}
              />
            </div>

            <button
              type="submit"
              disabled={profileLoading}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
            >
              {profileLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </div>
      )}

      {/* ==================== Security Tab ==================== */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <TwoFactorSetup />
          <ActiveSessions />
        </div>
      )}

      {/* ==================== Account Tab ==================== */}
      {activeTab === 'account' && (
        <div className="space-y-6">
          {/* Email Verification Status */}
          <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center gap-3 mb-6">
              <div className={`p-2.5 rounded-xl ${profile?.is_email_verified ? 'bg-green-100 dark:bg-green-900/30' : 'bg-amber-100 dark:bg-amber-900/30'}`}>
                <Mail className={`w-6 h-6 ${profile?.is_email_verified ? 'text-green-600 dark:text-green-400' : 'text-amber-600 dark:text-amber-400'}`} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-white">Email Verification</h3>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  {profile?.email}
                </p>
              </div>
              {profile?.is_email_verified ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Verified
                </span>
              ) : (
                <button
                  onClick={handleResendVerification}
                  disabled={verificationLoading}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-lg text-sm font-medium hover:bg-amber-200 dark:hover:bg-amber-900/40 transition-colors disabled:opacity-50"
                >
                  <Mail className="w-4 h-4" />
                  {verificationLoading ? 'Sending...' : 'Verify Email'}
                </button>
              )}
            </div>
          </div>

          {/* Email Notifications */}
          <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                <Bell className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-white">Email Notifications</h3>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">Choose which emails you'd like to receive</p>
              </div>
            </div>

            <div className="space-y-1">
              {[
                { key: 'weekly_reports', label: 'Weekly Reports', desc: 'Receive weekly analytics summary every Monday' },
                { key: 'automation_alerts', label: 'Automation Alerts', desc: 'Get notified when automations are triggered' },
                { key: 'dm_failures', label: 'DM Failures', desc: 'Alert when DMs fail to send' },
                { key: 'account_issues', label: 'Account Issues', desc: 'Important account and security alerts' },
              ].map((item, index, arr) => (
                <div key={item.key} className={`flex items-center justify-between py-4 ${index < arr.length - 1 ? 'border-b border-neutral-200 dark:border-neutral-800' : ''}`}>
                  <div>
                    <h4 className="font-medium text-neutral-900 dark:text-white">{item.label}</h4>
                    <p className="text-sm text-neutral-500 dark:text-neutral-400">{item.desc}</p>
                  </div>
                  <button
                    onClick={() => handleNotifToggle(item.key)}
                    disabled={notifLoading}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ${(notifPreferences as any)[item.key] ? 'bg-purple-600' : 'bg-neutral-300 dark:bg-neutral-700'}`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${(notifPreferences as any)[item.key] ? 'translate-x-6' : 'translate-x-1'}`} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Danger Zone */}
          <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-red-200 dark:border-red-900/50">
            <h3 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-2">Danger Zone</h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-6">
              Once you delete your account, there is no going back. Please be certain.
            </p>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white rounded-xl font-medium hover:bg-red-700 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Delete Account
            </button>
          </div>
        </div>
      )}

      {/* Delete Account Modal */}
      <DeleteAccountModal isOpen={showDeleteModal} onClose={() => setShowDeleteModal(false)} />

      {/* Disconnect Instagram Confirm Modal */}
      <ConfirmModal
        open={!!disconnectTarget}
        title="Disconnect Account"
        message={`Are you sure you want to disconnect @${disconnectTarget?.username}? You can reconnect it at any time.`}
        confirmLabel="Disconnect"
        variant="danger"
        onConfirm={confirmDisconnect}
        onCancel={() => setDisconnectTarget(null)}
      />
    </div>
  );
};