import { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Check, ArrowRight, Sparkles, Zap, TrendingUp, Crown,
  Star, Award, CheckCircle2, Shield, Infinity, Globe,
  Rocket, Users, AlertCircle, RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../utils/api';
import { useSubscription } from '../../hooks/useSubscription';
import {
  formatPrice, calculateSavings, getPlanFeatures,
  isPopularPlan, isBestValuePlan, isFreePlan
} from '../../lib/pricing';
import type { Plan, BillingCycle, CurrencyConversion } from '../../types/payments';

// ── Plan icon mapping ──────────────────────────────────────────────────────
const getPlanIcon = (name: string) => {
  const n = name.toLowerCase();
  if (n === 'free' || n === 'starter') return Sparkles;
  if (n === 'pro') return Zap;
  if (n === 'business') return TrendingUp;
  if (n === 'enterprise') return Crown;
  return Star;
};

// ── Billing toggle ─────────────────────────────────────────────────────────
const BillingToggle = ({
  value, onChange
}: { value: BillingCycle; onChange: (v: BillingCycle) => void }) => (
  <div className="inline-flex items-center gap-1 p-1 rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 shadow-sm">
    {(['monthly', 'annual'] as BillingCycle[]).map(cycle => (
      <button
        key={cycle}
        id={`billing-toggle-${cycle}`}
        onClick={() => onChange(cycle)}
        className={`
          relative px-6 py-2 rounded-lg text-sm font-medium transition-all duration-200
          ${value === cycle
            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/30'
            : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-800 dark:hover:text-white'
          }
        `}
      >
        {cycle === 'monthly' ? 'Monthly' : 'Annual'}
        {cycle === 'annual' && (
          <span className={`
            ml-2 px-1.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide
            ${value === 'annual' ? 'bg-emerald-400/20 text-emerald-200' : 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400'}
          `}>
            Save 20%
          </span>
        )}
      </button>
    ))}
  </div>
);

// ── Skeleton card ──────────────────────────────────────────────────────────
const PlanCardSkeleton = () => (
  <div className="rounded-2xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-8 animate-pulse">
    <div className="w-10 h-10 rounded-xl bg-neutral-200 dark:bg-neutral-700 mb-6" />
    <div className="h-6 w-24 bg-neutral-200 dark:bg-neutral-700 rounded mb-3" />
    <div className="h-4 w-36 bg-neutral-100 dark:bg-neutral-800 rounded mb-8" />
    <div className="h-10 w-28 bg-neutral-200 dark:bg-neutral-700 rounded mb-6" />
    <div className="space-y-3">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-4 bg-neutral-100 dark:bg-neutral-800 rounded w-full" />
      ))}
    </div>
    <div className="h-12 bg-neutral-200 dark:bg-neutral-700 rounded-xl mt-8" />
  </div>
);

