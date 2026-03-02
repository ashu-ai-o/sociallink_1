import React, { useState, useEffect } from 'react';
import { Monitor, Smartphone, Tablet, Globe, Clock, MapPin, Trash2, LogOut, AlertTriangle, Shield, X } from 'lucide-react';
import { api } from '../../utils/api';
import toast from 'react-hot-toast';

interface Session {
    id: string;
    device_type: string;
    browser_name: string;
    browser_version: string;
    os_name: string;
    os_version: string;
    ip_address: string;
    city: string;
    country: string;
    is_active: boolean;
    is_vpn: boolean;
    is_tor: boolean;
    last_activity: string;
    created_at: string;
    login_method: string;
    is_current?: boolean;
}

// ── Confirmation Modal ──────────────────────────────────────────────────────
interface LogoutAllModalProps {
    isOpen: boolean;
    loading: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

const LogoutAllModal: React.FC<LogoutAllModalProps> = ({ isOpen, loading, onConfirm, onCancel }) => {
    if (!isOpen) return null;
    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={(e) => { if (e.target === e.currentTarget) onCancel(); }}
        >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-150" />

            {/* Modal */}
            <div className="relative w-full max-w-md bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl border border-neutral-200 dark:border-neutral-800 animate-in zoom-in-95 fade-in duration-150 overflow-hidden">
                {/* Top accent bar */}
                <div className="h-1 w-full bg-gradient-to-r from-red-500 to-rose-500" />

                <div className="p-6">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="flex-shrink-0 p-2.5 rounded-xl bg-red-100 dark:bg-red-900/30">
                                <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                            </div>
                            <div>
                                <h3 className="text-base font-semibold text-neutral-900 dark:text-white">
                                    Logout All Other Devices
                                </h3>
                                <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                                    Security action
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onCancel}
                            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Body */}
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed mb-2">
                        This will immediately end all active sessions on other devices. You will remain logged in on this device.
                    </p>
                    <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/15 border border-amber-200 dark:border-amber-800/50 mt-4 mb-5">
                        <Shield className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-amber-700 dark:text-amber-300">
                            Use this if you suspect unauthorised access to your account.
                        </p>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 justify-end">
                        <button
                            onClick={onCancel}
                            disabled={loading}
                            className="px-4 py-2 rounded-xl text-sm font-medium text-neutral-700 dark:text-neutral-300 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={onConfirm}
                            disabled={loading}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white bg-red-600 hover:bg-red-700 transition-colors disabled:opacity-60 shadow-lg shadow-red-500/20"
                        >
                            <LogOut className="w-4 h-4" />
                            {loading ? 'Logging out…' : 'Yes, Logout All'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
// ────────────────────────────────────────────────────────────────────────────

export const ActiveSessions: React.FC = () => {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(true);
    const [endingSession, setEndingSession] = useState<string | null>(null);
    const [logoutAllLoading, setLogoutAllLoading] = useState(false);
    const [showLogoutAllModal, setShowLogoutAllModal] = useState(false);

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async () => {
        try {
            const data = await api.getActiveSessions();
            setSessions(data.sessions || data || []);
        } catch (error) {
            console.error('Failed to load sessions:', error);
            toast.error('Failed to load sessions');
        } finally {
            setLoading(false);
        }
    };

    const handleEndSession = async (sessionId: string) => {
        setEndingSession(sessionId);
        try {
            await api.endSession(sessionId);
            toast.success('Session ended');
            setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        } catch (error) {
            toast.error('Failed to end session');
        } finally {
            setEndingSession(null);
        }
    };

    const handleLogoutAllDevices = async () => {
        setShowLogoutAllModal(false);
        setLogoutAllLoading(true);
        try {
            await api.logoutAllDevices(true);
            toast.success('Logged out from all other devices');
            loadSessions();
        } catch (error) {
            toast.error('Failed to logout from all devices');
        } finally {
            setLogoutAllLoading(false);
        }
    };

    const getDeviceIcon = (type: string) => {
        switch (type) {
            case 'mobile':
                return <Smartphone className="w-5 h-5" />;
            case 'tablet':
                return <Tablet className="w-5 h-5" />;
            default:
                return <Monitor className="w-5 h-5" />;
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    if (loading) {
        return (
            <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
                <div className="animate-pulse space-y-4">
                    {[...Array(3)].map((_, i) => (
                        <div key={i} className="h-20 bg-neutral-200 dark:bg-neutral-800 rounded-xl"></div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                        <Globe className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-neutral-900 dark:text-white">
                            Active Sessions
                        </h3>
                        <p className="text-sm text-neutral-600 dark:text-neutral-400">
                            Manage your active sessions and devices
                        </p>
                    </div>
                </div>

                {sessions.length > 1 && (
                    <button
                        onClick={() => setShowLogoutAllModal(true)}
                        disabled={logoutAllLoading}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors disabled:opacity-50"
                    >
                        <LogOut className="w-4 h-4" />
                        {logoutAllLoading ? 'Logging out…' : 'Logout All Others'}
                    </button>
                )}
            </div>

            {sessions.length === 0 ? (
                <div className="text-center py-8">
                    <Globe className="w-12 h-12 text-neutral-300 dark:text-neutral-700 mx-auto mb-3" />
                    <p className="text-neutral-500 dark:text-neutral-400">No active sessions found</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {sessions.map((session) => (
                        <div
                            key={session.id}
                            className={`relative flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border transition-all ${session.is_current
                                ? 'bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-900'
                                : 'bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700'
                                }`}
                        >
                            <div className="flex items-center gap-4">
                                <div className={`p-2.5 rounded-xl ${session.is_current ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400' : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'}`}>
                                    {getDeviceIcon(session.device_type)}
                                </div>
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <h4 className="font-medium text-neutral-900 dark:text-white text-sm">
                                            {session.browser_name || 'Unknown'} {session.browser_version ? `v${session.browser_version}` : ''}
                                        </h4>
                                        {session.is_current && (
                                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 uppercase tracking-wider">
                                                This Device
                                            </span>
                                        )}
                                        {(session.is_vpn || session.is_tor) && (
                                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                                                {session.is_tor ? 'TOR' : 'VPN'}
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex flex-wrap items-center gap-3 text-xs text-neutral-500 dark:text-neutral-400">
                                        <span className="flex items-center gap-1">
                                            <Monitor className="w-3 h-3" />
                                            {session.os_name || 'Unknown OS'} {session.os_version || ''}
                                        </span>
                                        {(session.city || session.country) && (
                                            <span className="flex items-center gap-1">
                                                <MapPin className="w-3 h-3" />
                                                {[session.city, session.country].filter(Boolean).join(', ')}
                                            </span>
                                        )}
                                        <span className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {formatDate(session.last_activity)}
                                        </span>
                                        <span className="text-neutral-400 dark:text-neutral-500">
                                            {session.ip_address}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {!session.is_current && (
                                <button
                                    onClick={() => handleEndSession(session.id)}
                                    disabled={endingSession === session.id}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 rounded-lg text-xs font-medium hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                    {endingSession === session.id ? 'Ending...' : 'End Session'}
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            )}

            <LogoutAllModal
                isOpen={showLogoutAllModal}
                loading={logoutAllLoading}
                onConfirm={handleLogoutAllDevices}
                onCancel={() => setShowLogoutAllModal(false)}
            />
        </div>
    );
};
