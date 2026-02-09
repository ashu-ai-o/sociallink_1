import { useState, useEffect } from 'react';
import { Search, Download, User, FileSpreadsheet, TrendingUp, Mail } from 'lucide-react';
import { api } from '../../utils/api';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

export const ContactsPage = () => {
  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
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
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white">
            Contacts
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            {contacts.length} engaged followers captured by your automations
          </p>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          {showExportMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl shadow-soft-lg z-10 overflow-hidden">
              <button
                onClick={() => handleExport('csv')}
                className="w-full px-4 py-3 text-left hover:bg-neutral-50 dark:hover:bg-neutral-800 flex items-center gap-2 text-neutral-900 dark:text-white transition-colors"
              >
                <FileSpreadsheet className="w-4 h-4" />
                Export as CSV
              </button>
              <button
                onClick={() => handleExport('xlsx')}
                className="w-full px-4 py-3 text-left hover:bg-neutral-50 dark:hover:bg-neutral-800 flex items-center gap-2 text-neutral-900 dark:text-white transition-colors"
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
        <div className="bg-blue-50 dark:bg-blue-950/30 rounded-2xl p-6 border border-blue-200 dark:border-blue-900">
          <div className="flex items-start gap-4">
            <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">
                Building Your Customer Database
              </h3>
              <p className="text-sm text-neutral-700 dark:text-neutral-300">
                Every contact represents a potential customer who engaged with your content.
                Use this data to understand your audience and build lasting relationships.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
        <input
          type="text"
          placeholder="Search contacts..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-12 pr-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
        />
      </div>

      {/* Contacts Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 animate-pulse">
              <div className="h-40 bg-neutral-200 dark:bg-neutral-800 rounded"></div>
            </div>
          ))}
        </div>
      ) : filteredContacts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredContacts.map((contact: any) => (
            <div key={contact.id} className="group relative">
              {/* 3D floating shadow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-2xl blur-xl transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-3 transition-all duration-300"></div>

              <div className="relative bg-white dark:bg-neutral-900 rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800 hover:shadow-2xl transition-all duration-300 group-hover:-translate-y-1">
              <div className="flex items-center gap-4 mb-4">
                {contact.profile_picture_url ? (
                  <img
                    src={contact.profile_picture_url}
                    alt={contact.instagram_username}
                    className="w-12 h-12 rounded-full"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center">
                    <User className="w-6 h-6 text-neutral-600 dark:text-neutral-400" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-neutral-900 dark:text-white truncate">
                    @{contact.instagram_username}
                  </h3>
                  {contact.full_name && (
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 truncate">
                      {contact.full_name}
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-2 text-sm mb-4 pb-4 border-b border-neutral-200 dark:border-neutral-800">
                <div className="flex justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">DMs Received</span>
                  <span className="font-medium text-neutral-900 dark:text-white">
                    {contact.total_dms_received}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">Interactions</span>
                  <span className="font-medium text-neutral-900 dark:text-white">
                    {contact.total_interactions}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">Last Seen</span>
                  <span className="font-medium text-neutral-900 dark:text-white">
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
                      className="px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-xs font-medium rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg text-sm font-medium hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors">
                <Mail className="w-4 h-4" />
                Send Message
              </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-12 border border-neutral-200 dark:border-neutral-800 text-center">
          <User className="w-16 h-16 text-neutral-300 dark:text-neutral-700 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-neutral-900 dark:text-white mb-2">
            {searchQuery ? 'No contacts found' : 'No contacts yet'}
          </h3>
          <p className="text-neutral-600 dark:text-neutral-400 max-w-md mx-auto">
            {searchQuery
              ? 'Try adjusting your search terms'
              : 'Contacts will appear here when your automations interact with followers'}
          </p>
        </div>
      )}
    </div>
  );
};
