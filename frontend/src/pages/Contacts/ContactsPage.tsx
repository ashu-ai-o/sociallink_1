import { useState, useEffect } from 'react';
import { Search, Download, Filter, Mail, User, FileSpreadsheet, TrendingUp } from 'lucide-react';
import { api } from '../../utils/api';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

export const ContactsPage = () => {
  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [exportFormat, setExportFormat] = useState<'csv' | 'xlsx'>('csv');
  const [showExportMenu, setShowExportMenu] = useState(false);

  useEffect(() => {
    loadContacts();
  }, []);

  const loadContacts = async () => {
    try {
      setLoading(true);
      const data = await api.getContacts();
      setContacts(data.results || []);
    } catch (error) {
      console.error('Failed to load contacts:', error);
      toast.error('Failed to load contacts');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'csv' | 'xlsx') => {
    try {
      toast.loading('Preparing export...');
      const blob = await api.exportContactsFile(format);

      // Download blob
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `contacts_${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.dismiss();
      toast.success(`Contacts exported as ${format.toUpperCase()}`);
      setShowExportMenu(false);
    } catch (error) {
      toast.dismiss();
      toast.error('Export failed');
      console.error('Export failed:', error);
    }
  };

  const filteredContacts = contacts.filter((contact) =>
    contact.instagram_username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 slide-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Customer Database</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            {contacts.length} engaged followers automatically captured and organized by your automations
          </p>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="btn btn-primary"
          >
            <Download className="w-4 h-4" />
            Export Contacts
          </button>
          {showExportMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg z-10">
              <button
                onClick={() => handleExport('csv')}
                className="w-full px-4 py-2 text-left hover:bg-[var(--bg-hover)] flex items-center gap-2 text-[var(--text-primary)]"
              >
                <FileSpreadsheet className="w-4 h-4" />
                Export as CSV
              </button>
              <button
                onClick={() => handleExport('xlsx')}
                className="w-full px-4 py-2 text-left hover:bg-[var(--bg-hover)] flex items-center gap-2 text-[var(--text-primary)]"
              >
                <FileSpreadsheet className="w-4 h-4" />
                Export as Excel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Info Banner */}
      {!loading && contacts.length > 0 && (
        <div className="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
            <div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-1">
                Building Your Customer Relationships
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                Every contact represents a potential customer who engaged with your content.
                Use this data to understand your audience, follow up with interested leads, and build lasting relationships.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Search & Filter */}
      <div className="card">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-tertiary)]" />
            <input
              type="text"
              placeholder="Search contacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>
          <button className="btn btn-secondary">
            <Filter className="w-4 h-4" />
            Filters
          </button>
        </div>
      </div>

      {/* Contacts Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-40 bg-[var(--bg-secondary)] rounded"></div>
            </div>
          ))}
        </div>
      ) : filteredContacts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredContacts.map((contact: any) => (
            <div key={contact.id} className="card card-hover">
              <div className="flex items-center gap-4 mb-4">
                {contact.profile_picture_url ? (
                  <img
                    src={contact.profile_picture_url}
                    alt={contact.instagram_username}
                    className="w-12 h-12 rounded-full"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-[var(--accent-light)] flex items-center justify-center">
                    <User className="w-6 h-6 text-[var(--accent-primary)]" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-[var(--text-primary)] truncate">
                    @{contact.instagram_username}
                  </h3>
                  {contact.full_name && (
                    <p className="text-sm text-[var(--text-secondary)] truncate">
                      {contact.full_name}
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-2 text-sm mb-4">
                <div className="flex justify-between">
                  <span className="text-[var(--text-secondary)]">DMs Received</span>
                  <span className="font-medium text-[var(--text-primary)]">
                    {contact.total_dms_received}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-secondary)]">Interactions</span>
                  <span className="font-medium text-[var(--text-primary)]">
                    {contact.total_interactions}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-secondary)]">Last Seen</span>
                  <span className="font-medium text-[var(--text-primary)]">
                    {formatDistanceToNow(new Date(contact.last_interaction), {
                      addSuffix: true,
                    })}
                  </span>
                </div>
              </div>

              {contact.tags && contact.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {contact.tags.slice(0, 3).map((tag: string) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-[var(--accent-light)] text-[var(--accent-primary)] text-xs font-medium rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <button className="w-full btn btn-secondary text-sm">
                <Mail className="w-4 h-4" />
                Send Message
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <User className="w-16 h-16 text-[var(--text-tertiary)] mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
            {searchQuery ? 'No contacts match your search' : 'Start Building Your Customer Database'}
          </h3>
          <p className="text-[var(--text-secondary)] max-w-md mx-auto">
            {searchQuery
              ? 'Try adjusting your search terms to find the contact you\'re looking for'
              : 'Contacts will automatically appear here when your automations interact with followers. Each engagement is a potential customer relationship.'
            }
          </p>
        </div>
      )}
    </div>
  );
};


