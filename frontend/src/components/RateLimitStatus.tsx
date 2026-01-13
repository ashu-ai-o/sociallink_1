import React, { useEffect, useState } from 'react';
import { Clock, TrendingUp } from 'lucide-react';
import { api } from '../lib/api';

interface RateLimitData {
  username: string;
  dms_sent_this_hour: number;
  remaining_quota: number;
  limit: number;
  reset_time: string;
  queue_size: number;
}

export const RateLimitStatus: React.FC = () => {
  const [data, setData] = useState<RateLimitData[]>([]);
  
  useEffect(() => {
    loadRateLimits();
    const interval = setInterval(loadRateLimits, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);
  
  const loadRateLimits = async () => {
    try {
      const response = await api.client.get('/analytics/dashboard/rate_limit_status/');
      setData(response.data);
    } catch (error) {
      console.error('Failed to load rate limits:', error);
    }
  };
  
  const getPercentage = (sent: number, limit: number) => {
    return (sent / limit) * 100;
  };
  
  const getColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600 bg-red-50';
    if (percentage >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };
  
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Rate Limit Status
      </h3>
      
      <div className="space-y-4">
        {data.map((account) => {
          const percentage = getPercentage(account.dms_sent_this_hour, account.limit);
          const resetTime = new Date(account.reset_time);
          
          return (
            <div key={account.username} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">@{account.username}</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getColor(percentage)}`}>
                  {account.dms_sent_this_hour} / {account.limit}
                </span>
              </div>
              
              <div className="mb-2">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      percentage >= 90 ? 'bg-red-500' :
                      percentage >= 70 ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>Resets at {resetTime.toLocaleTimeString()}</span>
                </div>
                
                {account.queue_size > 0 && (
                  <div className="flex items-center gap-1 text-yellow-600">
                    <TrendingUp className="w-4 h-4" />
                    <span>{account.queue_size} queued</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
