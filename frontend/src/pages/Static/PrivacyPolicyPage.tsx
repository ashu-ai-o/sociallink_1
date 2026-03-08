import React from 'react';
import { Mail, Shield, Trash2, Database, Lock, Eye } from 'lucide-react';

const Card = ({ children, className = '' }: { children: React.ReactNode, className?: string }) => (
    <div className={`bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl shadow-sm overflow-hidden ${className}`}>
        {children}
    </div>
);

const CardContent = ({ children, className = '' }: { children: React.ReactNode, className?: string }) => (
    <div className={`p-6 ${className}`}>
        {children}
    </div>
);
export const PrivacyPolicyPage = () => {
    return (
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 font-sans text-neutral-900 dark:text-neutral-100">
            {/* Hero Section */}
            <div className="bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800">
                <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8 text-center">
                    <Shield className="w-16 h-16 text-purple-600 mx-auto mb-6" />
                    <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
                        Privacy Policy
                    </h1>
                    <p className="mt-4 text-xl text-neutral-500 dark:text-neutral-400">
                        Last updated: March 8, 2026
                    </p>
                    <p className="mt-4 text-lg text-neutral-600 dark:text-neutral-300 max-w-2xl mx-auto">
                        We are committed to protecting your privacy and ensuring your data is handled securely and transparently. This policy outlines how we collect, use, and safeguard your information.
                    </p>
                </div>
            </div>

            {/* Content Section */}
            <div className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8 space-y-12">

                {/* 1. Information We Collect */}
                <section>
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <Database className="w-6 h-6 text-purple-600" />
                        1. Information We Collect
                    </h2>
                    <Card>
                        <CardContent className="p-6 space-y-4 text-neutral-600 dark:text-neutral-300">
                            <p>When you use LinkSocial AutoDM, we collect the following types of information:</p>
                            <ul className="list-disc pl-6 space-y-2">
                                <li><strong>Account Information:</strong> Your email address, name, and basic profile details when you sign up.</li>
                                <li><strong>Platform Data (Instagram & Meta):</strong> When you connect your Instagram Professional account, we receive an access token, your Instagram Account ID, Media IDs, Usernames, and comments interactively associated with your automated campaigns.</li>
                                <li><strong>Usage Data:</strong> We log system interactions, errors, and automation analytics to improve our service.</li>
                            </ul>
                        </CardContent>
                    </Card>
                </section>

                {/* 2. How We Use Your Information */}
                <section>
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <Eye className="w-6 h-6 text-purple-600" />
                        2. How We Use Your Information
                    </h2>
                    <Card>
                        <CardContent className="p-6 space-y-4 text-neutral-600 dark:text-neutral-300">
                            <p>Your information is used strictly to provide and improve our services:</p>
                            <ul className="list-disc pl-6 space-y-2">
                                <li><strong>To trigger automations:</strong> We process incoming Instagram comments via Meta Webhooks to send automated Direct Messages based on your configuration.</li>
                                <li><strong>To communicate with you:</strong> We use your email to send account updates, system alerts, and customer support.</li>
                                <li><strong>Service improvement:</strong> We use aggregated analytics to enhance platform stability and user experience.</li>
                            </ul>
                            <p className="font-medium text-neutral-900 dark:text-neutral-100 mt-4">
                                We do not sell, rent, or monetize your personal data to third parties under any circumstances.
                            </p>
                        </CardContent>
                    </Card>
                </section>

                {/* 3. Data Protection and Security */}
                <section>
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <Lock className="w-6 h-6 text-purple-600" />
                        3. Data Protection and Security
                    </h2>
                    <Card>
                        <CardContent className="p-6 space-y-4 text-neutral-600 dark:text-neutral-300">
                            <p>
                                We use industry-standard security measures including SSL encryption, secure data hosting, and hashed database storage to protect your information. Access tokens provided by Meta are handled securely and are only used for the exact permissions you grant.
                            </p>
                        </CardContent>
                    </Card>
                </section>

                {/* 4. Data Deletion Instructions (Meta Requirement) */}
                <section id="data-deletion">
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <Trash2 className="w-6 h-6 text-purple-600" />
                        4. Data Deletion Instructions
                    </h2>
                    <Card className="border-red-200 dark:border-red-900/30">
                        <CardContent className="p-6 space-y-4 text-neutral-600 dark:text-neutral-300">
                            <p>
                                As required by the General Data Protection Regulation (GDPR) and Meta Platforms data policies, you have the absolute right to request the deletion of all your data from our servers.
                            </p>
                            <p className="font-semibold text-neutral-900 dark:text-white">How to delete your data:</p>
                            <ol className="list-decimal pl-6 space-y-3">
                                <li>
                                    <strong>Inside the Platform:</strong> Log into your Dashboard, go to Settings &gt; Account, and click the "Delete Account" button. All associated data, including Instagram connections, automations, and logs, will be permanently erased.
                                </li>
                                <li>
                                    <strong>Via Meta/Facebook:</strong> Go to your Facebook Account Settings &gt; Security and Login &gt; Business Integrations. Find our App, click "Remove", and you will be presented with a prompt to send us a Data Deletion Request. We process these requests automatically.
                                </li>
                                <li>
                                    <strong>Manual Request:</strong> You can email our Data Protection Officer at <a href="mailto:privacy@linkauto.social" className="text-purple-600 hover:underline">privacy@linkauto.social</a> with the subject "Data Deletion Request". We will comply within 72 hours.
                                </li>
                            </ol>
                        </CardContent>
                    </Card>
                </section>

                {/* 5. Contact Us */}
                <section>
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <Mail className="w-6 h-6 text-purple-600" />
                        5. Contact Us
                    </h2>
                    <Card>
                        <CardContent className="p-6 text-neutral-600 dark:text-neutral-300">
                            <p>
                                If you have any questions or concerns about this Privacy Policy, your data, or your rights, please contact us at:
                            </p>
                            <div className="mt-4 p-4 bg-neutral-100 dark:bg-neutral-800 rounded-lg inline-block">
                                <p className="font-medium text-neutral-900 dark:text-white">Privacy Team</p>
                                <a href="mailto:privacy@linkauto.social" className="text-purple-600 hover:underline">privacy@linkauto.social</a>
                            </div>
                        </CardContent>
                    </Card>
                </section>

            </div>
        </div>
    );
};
