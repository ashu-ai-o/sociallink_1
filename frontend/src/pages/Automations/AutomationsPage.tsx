// ============================================================================
// AUTOMATIONS PAGE - Clean card-based list with ZapDM-inspired design
// ============================================================================

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  Zap,
  Edit2,
  Trash2,
  Power,
  PowerOff,
  MessageCircle,
  Send,
  TrendingUp,
} from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import {
  fetchAutomations,
  toggleAutomation,
  deleteAutomation,
} from '../../store/slices/automationsSlice';
import toast from 'react-hot-toast';

export const AutomationsPage = () => {
  const dispatch = useAppDispatch();
  const { items: automations, loading } = useAppSelector(
    (state) => state.automations
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');

  useEffect(() => {
    dispatch(fetchAutomations());
  }, []);

  const handleToggle = async (id: string) => {
    try {
      await dispatch(toggleAutomation(id)).unwrap();
      toast.success('Automation updated successfully');
    } catch (error) {
      toast.error('Failed to update automation');
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
      try {
        await dispatch(deleteAutomation(id)).unwrap();
        toast.success('Automation deleted successfully');
      } catch (error) {
        toast.error('Failed to delete automation');
      }
    }
  };

  const filteredAutomations = automations.filter((automation) => {
    const matchesSearch = automation.name
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesFilter =
      filterStatus === 'all' ||
      (filterStatus === 'active' && automation.is_active) ||
      (filterStatus === 'inactive' && !automation.is_active);
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white">
            Automations
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            Manage your Instagram automation workflows
          </p>
        </div>
        <Link
          to="/automations/create"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <Plus className="w-4 h-4" />
          Create Automation
        </Link>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
          <input
            type="text"
            placeholder="Search automations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 bg-neutral-100 dark:bg-neutral-900 rounded-lg p-1">
          <button
            onClick={() => setFilterStatus('all')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              filterStatus === 'all'
                ? 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white shadow-sm'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilterStatus('active')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              filterStatus === 'active'
                ? 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white shadow-sm'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => setFilterStatus('inactive')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              filterStatus === 'inactive'
                ? 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white shadow-sm'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            Inactive
          </button>
        </div>
      </div>

      {/* Automations List */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 animate-pulse"
            >
              <div className="h-5 bg-neutral-200 dark:bg-neutral-800 rounded w-1/3 mb-4"></div>
              <div className="h-4 bg-neutral-200 dark:bg-neutral-800 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : filteredAutomations.length > 0 ? (
        <div className="space-y-4">
          {filteredAutomations.map((automation) => (
            <div
              key={automation.id}
              className="bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-soft-lg transition-all duration-200 group"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-medium text-neutral-900 dark:text-white">
                      {automation.name}
                    </h3>
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
                  </div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2">
                    {automation.dm_message.substring(0, 120)}...
                  </p>
                </div>

                {/* Toggle Switch */}
                <button
                  onClick={() => handleToggle(automation.id)}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    automation.is_active
                      ? 'bg-green-500'
                      : 'bg-neutral-300 dark:bg-neutral-700'
                  }`}
                  title={automation.is_active ? 'Pause automation' : 'Activate automation'}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform ${
                      automation.is_active ? 'translate-x-6' : 'translate-x-0'
                    }`}
                  ></span>
                </button>
              </div>

              {/* Stats */}
              <div className="flex items-center gap-6 mb-4 py-4 border-t border-b border-neutral-200 dark:border-neutral-800">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-neutral-100 dark:bg-neutral-800 rounded-lg">
                    <MessageCircle className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-neutral-900 dark:text-white">
                      {automation.total_triggers}
                    </div>
                    <div className="text-xs text-neutral-500">Triggers</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <Send className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-neutral-900 dark:text-white">
                      {automation.total_dms_sent}
                    </div>
                    <div className="text-xs text-neutral-500">DMs Sent</div>
                  </div>
                </div>

                {automation.total_comment_replies > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-neutral-900 dark:text-white">
                        {automation.total_comment_replies}
                      </div>
                      <div className="text-xs text-neutral-500">Replies</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3">
                <Link
                  to={`/automations/${automation.id}/edit`}
                  className="flex items-center gap-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg text-sm font-medium hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                  Edit
                </Link>
                <button
                  onClick={() => handleDelete(automation.id, automation.name)}
                  className="flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-12 border border-neutral-200 dark:border-neutral-800 text-center">
          <div className="max-w-md mx-auto">
            <Zap className="w-16 h-16 text-neutral-300 dark:text-neutral-700 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-neutral-900 dark:text-white mb-2">
              {searchQuery || filterStatus !== 'all'
                ? 'No automations found'
                : 'No automations yet'}
            </h3>
            <p className="text-neutral-600 dark:text-neutral-400 mb-6">
              {searchQuery || filterStatus !== 'all'
                ? 'Try adjusting your search or filter settings'
                : 'Create your first automation to start engaging with your Instagram audience automatically'}
            </p>
            {!searchQuery && filterStatus === 'all' && (
              <Link
                to="/automations/create"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                <Plus className="w-4 h-4" />
                Create Your First Automation
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
