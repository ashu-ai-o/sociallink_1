import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Search, Download, Filter, Mail, User } from 'lucide-react';
import { api } from '../lib/api';
import { formatDistanceToNow } from 'date-fns';
import type { Contact } from '../types';

export const ContactsPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTag, setFilterTag] = useState<string>('');

  const { data: contacts, isLoading } = useQuery('contacts', () =>
    api.getContacts()
  );

  const filteredContacts = contacts?.results?.filter((contact: Contact) => {
    const matchesSearch = contact.instagram_username
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesTag = !filterTag || contact.tags.includes(filterTag);
    return matchesSearch && matchesTag;
  });

  const handleExport = async () => {
    const blob = await api.exportContacts('csv');
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'contacts.csv';
    a.click();
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Contacts</h1>
          <p className="text-gray-600 mt-1">
            {contacts?.count || 0} total contacts
          </p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
        >
          <Download className="w-5 h-5" />
          Export
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search contacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            <Filter className="w-5 h-5" />
            Filters
          </button>
        </div>
      </div>

      {/* Contacts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredContacts?.map((contact: Contact) => (
          <div
            key={contact.id}
            className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center gap-4 mb-4">
              {contact.profile_picture_url ? (
                <img
                  src={contact.profile_picture_url}
                  alt={contact.instagram_username}
                  className="w-12 h-12 rounded-full"
                />
              ) : (
                <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                  <User className="w-6 h-6 text-purple-600" />
                </div>
              )}
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">
                  @{contact.instagram_username}
                </h3>
                {contact.full_name && (
                  <p className="text-sm text-gray-500">{contact.full_name}</p>
                )}
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">DMs Received</span>
                <span className="font-medium text-gray-900">
                  {contact.total_dms_received}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Interactions</span>
                <span className="font-medium text-gray-900">
                  {contact.total_interactions}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Last Seen</span>
                <span className="font-medium text-gray-900">
                  {formatDistanceToNow(new Date(contact.last_interaction), {
                    addSuffix: true,
                  })}
                </span>
              </div>
            </div>

            {contact.tags.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {contact.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <button className="mt-4 w-full px-4 py-2 border border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors flex items-center justify-center gap-2">
              <Mail className="w-4 h-4" />
              Send Message
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