// ── Main PricingPage ───────────────────────────────────────────────────────
export const PricingPage = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');

  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<BillingCycle>('monthly');
  const [currency, setCurrency] = useState<CurrencyConversion | null>(null);

  const {
    currentSubscription,
    isCurrentPlan,
    isDowngrade,
    canPurchasePlan,
    getPlanButtonText,
  } = useSubscription();

  const exchangeRate = currency?.exchange_rate ?? 1;
  const currencySymbol = currency?.currency_symbol ?? '$';

  // Fetch plans
  useEffect(() => {
    const load = async () => {
      try {
        setError(null);
        const data = await api.getPlans();
        const planList: Plan[] = data?.plans ?? (Array.isArray(data) ? data : []);
        setPlans(planList);
      } catch {
        setError('Failed to load plans. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Fetch currency conversion (only for logged-in users)
  useEffect(() => {
    if (!isAuthenticated) return;
    api.convertCurrency(1).then(data => {
      if (data?.conversion_success) setCurrency(data);
    }).catch(() => {});
  }, [isAuthenticated]);

  // Build computed plan data
  const computedPlans = useMemo(() => plans.map(plan => {
    const PlanIcon = getPlanIcon(plan.name);
    const isPlanPopular = isPopularPlan(plan);
    const isPlanBestValue = isBestValuePlan(plan);
    const isPlanFree = isFreePlan(plan);
    const isActivePlan = isCurrentPlan(plan, billingCycle);
    const isPlanDowngrade = isDowngrade(plan, billingCycle);
    const canPurchase = canPurchasePlan(plan, billingCycle);
    const features = getPlanFeatures(plan);
    const buttonText = getPlanButtonText(plan, billingCycle);

    const displayPrice = billingCycle === 'annual' && plan.annual_price
      ? formatPrice(plan.annual_price, exchangeRate, currencySymbol)
      : formatPrice(plan.monthly_price, exchangeRate, currencySymbol);

    const perMonthNote = billingCycle === 'annual' && plan.annual_price
      ? `${currencySymbol}${Math.round(parseFloat(plan.annual_price) * exchangeRate / 12)}/mo billed annually`
      : null;

    const savings = billingCycle === 'annual' && plan.annual_price && parseFloat(plan.monthly_price) > 0
      ? calculateSavings(plan.monthly_price, plan.annual_price)
      : null;

    return {
      ...plan,
      computed: {
        PlanIcon, isPlanPopular, isPlanBestValue, isPlanFree,
        isActivePlan, isPlanDowngrade, canPurchase,
        features, buttonText, displayPrice, perMonthNote, savings
      }
    };
  }), [plans, billingCycle, exchangeRate, currencySymbol, isCurrentPlan, isDowngrade, canPurchasePlan, getPlanButtonText]);

  const handlePlanClick = (plan: Plan, canPurchase: boolean) => {
    if (plan.requires_admin_approval) {
      navigate('/contact');
      return;
    }
    if (!isAuthenticated) {
      navigate('/auth');
      return;
    }
    if (!canPurchase) {
      toast.error('You cannot downgrade to this plan directly.');
      return;
    }
    if (isFreePlan(plan)) {
      toast('You are already on the Free plan or it requires no payment.', { icon: 'ℹ️' });
      return;
    }
    navigate(`/checkout?plan=${plan.name}&cycle=${billingCycle}`);
  };

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      {/* ── Hero ── */}
      <div className="relative overflow-hidden">

        <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-16 text-center">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 mb-6">
            <Sparkles className="w-3 h-3" />
            Transparent pricing, no hidden fees
          </span>

          <h1 className="text-5xl md:text-6xl font-bold text-neutral-900 dark:text-white mb-5 leading-tight">
            Simple, honest{' '}
            <span className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              pricing
            </span>
          </h1>

          <p className="text-lg text-neutral-500 dark:text-neutral-400 mb-10 max-w-2xl mx-auto">
            Start free and scale as you grow. Every plan includes our core automation engine — no credit card required to start.
          </p>

          <BillingToggle value={billingCycle} onChange={setBillingCycle} />

          {isAuthenticated && currency && currency.local_currency !== 'USD' && (
            <p className="mt-3 text-xs text-neutral-400">
              Prices shown in {currency.local_currency} · 1 USD = {currency.exchange_rate.toFixed(2)} {currency.local_currency}
            </p>
          )}
        </div>
      </div>

      {/* ── Plan Grid ── */}
      <div className="max-w-7xl mx-auto px-6 pb-24">
        {error ? (
          <div className="max-w-md mx-auto text-center py-16">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400 mb-4">{error}</p>
            <button
              id="retry-load-plans"
              onClick={() => { setLoading(true); setError(null); api.getPlans().then(d => setPlans(d?.plans ?? [])).catch(() => setError('Failed again.')).finally(() => setLoading(false)); }}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" /> Try Again
            </button>
          </div>
        ) : (
          <div className={`grid gap-6 ${computedPlans.length <= 3 ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'} max-w-7xl mx-auto`}>
            {loading
              ? [...Array(3)].map((_, i) => <PlanCardSkeleton key={i} />)
              : computedPlans.map(plan => {
                  const {
                    PlanIcon, isPlanPopular, isPlanBestValue, isActivePlan,
                    canPurchase, features, buttonText, displayPrice, perMonthNote, savings
                  } = plan.computed;

                  return (
                    <div
                      key={plan.id}
                      className={`
                        relative flex flex-col rounded-2xl border transition-all duration-300
                        ${isActivePlan
                          ? 'border-emerald-500 dark:border-emerald-500 shadow-xl shadow-emerald-500/10 ring-2 ring-emerald-500/20'
                          : isPlanPopular
                            ? 'border-indigo-500 dark:border-indigo-500 shadow-2xl shadow-indigo-500/15 scale-[1.02]'
                            : isPlanBestValue
                              ? 'border-purple-400 dark:border-purple-600 shadow-xl shadow-purple-500/10'
                              : 'border-neutral-200 dark:border-neutral-700 shadow-sm hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-lg'
                        }
                        bg-white dark:bg-neutral-900
                        ${!canPurchase && !isActivePlan ? 'opacity-70' : ''}
                      `}
                    >
                      {/* Badge */}
                      {(isActivePlan || isPlanPopular || isPlanBestValue) && (
                        <div className={`
                          absolute -top-3.5 left-1/2 -translate-x-1/2
                          px-4 py-1 rounded-full text-xs font-bold flex items-center gap-1.5
                          ${isActivePlan
                            ? 'bg-emerald-500 text-white'
                            : isPlanPopular
                              ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white'
                              : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                          }
                        `}>
                          {isActivePlan && <><CheckCircle2 className="w-3 h-3" /> Current Plan</>}
                          {!isActivePlan && isPlanPopular && <><Star className="w-3 h-3" /> Most Popular</>}
                          {!isActivePlan && isPlanBestValue && <><Award className="w-3 h-3" /> Best Value</>}
                        </div>
                      )}

                      <div className="p-8 flex flex-col flex-1">
                        {/* Icon + Name */}
                        <div className={`
                          w-12 h-12 rounded-xl flex items-center justify-center mb-5
                          ${isPlanPopular
                            ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400'
                            : isPlanBestValue
                              ? 'bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400'
                              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'
                          }
                        `}>
                          <PlanIcon className="w-6 h-6" />
                        </div>

                        <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-1">
                          {plan.display_name || plan.name}
                        </h3>
                        <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-6 min-h-[40px]">
                          {plan.description}
                        </p>

                        {/* Price */}
                        <div className="mb-6">
                          <div className="flex items-end gap-1">
                            <span className="text-4xl font-bold text-neutral-900 dark:text-white">
                              {displayPrice}
                            </span>
                            {parseFloat(plan.monthly_price) > 0 && (
                              <span className="text-sm text-neutral-400 mb-1">
                                /{billingCycle === 'annual' ? 'yr' : 'mo'}
                              </span>
                            )}
                          </div>
                          {perMonthNote && (
                            <p className="text-xs text-neutral-400 mt-1">{perMonthNote}</p>
                          )}
                          {savings && savings.amount > 0 && (
                            <span className="inline-flex mt-2 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400">
                              Save {savings.percentage}% annually
                            </span>
                          )}
                        </div>

                        {/* Features */}
                        <ul className="space-y-2.5 mb-8 flex-1">
                          {features.map((f, i) => (
                            <li key={i} className="flex items-start gap-3 text-sm">
                              <div className={`
                                mt-0.5 w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0
                                ${isPlanPopular ? 'bg-indigo-100 dark:bg-indigo-900/50' : 'bg-neutral-100 dark:bg-neutral-800'}
                              `}>
                                <Check className={`w-2.5 h-2.5 ${isPlanPopular ? 'text-indigo-600 dark:text-indigo-400' : 'text-neutral-600 dark:text-neutral-400'}`} />
                              </div>
                              <span className="text-neutral-600 dark:text-neutral-300">{f}</span>
                            </li>
                          ))}
                        </ul>

                        {/* CTA */}
                        <button
                          id={`plan-cta-${plan.name}`}
                          onClick={() => handlePlanClick(plan, canPurchase)}
                          disabled={isActivePlan || (!canPurchase && !isFreePlan(plan))}
                          className={`
                            w-full py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-200
                            flex items-center justify-center gap-2
                            ${isActivePlan
                              ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 cursor-default'
                              : !canPurchase
                                ? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-400 cursor-not-allowed'
                                : isPlanPopular
                                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:from-indigo-600 hover:to-purple-700 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5'
                                  : isPlanBestValue
                                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:from-purple-600 hover:to-pink-600 shadow-lg shadow-purple-500/25 hover:-translate-y-0.5'
                                    : 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-700 dark:hover:bg-neutral-100 hover:-translate-y-0.5'
                            }
                          `}
                        >
                          {buttonText}
                          {canPurchase && !isActivePlan && <ArrowRight className="w-4 h-4" />}
                          {isActivePlan && <CheckCircle2 className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  );
                })}

            {/* Enterprise card — always shown */}
            {!loading && (
              <div className="relative flex flex-col rounded-2xl border border-amber-200 dark:border-amber-800 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-neutral-900 dark:to-neutral-900 shadow-xl shadow-amber-500/10">
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white">
                  <Crown className="w-3 h-3" /> Enterprise
                </div>
                <div className="p-8 flex flex-col flex-1">
                  <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center mb-5">
                    <Crown className="w-6 h-6 text-amber-600 dark:text-amber-400" />
                  </div>
                  <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-1">Enterprise</h3>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-6 min-h-[40px]">
                    For large teams and agencies with custom requirements
                  </p>
                  <div className="mb-6">
                    <span className="text-4xl font-bold text-neutral-900 dark:text-white">Custom</span>
                    <p className="text-xs text-neutral-400 mt-1">Contact us for pricing</p>
                  </div>
                  <ul className="space-y-2.5 mb-8 flex-1">
                    {['Unlimited automations & DMs', 'White-label solution', 'Dedicated account manager', '24/7 priority support', 'Custom integrations & API', 'Multi-account management'].map((f, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm">
                        <div className="mt-0.5 w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 bg-amber-100 dark:bg-amber-900/40">
                          <Check className="w-2.5 h-2.5 text-amber-600 dark:text-amber-400" />
                        </div>
                        <span className="text-neutral-600 dark:text-neutral-300">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Link
                    to="/contact"
                    id="plan-cta-enterprise"
                    className="w-full py-3 px-6 rounded-xl font-semibold text-sm bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-600 hover:to-orange-600 shadow-lg shadow-amber-500/25 hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center gap-2"
                  >
                    Contact Sales <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Trust badges ── */}
      <div className="border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
        <div className="max-w-4xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { icon: Shield, label: 'Secure Payments', sub: '256-bit SSL encryption' },
            { icon: Infinity, label: 'Cancel Anytime', sub: 'No lock-in contracts' },
            { icon: Globe, label: 'Global Support', sub: '24/7 customer service' },
            { icon: Rocket, label: 'Instant Activation', sub: 'Start automating immediately' },
          ].map(({ icon: Icon, label, sub }) => (
            <div key={label} className="group">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                <Icon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <h4 className="font-semibold text-neutral-900 dark:text-white text-sm mb-0.5">{label}</h4>
              <p className="text-xs text-neutral-400">{sub}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── FAQ ── */}
      <div className="max-w-3xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-neutral-900 dark:text-white text-center mb-2">FAQ</h2>
        <p className="text-neutral-400 text-center mb-10">Everything you need to know about our plans</p>
        <div className="space-y-3">
          {[
            { q: 'Can I change plans anytime?', a: "Yes. Upgrades take effect immediately with prorated billing. Downgrades are scheduled for your next billing cycle." },
            { q: 'What payment methods do you accept?', a: "We accept all major credit/debit cards, UPI, net banking, and digital wallets via Razorpay." },
            { q: 'Is there a free plan?', a: "Yes — the Free plan is free forever. No credit card required. You get 2 automations and 500 DMs/month." },
            { q: 'What happens if I exceed my DM limit?', a: "Your automations pause automatically. Upgrade your plan or wait for your next billing cycle." },
            { q: 'Do you offer refunds?', a: "We offer a 14-day money-back guarantee for all paid plans. No questions asked." },
          ].map(({ q, a }) => (
            <details
              key={q}
              className="group rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 overflow-hidden"
            >
              <summary className="flex items-center justify-between p-5 cursor-pointer font-medium text-neutral-900 dark:text-white list-none">
                <span>{q}</span>
                <span className="text-neutral-400 group-open:rotate-180 transition-transform text-lg leading-none">›</span>
              </summary>
              <p className="px-5 pb-5 text-sm text-neutral-500 dark:text-neutral-400 border-t border-neutral-100 dark:border-neutral-800 pt-4 mt-0">
                {a}
              </p>
            </details>
          ))}
        </div>
      </div>

      {/* ── Bottom CTA ── */}
      <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600">
        <div className="max-w-3xl mx-auto px-6 py-16 text-center">
          <Sparkles className="w-10 h-10 text-white/80 mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-3">Still have questions?</h2>
          <p className="text-indigo-200 mb-8">Our team is happy to help you pick the right plan.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/contact"
              className="px-8 py-3 rounded-xl bg-white text-indigo-600 font-semibold hover:bg-indigo-50 transition-colors shadow-lg"
            >
              Contact us
            </Link>
            <Link
              to="/auth"
              className="px-8 py-3 rounded-xl bg-white/10 text-white font-semibold hover:bg-white/20 transition-colors border border-white/20"
            >
              Start for free
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
