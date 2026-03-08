import React from 'react';
import { Link } from 'react-router-dom';
import { Instagram, Book, Shield, Mail } from 'lucide-react';

export const Footer = () => {
    return (
        <footer className="bg-white dark:bg-neutral-900 border-t border-neutral-200 dark:border-neutral-800 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8">

                    {/* Brand Info */}
                    <div className="col-span-1 md:col-span-1">
                        <Link to="/" className="flex items-center gap-2 group mb-4">
                            <div className="p-1.5 rounded-lg bg-neutral-900 dark:bg-white group-hover:scale-105 transition-transform">
                                <Instagram className="w-5 h-5 text-white dark:text-neutral-900" />
                            </div>
                            <span className="text-lg font-semibold text-neutral-900 dark:text-white">
                                DmMe
                            </span>
                        </Link>
                        <p className="text-sm text-neutral-500 dark:text-neutral-400">
                            Automated Instagram DM outreach powered by intelligent triggers and seamless integration.
                        </p>
                    </div>

                    {/* Links - Product */}
                    <div>
                        <h3 className="text-sm font-semibold text-neutral-900 dark:text-white uppercase tracking-wider mb-4">
                            Product
                        </h3>
                        <ul className="space-y-3">
                            <li><Link to="/pricing" className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-purple-600 dark:hover:text-purple-400">Pricing</Link></li>
                            <li><Link to="/about" className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-purple-600 dark:hover:text-purple-400">About Us</Link></li>
                            <li><Link to="/contact" className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-purple-600 dark:hover:text-purple-400">Contact</Link></li>
                        </ul>
                    </div>

                    {/* Links - Legal */}
                    <div>
                        <h3 className="text-sm font-semibold text-neutral-900 dark:text-white uppercase tracking-wider mb-4">
                            Legal
                        </h3>
                        <ul className="space-y-3">
                            <li>
                                <Link to="/privacy-policy" className="flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400 hover:text-purple-600 dark:hover:text-purple-400">
                                    <Shield className="w-4 h-4" /> Privacy Policy
                                </Link>
                            </li>
                            <li>
                                <Link to="/terms-of-service" className="flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400 hover:text-purple-600 dark:hover:text-purple-400">
                                    <Book className="w-4 h-4" /> Terms of Service
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Contact */}
                    <div>
                        <h3 className="text-sm font-semibold text-neutral-900 dark:text-white uppercase tracking-wider mb-4">
                            Support
                        </h3>
                        <ul className="space-y-3">
                            <li>
                                <a href="mailto:support@linkauto.social" className="flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400 hover:text-purple-600 dark:hover:text-purple-400">
                                    <Mail className="w-4 h-4" /> Support
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="mt-12 pt-8 border-t border-neutral-200 dark:border-neutral-800 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-sm text-neutral-500 dark:text-neutral-400">
                        &copy; {new Date().getFullYear()} DmMe. All rights reserved.
                    </p>
                    <div className="flex gap-4">
                        <span className="text-xs text-neutral-400">Not affiliated with Instagram or Meta Platforms, Inc.</span>
                    </div>
                </div>
            </div>
        </footer>
    );
};
