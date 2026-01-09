import { useState, useEffect } from 'react';
import { Search, Download, Filter, Mail, User } from 'lucide-react';
import { api } from '../../utils/api';
import { formatDistanceToNow } from 'date-fns';

export const ContactsPage = () => {
  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

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
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const blob = await api.client.get('/contacts/export/', {
        params: { format: 'csv' },
        responseType: 'blob',
      });
      // Download blob
      const url = window.URL.createObjectURL(new Blob([blob.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'contacts.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
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
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Contacts</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            {contacts.length} total contacts from your automations
          </p>
        </div>
        <button onClick={handleExport} className="btn btn-primary">
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

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
            No contacts found
          </h3>
          <p className="text-[var(--text-secondary)]">
            Contacts will appear here as your automations interact with users
          </p>
        </div>
      )}
    </div>
  );
};


