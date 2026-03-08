import React from 'react';
import { Book, Shield, Scale, HelpCircle } from 'lucide-react';

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

export const TermsOfServicePage = () => {
    return (
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 font-sans text-neutral-900 dark:text-neutral-100">
            {/* Hero Section */}
            <div className="bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800">
                <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8 text-center">
                    <Book className="w-16 h-16 text-purple-600 mx-auto mb-6" />
                    <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
                        Terms of Service
                    </h1>
                    <p className="mt-4 text-xl text-neutral-500 dark:text-neutral-400">
                        Last updated: March 8, 2026
                    </p>
                    <p className="mt-4 text-lg text-neutral-600 dark:text-neutral-300 max-w-2xl mx-auto">
                        Please read these terms carefully before using DmMe. By using our service, you agree to these legal terms and conditions.
                    </p>
                </div>
            </div>

            {/* Content Section */}
            <div className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8 space-y-12">

                {/* 1. Agreement to Terms */}
                <section>
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <Scale className="w-6 h-6 text-purple-600" />
                        1. Agreement to Terms
                    </h2>
                    <Card>
                        <CardContent className="p-6 space-y-4 text-neutral-600 dark:text-neutral-300">
                            <p>
                                By accessing or using DmMe, you agree to be bound by these Terms of Service and all applicable laws and regulations. If you do not agree with any of these terms, you are prohibited from using or accessing this site.
                            </p>
                        </CardContent>
                    </Card>
                </section>

                {/* 2. Platform Usage & Restrictions */}
                <section>
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <Shield className="w-6 h-6 text-purple-600" />
                        2. Acceptable Use & Meta Policies
                    </h2>
                    <Card>
                        <CardContent className="p-6 space-y-4 text-neutral-600 dark:text-neutral-300">
                            <p>When using our Instagram integration, you agree to the following:</p>
                            <ul className="list-disc pl-6 space-y-2">
                                <li><strong>Comply with Meta API Terms:</strong> You must strictly adhere to the Meta Platform Terms and Instagram Community Guidelines.</li>
                                <li><strong>No Spam:</strong> You may not use this tool to send unsolicited spam, abusive, or misleading messages.</li>
                                <li><strong>Rate Limits:</strong> You accept that Meta enforces rate limits and that automated messages are subject to these upstream restrictions.</li>
                            </ul>
                        </CardContent>
                    </Card>
                </section>

                {/* 3. Account Termination */}
                <section>
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <HelpCircle className="w-6 h-6 text-purple-600" />
                        3. Account Suspension & Termination
                    </h2>
                    <Card>
                        <CardContent className="p-6 space-y-4 text-neutral-600 dark:text-neutral-300">
                            <p>
                                We reserve the right to suspend or terminate your account at any time, without notice, for conduct that violates these Terms of Service, particularly involving spam or breach of Meta's Developer Policies.
                            </p>
                        </CardContent>
                    </Card>
                </section>

            </div>
        </div>
    );
};
