import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, Zap, Crown, Rocket, ArrowLeft } from 'lucide-react';

export const PricingPage = () => {
  const [billing, setBilling] = useState<'monthly' | 'annual'>('monthly');

  const plans = [
    {
      name: 'Free',
      icon: <Zap className="w-8 h-8" />,
      price: { monthly: 0, annual: 0 },
      description: 'Perfect for getting started',
      features: [
        '2 active automations',
        '500 DMs per month',
        'Basic analytics',
        'Email support',
        'Comment replies',
      ],
      cta: 'Get Started Free',
      highlighted: false,
    },
    {
      name: 'Pro',
      icon: <Crown className="w-8 h-8" />,
      price: { monthly: 29, annual: 290 },
      description: 'For growing businesses',
      features: [
        '10 active automations',
        '5,000 DMs per month',
        'Advanced analytics',
        'Priority support',
        'AI-powered personalization',
        'A/B testing',
        'Custom branding',
      ],
      cta: 'Start Pro Trial',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      icon: <Rocket className="w-8 h-8" />,
      price: { monthly: 99, annual: 990 },
      description: 'For large-scale operations',
      features: [
        'Unlimited automations',
        'Unlimited DMs',
        'White-label solution',
        'Dedicated support',
        'Custom integrations',
        'Advanced AI features',
        'Multi-account management',
        'API access',
      ],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  return (
    <div className="min-h-screen bg-[neutral-50 dark:bg-neutral-800]">
      {/* Header */}
      <div className="border-b border-[neutral-200 dark:border-neutral-800] bg-[white dark:bg-neutral-900]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-[neutral-600 dark:text-neutral-400] hover:text-[neutral-900 dark:text-white]"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-[neutral-900 dark:text-white] mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-[neutral-600 dark:text-neutral-400] mb-8">
            Choose the perfect plan for your Instagram automation needs
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center gap-4 p-2 bg-[white dark:bg-neutral-900] rounded-lg border border-[neutral-200 dark:border-neutral-800]">
            <button
              onClick={() => setBilling('monthly')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                billing === 'monthly'
                  ? 'bg-[neutral-900 dark:text-white] text-white'
                  : 'text-[neutral-600 dark:text-neutral-400]'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBilling('annual')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                billing === 'annual'
                  ? 'bg-[neutral-900 dark:text-white] text-white'
                  : 'text-[neutral-600 dark:text-neutral-400]'
              }`}
            >
              Annual
              <span className="ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
                Save 17%
              </span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`card relative ${
                plan.highlighted
                  ? 'ring-2 ring-[neutral-900 dark:text-white] shadow-xl scale-105'
                  : ''
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-[neutral-900 dark:text-white] text-white text-sm font-medium rounded-full">
                  Most Popular
                </div>
              )}

              <div className="text-center mb-6">
                <div className="inline-flex p-3 rounded-xl bg-[var(--accent-light)] text-[neutral-900 dark:text-white] mb-4">
                  {plan.icon}
                </div>
                <h3 className="text-2xl font-bold text-[neutral-900 dark:text-white] mb-2">
                  {plan.name}
                </h3>
                <p className="text-[neutral-600 dark:text-neutral-400]">{plan.description}</p>
              </div>

              <div className="text-center mb-6">
                <div className="text-5xl font-bold text-[neutral-900 dark:text-white] mb-2">
                  ${plan.price[billing]}
                  <span className="text-xl text-[neutral-600 dark:text-neutral-400] font-normal">
                    /{billing === 'monthly' ? 'mo' : 'yr'}
                  </span>
                </div>
                {billing === 'annual' && plan.price.annual > 0 && (
                  <p className="text-sm text-[neutral-500]">
                    ${(plan.price.annual / 12).toFixed(2)}/mo billed annually
                  </p>
                )}
              </div>

              <Link
                to={plan.name === 'Enterprise' ? '/contact' : '/auth'}
                className={`block w-full text-center py-3 px-6 rounded-lg font-medium transition-all mb-6 ${
                  plan.highlighted
                    ? 'bg-[neutral-900 dark:text-white] text-white hover:bg-[var(--accent-hover)]'
                    : 'bg-[neutral-50 dark:bg-neutral-800] text-[neutral-900 dark:text-white] hover:bg-[neutral-50 dark:hover:bg-neutral-800]'
                }`}
              >
                {plan.cta}
              </Link>

              <ul className="space-y-3">
                {plan.features.map((feature) => (
                  <li
                    key={feature}
                    className="flex items-start gap-3 text-[neutral-600 dark:text-neutral-400]"
                  >
                    <Check className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-[neutral-900 dark:text-white] text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            <FAQItem
              question="Can I change plans anytime?"
              answer="Yes, you can upgrade or downgrade your plan at any time. Changes will be reflected in your next billing cycle."
            />
            <FAQItem
              question="What happens if I exceed my DM limit?"
              answer="Your automations will pause automatically. You can upgrade your plan or wait for the next billing cycle to reset your limit."
            />
            <FAQItem
              question="Do you offer refunds?"
              answer="Yes, we offer a 14-day money-back guarantee for all paid plans. No questions asked."
            />
            <FAQItem
              question="Can I try Pro features before purchasing?"
              answer="Absolutely! We offer a 7-day free trial of the Pro plan with no credit card required."
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const FAQItem = ({ question, answer }: { question: string; answer: string }) => (
  <details className="card group">
    <summary className="cursor-pointer font-medium text-[neutral-900 dark:text-white] list-none flex items-center justify-between">
      <span>{question}</span>
      <span className="text-[neutral-500] group-open:rotate-180 transition-transform">
        ▼
      </span>
    </summary>
    <p className="mt-4 text-[neutral-600 dark:text-neutral-400]">{answer}</p>
  </details>
);

