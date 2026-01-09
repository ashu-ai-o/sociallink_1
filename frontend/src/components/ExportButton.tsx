import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { api } from '../lib/api';

interface ExportButtonProps {
  type: 'contacts' | 'triggers' | 'analytics';
  automationId?: string;
  period?: '7d' | '30d' | '90d';
}

export const ExportButton: React.FC<ExportButtonProps> = ({ 
  type, 
  automationId, 
  period = '30d' 
}) => {
  const [loading, setLoading] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  
  const handleExport = async (format: 'csv' | 'xlsx') => {
    setLoading(true);
    setShowMenu(false);
    
    try {
      if (type === 'contacts') {
        await api.exportContacts(format);
      } else if (type === 'triggers') {
        await api.exportTriggers(format, automationId);
      } else if (type === 'analytics') {
        await api.exportAnalytics(period);
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        disabled={loading}
        className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
      >
        <Download className="w-4 h-4" />
        {loading ? 'Exporting...' : 'Export'}
      </button>
      
      {showMenu && (
        <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          <button
            onClick={() => handleExport('csv')}
            className="w-full px-4 py-2 text-left hover:bg-gray-50 text-sm"
          >
            Export as CSV
          </button>
          <button
            onClick={() => handleExport('xlsx')}
            className="w-full px-4 py-2 text-left hover:bg-gray-50 text-sm"
          >
            Export as Excel
          </button>
        </div>
      )}
    </div>
  );
};

// Usage:
// <ExportButton type="contacts" />
// <ExportButton type="triggers" automationId={automation.id} />
// <ExportButton type="analytics" period="30d" />
