import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Filter, Zap, MoreVertical, Edit, Trash2, Power, PowerOff } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { fetchAutomations, toggleAutomation, deleteAutomation } from '../../store/slices/automationsSlice';
import toast from 'react-hot-toast';

export const AutomationsPage = () => {
  const dispatch = useAppDispatch();
  const { items: automations, loading } = useAppSelector((state) => state.automations);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');

  useEffect(() => {
    dispatch(fetchAutomations());
  }, []);

  const handleToggle = async (id: string) => {
    try {
      await dispatch(toggleAutomation(id)).unwrap();
      toast.success('Automation toggled successfully');
    } catch (error) {
      toast.error('Failed to toggle automation');
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
      try {
        await dispatch(deleteAutomation(id)).unwrap();
        toast.success('Automation deleted');
      } catch (error) {
        toast.error('Failed to delete automation');
      }
    }
  };

  const filteredAutomations = automations.filter((automation) => {
    const matchesSearch = automation.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter =
      filterStatus === 'all' ||
      (filterStatus === 'active' && automation.is_active) ||
      (filterStatus === 'inactive' && !automation.is_active);
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6 slide-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Automations</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Manage your Instagram automation workflows
          </p>
        </div>
        <Link to="/automations/create" className="btn btn-primary">
          <Plus className="w-4 h-4" />
          New Automation
        </Link>
      </div>

      {/* Search & Filter */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)]" />
            <input
              type="text"
              placeholder="Search automations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setFilterStatus('all')}
              className={`btn ${
                filterStatus === 'all' ? 'btn-primary' : 'btn-secondary'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterStatus('active')}
              className={`btn ${
                filterStatus === 'active' ? 'btn-primary' : 'btn-secondary'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setFilterStatus('inactive')}
              className={`btn ${
                filterStatus === 'inactive' ? 'btn-primary' : 'btn-secondary'
              }`}
            >
              Inactive
            </button>
          </div>
        </div>
      </div>

      {/* Automations Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-32 bg-[var(--bg-secondary)] rounded"></div>
            </div>
          ))}
        </div>
      ) : filteredAutomations.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAutomations.map((automation) => (
            <div key={automation.id} className="card card-hover group">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    automation.is_active
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                  }`}>
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
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
                </div>
                <div className="relative">
                  <button className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-tertiary)] opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                {automation.name}
              </h3>

              <p className="text-sm text-[var(--text-secondary)] mb-4 line-clamp-2">
                {automation.dm_message.substring(0, 80)}...
              </p>

              <div className="grid grid-cols-3 gap-4 mb-4 py-4 border-t border-[var(--border-primary)]">
                <div>
                  <div className="text-2xl font-bold text-[var(--text-primary)]">
                    {automation.total_triggers}
                  </div>
                  <div className="text-xs text-[var(--text-tertiary)]">Triggers</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[var(--text-primary)]">
                    {automation.total_dms_sent}
                  </div>
                  <div className="text-xs text-[var(--text-tertiary)]">DMs Sent</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[var(--text-primary)]">
                    {automation.total_comment_replies}
                  </div>
                  <div className="text-xs text-[var(--text-tertiary)]">Replies</div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleToggle(automation.id)}
                  className="flex-1 btn btn-secondary text-sm"
                >
                  {automation.is_active ? (
                    <>
                      <PowerOff className="w-4 h-4" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Power className="w-4 h-4" />
                      Activate
                    </>
                  )}
                </button>
                <Link
                  to={`/automations/${automation.id}/edit`}
                  className="btn btn-secondary text-sm"
                >
                  <Edit className="w-4 h-4" />
                </Link>
                <button
                  onClick={() => handleDelete(automation.id, automation.name)}
                  className="btn btn-secondary text-sm text-[var(--error)]"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <Zap className="w-16 h-16 text-[var(--text-tertiary)] mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
            {searchQuery || filterStatus !== 'all'
              ? 'No automations found'
              : 'No automations yet'}
          </h3>
          <p className="text-[var(--text-secondary)] mb-6">
            {searchQuery || filterStatus !== 'all'
              ? 'Try adjusting your search or filters'
              : 'Create your first automation to start automating Instagram DMs'}
          </p>
          {!searchQuery && filterStatus === 'all' && (
            <Link to="/automations/create" className="btn btn-primary">
              <Plus className="w-4 h-4" />
              Create Your First Automation
            </Link>
          )}
        </div>
      )}
    </div>
  );
};
