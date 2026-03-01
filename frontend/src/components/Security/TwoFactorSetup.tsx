import React, { useState, useEffect } from 'react';
import { Shield, ShieldCheck, ShieldOff, Copy, RefreshCw, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { api } from '../../utils/api';
import toast from 'react-hot-toast';

export const TwoFactorSetup: React.FC = () => {
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [setupData, setSetupData] = useState<any>(null);
    const [verifyToken, setVerifyToken] = useState('');
    const [disablePassword, setDisablePassword] = useState('');
    const [disableToken, setDisableToken] = useState('');
    const [showDisable, setShowDisable] = useState(false);
    const [showBackupCodes, setShowBackupCodes] = useState(false);
    const [backupCodes, setBackupCodes] = useState<any>(null);
    const [regenToken, setRegenToken] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        loadStatus();
    }, []);

    const loadStatus = async () => {
        try {
            const data = await api.get2FAStatus();
            setStatus(data);
        } catch (error) {
            console.error('Failed to load 2FA status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSetup = async () => {
        setActionLoading(true);
        try {
            const data = await api.setup2FA();
            setSetupData(data);
        } catch (error: any) {
            toast.error(error.response?.data?.error || 'Failed to start 2FA setup');
        } finally {
            setActionLoading(false);
        }
    };

    const handleVerifySetup = async (e: React.FormEvent) => {
        e.preventDefault();
        setActionLoading(true);
        try {
            const result = await api.verifySetup2FA({ token: verifyToken, secret: setupData.secret });
            toast.success('Two-factor authentication enabled!');
            setSetupData(null);
            setVerifyToken('');

            // Show backup codes
            if (result.backup_codes) {
                setBackupCodes(result.backup_codes);
                setShowBackupCodes(true);
            }

            loadStatus();
        } catch (error: any) {
            toast.error(error.response?.data?.error || 'Invalid verification code');
        } finally {
            setActionLoading(false);
        }
    };

    const handleDisable = async (e: React.FormEvent) => {
        e.preventDefault();
        setActionLoading(true);
        try {
            await api.disable2FA({ password: disablePassword, token: disableToken });
            toast.success('Two-factor authentication disabled');
            setShowDisable(false);
            setDisablePassword('');
            setDisableToken('');
            loadStatus();
        } catch (error: any) {
            toast.error(error.response?.data?.error || 'Failed to disable 2FA');
        } finally {
            setActionLoading(false);
        }
    };

    const handleViewBackupCodes = async () => {
        try {
            const data = await api.getBackupCodes();
            setBackupCodes(data);
            setShowBackupCodes(true);
        } catch (error) {
            toast.error('Failed to load backup codes');
        }
    };

    const handleRegenerateBackupCodes = async (e: React.FormEvent) => {
        e.preventDefault();
        setActionLoading(true);
        try {
            const data = await api.regenerateBackupCodes(regenToken);
            setBackupCodes(data.backup_codes || data);
            setRegenToken('');
            toast.success('Backup codes regenerated');
        } catch (error: any) {
            toast.error(error.response?.data?.error || 'Failed to regenerate codes');
        } finally {
            setActionLoading(false);
        }
    };

    const copyBackupCodes = () => {
        if (!backupCodes) return;
        const codes = Array.isArray(backupCodes)
            ? backupCodes.join('\n')
            : typeof backupCodes === 'object'
                ? JSON.stringify(backupCodes, null, 2)
                : String(backupCodes);
        navigator.clipboard.writeText(codes);
        toast.success('Backup codes copied to clipboard');
    };

    if (loading) {
        return (
            <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-neutral-200 dark:bg-neutral-800 rounded w-1/3"></div>
                    <div className="h-4 bg-neutral-200 dark:bg-neutral-800 rounded w-2/3"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-xl ${status?.two_factor_enabled ? 'bg-green-100 dark:bg-green-900/30' : 'bg-neutral-100 dark:bg-neutral-800'}`}>
                        {status?.two_factor_enabled ? (
                            <ShieldCheck className="w-6 h-6 text-green-600 dark:text-green-400" />
                        ) : (
                            <Shield className="w-6 h-6 text-neutral-500 dark:text-neutral-400" />
                        )}
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-neutral-900 dark:text-white">
                            Two-Factor Authentication
                        </h3>
                        <p className="text-sm text-neutral-600 dark:text-neutral-400">
                            {status?.two_factor_enabled
                                ? 'Enabled — your account has extra security'
                                : 'Add an extra layer of security to your account'}
                        </p>
                    </div>
                </div>

                {status?.two_factor_enabled ? (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                        Active
                    </span>
                ) : (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400">
                        Disabled
                    </span>
                )}
            </div>

            {/* Setup Flow */}
            {!status?.two_factor_enabled && !setupData && (
                <button
                    onClick={handleSetup}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
                >
                    <Shield className="w-4 h-4" />
                    {actionLoading ? 'Setting up...' : 'Enable 2FA'}
                </button>
            )}

            {/* QR Code + Verify */}
            {setupData && (
                <div className="space-y-6 mt-4">
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-xl">
                        <p className="text-sm text-blue-800 dark:text-blue-300">
                            Scan the QR code below with your authenticator app (Google Authenticator, Authy, etc.), then enter the 6-digit code.
                        </p>
                    </div>

                    {setupData.qr_code && (
                        <div className="flex justify-center">
                            <div className="p-4 bg-white rounded-2xl shadow-inner border border-neutral-200">
                                <img src={setupData.qr_code} alt="QR Code" className="w-48 h-48" />
                            </div>
                        </div>
                    )}

                    {setupData.secret && (
                        <div className="text-center">
                            <p className="text-xs text-neutral-500 mb-1">Or enter this key manually:</p>
                            <code className="text-sm font-mono bg-neutral-100 dark:bg-neutral-800 px-3 py-1.5 rounded-lg text-neutral-900 dark:text-white select-all">
                                {setupData.secret}
                            </code>
                        </div>
                    )}

                    {setupData.backup_codes && (
                        <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-xl">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                                <span className="text-sm font-semibold text-amber-800 dark:text-amber-300">Save these backup codes!</span>
                            </div>
                            <p className="text-xs text-amber-700 dark:text-amber-400 mb-3">
                                Store them somewhere safe. Each code can only be used once.
                            </p>
                            <div className="grid grid-cols-2 gap-2">
                                {setupData.backup_codes.map((code: string, i: number) => (
                                    <code key={i} className="text-xs font-mono bg-white dark:bg-neutral-800 px-2 py-1 rounded text-center">
                                        {code}
                                    </code>
                                ))}
                            </div>
                            <button
                                onClick={() => {
                                    navigator.clipboard.writeText(setupData.backup_codes.join('\n'));
                                    toast.success('Backup codes copied');
                                }}
                                className="mt-3 inline-flex items-center gap-1.5 text-xs text-amber-700 dark:text-amber-400 hover:underline"
                            >
                                <Copy className="w-3 h-3" /> Copy all codes
                            </button>
                        </div>
                    )}

                    <form onSubmit={handleVerifySetup} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                                Verification Code
                            </label>
                            <input
                                type="text"
                                className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all text-center text-xl tracking-[0.4em] font-mono"
                                placeholder="000000"
                                value={verifyToken}
                                onChange={(e) => setVerifyToken(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                maxLength={6}
                                required
                            />
                        </div>
                        <div className="flex gap-3">
                            <button
                                type="submit"
                                disabled={actionLoading || verifyToken.length < 6}
                                className="flex-1 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
                            >
                                {actionLoading ? 'Verifying...' : 'Verify & Enable'}
                            </button>
                            <button
                                type="button"
                                onClick={() => { setSetupData(null); setVerifyToken(''); }}
                                className="px-5 py-2.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-xl font-medium hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Enabled State: Actions */}
            {status?.two_factor_enabled && !setupData && (
                <div className="space-y-4 mt-4">
                    <div className="flex flex-wrap gap-3">
                        <button
                            onClick={handleViewBackupCodes}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg text-sm font-medium hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                        >
                            <Eye className="w-4 h-4" />
                            View Backup Codes
                        </button>
                        <button
                            onClick={() => setShowDisable(!showDisable)}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                        >
                            <ShieldOff className="w-4 h-4" />
                            Disable 2FA
                        </button>
                    </div>

                    {/* Backup Codes Display */}
                    {showBackupCodes && backupCodes && (
                        <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 border border-neutral-200 dark:border-neutral-700 rounded-xl">
                            <div className="flex items-center justify-between mb-3">
                                <h4 className="text-sm font-semibold text-neutral-900 dark:text-white">Backup Codes</h4>
                                <div className="flex gap-2">
                                    <button onClick={copyBackupCodes} className="text-xs text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1">
                                        <Copy className="w-3 h-3" /> Copy
                                    </button>
                                    <button onClick={() => setShowBackupCodes(false)} className="text-xs text-neutral-500 hover:text-neutral-700">
                                        <EyeOff className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>
                            {backupCodes.remaining_codes !== undefined ? (
                                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                                    {backupCodes.remaining_codes} of {backupCodes.total_codes} backup codes remaining
                                </p>
                            ) : Array.isArray(backupCodes) ? (
                                <div className="grid grid-cols-2 gap-2">
                                    {backupCodes.map((code: string, i: number) => (
                                        <code key={i} className="text-xs font-mono bg-white dark:bg-neutral-800 px-2 py-1 rounded text-center border">
                                            {code}
                                        </code>
                                    ))}
                                </div>
                            ) : null}

                            {/* Regenerate */}
                            <form onSubmit={handleRegenerateBackupCodes} className="mt-4 flex gap-2">
                                <input
                                    type="text"
                                    className="flex-1 px-3 py-2 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg text-sm text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                                    placeholder="Enter 2FA code to regenerate"
                                    value={regenToken}
                                    onChange={(e) => setRegenToken(e.target.value)}
                                />
                                <button
                                    type="submit"
                                    disabled={actionLoading || regenToken.length < 6}
                                    className="inline-flex items-center gap-1.5 px-3 py-2 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg text-sm font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-colors disabled:opacity-50"
                                >
                                    <RefreshCw className="w-3.5 h-3.5" />
                                    Regenerate
                                </button>
                            </form>
                        </div>
                    )}

                    {/* Disable 2FA Form */}
                    {showDisable && (
                        <form onSubmit={handleDisable} className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-xl space-y-4">
                            <p className="text-sm text-red-800 dark:text-red-300">
                                To disable two-factor authentication, enter your password and current authenticator code.
                            </p>
                            <input
                                type="password"
                                className="w-full px-4 py-2.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-sm text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                placeholder="Current password"
                                value={disablePassword}
                                onChange={(e) => setDisablePassword(e.target.value)}
                                required
                            />
                            <input
                                type="text"
                                className="w-full px-4 py-2.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-sm text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent text-center tracking-widest font-mono"
                                placeholder="6-digit code"
                                value={disableToken}
                                onChange={(e) => setDisableToken(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                maxLength={6}
                                required
                            />
                            <div className="flex gap-3">
                                <button
                                    type="submit"
                                    disabled={actionLoading}
                                    className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-50"
                                >
                                    {actionLoading ? 'Disabling...' : 'Disable 2FA'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => { setShowDisable(false); setDisablePassword(''); setDisableToken(''); }}
                                    className="px-4 py-2.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-xl text-sm font-medium hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            )}
        </div>
    );
};
