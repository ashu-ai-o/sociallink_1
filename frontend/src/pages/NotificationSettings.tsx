import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';

type PreferenceKey = 'weekly_reports' | 'automation_alerts' | 'dm_failures' | 'account_issues';

type Preferences = {
  weekly_reports: boolean;
  automation_alerts: boolean;
  dm_failures: boolean;
  account_issues: boolean;
};

export const NotificationSettings: React.FC = () => {
  const [preferences, setPreferences] = useState<Preferences>({
    weekly_reports: true,
    automation_alerts: true,
    dm_failures: true,
    account_issues: true,
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const response = await api.client.get('/users/email_preferences/');
      setPreferences(response.data);
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
  };

  const handleToggle = async (key: PreferenceKey) => {
    const newPreferences = {
      ...preferences,
      [key]: !preferences[key],
    };
    
    setPreferences(newPreferences);
    setLoading(true);

    try {
      await api.client.patch('/users/email_preferences/', { [key]: newPreferences[key] });
    } catch (error) {
      console.error('Failed to update preference:', error);
      setPreferences(preferences); // Revert on error
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Email Notifications</h2>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between py-3 border-b border-gray-200">
          <div>
            <h3 className="font-medium text-gray-900">Weekly Reports</h3>
            <p className="text-sm text-gray-600">Receive weekly analytics summary every Monday</p>
          </div>
          <button
            onClick={() => handleToggle('weekly_reports')}
            disabled={loading}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.weekly_reports ? 'bg-purple-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences.weekly_reports ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        <div className="flex items-center justify-between py-3 border-b border-gray-200">
          <div>
            <h3 className="font-medium text-gray-900">Automation Alerts</h3>
            <p className="text-sm text-gray-600">Get notified when automations are triggered</p>
          </div>
          <button
            onClick={() => handleToggle('automation_alerts')}
            disabled={loading}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.automation_alerts ? 'bg-purple-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences.automation_alerts ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        <div className="flex items-center justify-between py-3 border-b border-gray-200">
          <div>
            <h3 className="font-medium text-gray-900">DM Failures</h3>
            <p className="text-sm text-gray-600">Alert when DMs fail to send</p>
          </div>
          <button
            onClick={() => handleToggle('dm_failures')}
            disabled={loading}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.dm_failures ? 'bg-purple-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences.dm_failures ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        <div className="flex items-center justify-between py-3">
          <div>
            <h3 className="font-medium text-gray-900">Account Issues</h3>
            <p className="text-sm text-gray-600">Important account and security alerts</p>
          </div>
          <button
            onClick={() => handleToggle('account_issues')}
            disabled={loading}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.account_issues ? 'bg-purple-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences.account_issues ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
};
