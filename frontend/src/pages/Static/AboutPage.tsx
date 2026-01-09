import { Heart, Target, Users, Sparkles } from 'lucide-react';

export const AboutPage = () => {
  return (
    <div className="min-h-screen bg-[var(--bg-secondary)]">
      {/* Header */}
      <div className="border-b border-[var(--border-primary)] bg-[var(--bg-primary)]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-[var(--text-primary)] mb-4">
            We're Building the Future of Instagram Automation
          </h1>
          <p className="text-xl text-[var(--text-secondary)] max-w-3xl mx-auto">
            LinkPlease Pro helps businesses automate Instagram DMs with AI-powered
            personalization, saving time and increasing conversions.
          </p>
        </div>

        {/* Mission */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16">
          <div className="card">
            <div className="inline-flex p-3 rounded-xl bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 mb-4">
              <Target className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-4">
              Our Mission
            </h2>
            <p className="text-[var(--text-secondary)] leading-relaxed">
              To empower businesses of all sizes to engage with their Instagram audience
              authentically and efficiently through intelligent automation. We believe
              every comment deserves a response, and every interaction should feel
              personal.
            </p>
          </div>

          <div className="card">
            <div className="inline-flex p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 mb-4">
              <Heart className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-4">
              Our Values
            </h2>
            <ul className="space-y-2 text-[var(--text-secondary)]">
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <span>Authenticity in every automated interaction</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <span>Privacy and security first</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <span>Continuous innovation with AI</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-16">
          <StatCard value="10,000+" label="Active Users" />
          <StatCard value="5M+" label="DMs Sent" />
          <StatCard value="67%" label="Avg. Conversion Increase" />
          <StatCard value="99.9%" label="Uptime" />
        </div>

        {/* Team */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
            Powered by AI Excellence
          </h2>
          <p className="text-[var(--text-secondary)] max-w-2xl mx-auto">
            We use Claude AI by Anthropic to deliver the most advanced message
            personalization technology available.
          </p>
        </div>

        <div className="card text-center max-w-2xl mx-auto bg-gradient-to-br from-purple-500 to-pink-500 text-white">
          <Sparkles className="w-16 h-16 mx-auto mb-4" />
          <h3 className="text-2xl font-bold mb-2">Built with Claude AI</h3>
          <p className="text-white/90">
            Every message is crafted with care using state-of-the-art AI to ensure
            authentic, personalized communication with your audience.
          </p>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ value, label }: { value: string; label: string }) => (
  <div className="card text-center">
    <div className="text-4xl font-bold text-[var(--accent-primary)] mb-2">{value}</div>
    <div className="text-[var(--text-secondary)]">{label}</div>
  </div>
);
