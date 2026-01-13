// ============================================================================
// ENHANCED CHARTS & GRAPHS (Using Recharts)
// ============================================================================

/**
 * Beautiful, interactive charts for analytics dashboard
 * Recharts is already in package.json, so these work out of the box!
 */

import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

// ============================================================================
// 1. DM VOLUME CHART (Line + Area)
// ============================================================================

interface DMVolumeChartProps {
  data: Array<{
    date: string;
    dms_sent: number;
    triggers: number;
  }>;
}

export const DMVolumeChart: React.FC<DMVolumeChartProps> = ({ data }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        DM Volume Over Time
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorDMs" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorTriggers" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="date" 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="dms_sent"
            stroke="#8b5cf6"
            fillOpacity={1}
            fill="url(#colorDMs)"
            strokeWidth={2}
            name="DMs Sent"
          />
          <Area
            type="monotone"
            dataKey="triggers"
            stroke="#10b981"
            fillOpacity={1}
            fill="url(#colorTriggers)"
            strokeWidth={2}
            name="Triggers"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};


// ============================================================================
// 2. SUCCESS RATE CHART (Line with trend indicator)
// ============================================================================

interface SuccessRateChartProps {
  data: Array<{
    date: string;
    success_rate: number;
  }>;
}

export const SuccessRateChart: React.FC<SuccessRateChartProps> = ({ data }) => {
  // Calculate trend
  const firstRate = data[0]?.success_rate || 0;
  const lastRate = data[data.length - 1]?.success_rate || 0;
  const trend = lastRate - firstRate;
  const isPositive = trend >= 0;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Success Rate Trend
        </h3>
        <div className={`flex items-center gap-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span className="text-sm font-medium">
            {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
          </span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="date" 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value: number) => `${value.toFixed(1)}%`}
          />
          <Line
            type="monotone"
            dataKey="success_rate"
            stroke="#8b5cf6"
            strokeWidth={3}
            dot={{ fill: '#8b5cf6', r: 4 }}
            activeDot={{ r: 6 }}
            name="Success Rate"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};


// ============================================================================
// 3. AUTOMATION PERFORMANCE BAR CHART
// ============================================================================

interface AutomationPerformanceProps {
  data: Array<{
    name: string;
    triggers: number;
    dms_sent: number;
  }>;
}

export const AutomationPerformanceChart: React.FC<AutomationPerformanceProps> = ({ data }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Automation Performance
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} barGap={8}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="name" 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Bar 
            dataKey="triggers" 
            fill="#10b981" 
            radius={[8, 8, 0, 0]}
            name="Triggers"
          />
          <Bar 
            dataKey="dms_sent" 
            fill="#8b5cf6" 
            radius={[8, 8, 0, 0]}
            name="DMs Sent"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};


// ============================================================================
// 4. AI USAGE PIE CHART
// ============================================================================

interface AIUsageChartProps {
  data: {
    ai_enhanced: number;
    manual: number;
  };
}

export const AIUsageChart: React.FC<AIUsageChartProps> = ({ data }) => {
  const total = data.ai_enhanced + data.manual;
  const aiPercentage = ((data.ai_enhanced / total) * 100).toFixed(1);

  const chartData = [
    { name: 'AI Enhanced', value: data.ai_enhanced, color: '#8b5cf6' },
    { name: 'Manual', value: data.manual, color: '#e5e7eb' },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        AI Enhancement Usage
      </h3>
      <div className="flex items-center gap-8">
        <ResponsiveContainer width="60%" height={200}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
        
        <div className="flex-1">
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600">AI Enhanced</span>
                <span className="text-sm font-medium">{aiPercentage}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-600"
                  style={{ width: `${aiPercentage}%` }}
                />
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {data.ai_enhanced.toLocaleString()} of {total.toLocaleString()} messages
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


// ============================================================================
// 5. HOURLY ACTIVITY HEATMAP
// ============================================================================

interface HourlyActivityProps {
  data: Array<{
    hour: string;
    count: number;
  }>;
}

export const HourlyActivityChart: React.FC<HourlyActivityProps> = ({ data }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Activity by Hour
      </h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="hour" 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Bar 
            dataKey="count" 
            fill="#8b5cf6" 
            radius={[8, 8, 0, 0]}
            name="Activities"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};


// ============================================================================
// 6. CONVERSION FUNNEL CHART
// ============================================================================

interface ConversionFunnelProps {
  data: Array<{
    stage: string;
    value: number;
    color: string;
  }>;
}

export const ConversionFunnelChart: React.FC<ConversionFunnelProps> = ({ data }) => {
  const maxValue = data[0]?.value || 1;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Conversion Funnel
      </h3>
      <div className="space-y-4">
        {data.map((stage, index) => {
          const percentage = (stage.value / maxValue) * 100;
          const conversionRate = index > 0 
            ? ((stage.value / data[index - 1].value) * 100).toFixed(1)
            : '100.0';

          return (
            <div key={stage.stage}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">
                  {stage.stage}
                </span>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-600">
                    {stage.value.toLocaleString()}
                  </span>
                  {index > 0 && (
                    <span className="text-xs text-green-600 font-medium">
                      {conversionRate}%
                    </span>
                  )}
                </div>
              </div>
              <div className="h-12 bg-gray-100 rounded-lg overflow-hidden">
                <div
                  className="h-full flex items-center justify-center text-white font-medium transition-all duration-500"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: stage.color,
                  }}
                >
                  {percentage > 20 && `${percentage.toFixed(0)}%`}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};


// ============================================================================
// 7. SPARKLINE MINI CHART
// ============================================================================

interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
}

export const Sparkline: React.FC<SparklineProps> = ({ 
  data, 
  color = '#8b5cf6',
  height = 40 
}) => {
  const formattedData = data.map((value, index) => ({ index, value }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={formattedData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};


// ============================================================================
// 8. USAGE IN ANALYTICS PAGE
// ============================================================================

export const EnhancedAnalyticsPage: React.FC = () => {
  // Sample data - replace with actual API data
  const volumeData = [
    { date: 'Jan 1', dms_sent: 45, triggers: 52 },
    { date: 'Jan 2', dms_sent: 62, triggers: 68 },
    { date: 'Jan 3', dms_sent: 78, triggers: 85 },
    { date: 'Jan 4', dms_sent: 91, triggers: 98 },
    { date: 'Jan 5', dms_sent: 105, triggers: 112 },
    { date: 'Jan 6', dms_sent: 88, triggers: 95 },
    { date: 'Jan 7', dms_sent: 120, triggers: 128 },
  ];

  const successData = [
    { date: 'Jan 1', success_rate: 86.5 },
    { date: 'Jan 2', success_rate: 91.2 },
    { date: 'Jan 3', success_rate: 91.8 },
    { date: 'Jan 4', success_rate: 92.9 },
    { date: 'Jan 5', success_rate: 93.8 },
    { date: 'Jan 6', success_rate: 92.6 },
    { date: 'Jan 7', success_rate: 93.8 },
  ];

  const automationData = [
    { name: 'Link in Bio', triggers: 156, dms_sent: 145 },
    { name: 'Product Launch', triggers: 98, dms_sent: 92 },
    { name: 'Welcome Message', triggers: 67, dms_sent: 65 },
    { name: 'Giveaway', triggers: 234, dms_sent: 220 },
  ];

  const aiUsageData = {
    ai_enhanced: 420,
    manual: 135,
  };

  const funnelData = [
    { stage: 'Comments', value: 1000, color: '#8b5cf6' },
    { stage: 'DMs Sent', value: 850, color: '#7c3aed' },
    { stage: 'Opened', value: 680, color: '#6d28d9' },
    { stage: 'Clicked', value: 340, color: '#5b21b6' },
    { stage: 'Converted', value: 170, color: '#4c1d95' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>

      {/* Top Row: Volume & Success Rate */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DMVolumeChart data={volumeData} />
        <SuccessRateChart data={successData} />
      </div>

      {/* Middle Row: Automation Performance */}
      <AutomationPerformanceChart data={automationData} />

      {/* Bottom Row: AI Usage & Funnel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AIUsageChart data={aiUsageData} />
        <ConversionFunnelChart data={funnelData} />
      </div>
    </div>
  );
};


// ============================================================================
// 9. STAT CARD WITH SPARKLINE
// ============================================================================

interface StatCardWithChartProps {
  title: string;
  value: string | number;
  change: number;
  data: number[];
  icon: React.ReactNode;
}

export const StatCardWithChart: React.FC<StatCardWithChartProps> = ({
  title,
  value,
  change,
  data,
  icon,
}) => {
  const isPositive = change >= 0;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          <div className={`flex items-center gap-1 mt-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            <span className="text-sm font-medium">
              {change > 0 ? '+' : ''}{change}%
            </span>
          </div>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg text-purple-600">
          {icon}
        </div>
      </div>
      <Sparkline data={data} color={isPositive ? '#10b981' : '#ef4444'} />
    </div>
  );
};