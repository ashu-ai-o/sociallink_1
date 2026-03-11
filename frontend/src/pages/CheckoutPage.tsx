import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  ArrowLeft, CreditCard, Loader2, Check, Shield, Lock,
  Sparkles, Zap, AlertCircle, CheckCircle2, Wallet,
  Building2, Smartphone
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../utils/api';
import { useRazorpay } from '../hooks/useRazorpay';
import { formatPrice, calculateSavings, getPlanFeatures } from '../lib/pricing';
import { RAZORPAY_THEME } from '../lib/paymentConstants';
import type { Plan, BillingCycle, PaymentMethodType } from '../types/payments';

// ── Skeleton ───────────────────────────────────────────────────────────────
const CheckoutSkeleton = () => (
  <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 flex items-center justify-center">
    <div className="w-full max-w-5xl px-6 grid md:grid-cols-5 gap-8 animate-pulse">
      <div className="md:col-span-3 space-y-4">
        <div className="h-8 bg-neutral-200 dark:bg-neutral-800 rounded-xl w-48" />
        <div className="h-64 bg-neutral-200 dark:bg-neutral-800 rounded-2xl" />
      </div>
      <div className="md:col-span-2">
        <div className="h-80 bg-neutral-200 dark:bg-neutral-800 rounded-2xl" />
      </div>
    </div>
  </div>
);

// ── CheckoutPage ───────────────────────────────────────────────────────────
export const CheckoutPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isScriptLoaded, scriptError, openPayment } = useRazorpay();

  const planName = searchParams.get('plan');
  const cycleParm = searchParams.get('cycle');

  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [billingCycle, setBillingCycle] = useState<BillingCycle>(
    cycleParm === 'annual' ? 'annual' : 'monthly'
  );
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethodType>('card');
  const [isIndianUser, setIsIndianUser] = useState(false);

  const isAuthenticated = !!localStorage.getItem('access_token');

  // Redirect if not logged in
  useEffect(() => {
    if (!isAuthenticated) {
      toast.error('Please log in to continue');
      navigate('/auth');
    }
  }, [isAuthenticated, navigate]);

  // Fetch plan details
  useEffect(() => {
    if (!planName) { navigate('/pricing'); return; }
    const load = async () => {
      try {
        const data = await api.getPlans();
        const planList: Plan[] = data?.plans ?? (Array.isArray(data) ? data : []);
        const plan = planList.find(p => p.name === planName);
        if (plan) {
          setSelectedPlan(plan);
        } else {
          toast.error('Plan not found. Redirecting…');
          setTimeout(() => navigate('/pricing'), 2000);
        }
      } catch {
        toast.error('Failed to load plan details.');
        navigate('/pricing');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [planName, navigate]);

  // Show script errors from Razorpay
  useEffect(() => {
    if (scriptError) toast.error(scriptError);
  }, [scriptError]);

  // Fetch plan preview
  useEffect(() => {
    if (!selectedPlan) return;
    const getPreview = async () => {
      setPreviewLoading(true);
      try {
        const preview = await api.getSubscriptionChangePreview({
          plan_id: selectedPlan.id,
          billing_cycle: billingCycle
        });
        if (preview.success && preview.currency_details) {
          setPreviewData(preview);
          setIsIndianUser(['IN', 'LOCAL'].includes(preview.location_detected));
        }
      } catch (err) {
        console.error('Failed to get plan preview details:', err);
      } finally {
        setPreviewLoading(false);
      }
    };
    getPreview();
  }, [selectedPlan, billingCycle]);

  // Memoised checkout totals
  const { features, displayPrice, savings, totalDisplay, taxUsd } = useMemo(() => {
    if (!selectedPlan) return { features: [], displayPrice: '', savings: null, totalDisplay: '', taxUsd: 0 };

    const features = getPlanFeatures(selectedPlan);

    // Always use USD format for the frontend checkout screen
    let displayPrice = '';
    let totalDisplay = '';
    let savings = null;
    let taxUsd = 0;

    const usdMonthly = parseFloat(selectedPlan.monthly_price);
    const usdAnnual = parseFloat(selectedPlan.annual_price || '0');

    let baseUsd = billingCycle === 'annual'
      ? (usdAnnual || usdMonthly * 12)
      : usdMonthly;

    if (previewData && previewData.currency_details) {
      // Use the calculated prorated USD backend value directly, with an immediate fallback so it never triggers undefined crashes.
      baseUsd = previewData.currency_details.base_usd_amount ?? baseUsd;
      taxUsd = baseUsd * previewData.currency_details.tax_rate;
    } else {
      // 18% without LUT for all users
      taxUsd = baseUsd * 0.18;
    }

    // format exactly to 2 decimal places to prevent random rounding bugs causing $23.60 to show as $24
    const formatUsd = (val: number) => val % 1 !== 0 ? `$${val.toFixed(2)}` : `$${val}`;

    displayPrice = formatUsd(baseUsd);

    savings = billingCycle === 'annual' && usdAnnual && usdMonthly > 0
      ? calculateSavings(String(usdMonthly), String(usdAnnual))
      : null;

    const totalUsd = baseUsd + taxUsd;
    totalDisplay = formatUsd(totalUsd);

    return { features, displayPrice, savings, totalDisplay, taxUsd };
  }, [selectedPlan, billingCycle, isIndianUser, previewData]);

  const handlePayment = async () => {
    if (!selectedPlan || !isScriptLoaded) return;

    setProcessingPayment(true);
    try {
      const orderData = await api.createSubscriptionOrder({
        plan_id: selectedPlan.id,
        billing_cycle: billingCycle,
      });

      if (!orderData.success) throw new Error(orderData.error || 'Failed to create order');

      const isINR = orderData.currency === 'INR';

      const options = {
        key: orderData.razorpay_key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        order_id: orderData.order_id,
        name: 'DmMe',
        description: `${selectedPlan.display_name} — ${billingCycle === 'annual' ? 'Annual' : 'Monthly'}`,
        prefill: { email: '' }, // User email not cached here, Razorpay shows prefill form
        ...(isINR && { method: paymentMethod }),
        ...RAZORPAY_THEME,

        handler: async (response: any) => {
          try {
            const verifyData = await api.verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              plan_id: selectedPlan.id,
              billing_cycle: billingCycle,
            });

            if (verifyData.success) {
              // Save payment method for future use
              try {
                await api.savePaymentMethod({
                  razorpay_payment_id: response.razorpay_payment_id,
                  is_default: true,
                });
              } catch { /* non-critical */ }

              toast.success(`🎉 Payment successful! Welcome to ${selectedPlan.display_name}!`, { duration: 5000 });
              setProcessingPayment(false);
              setTimeout(() => navigate('/settings'), 2500);
            } else {
              throw new Error(verifyData.error || 'Payment verification failed');
            }
          } catch (err: any) {
            toast.error(err.message || 'Payment verification failed. Contact support.');
            setProcessingPayment(false);
          }
        },

        modal: {
          ondismiss: () => {
            setProcessingPayment(false);
            toast('Payment cancelled.', { icon: '⚠️' });
          },
        },

        retry: { enabled: false },
      };

      const razorpay = new window.Razorpay(options);

      razorpay.on('payment.failed', async (response: any) => {
        try {
          await api.recordPaymentFailure({
            razorpay_order_id: orderData.order_id,
            razorpay_payment_id: response.error.metadata?.payment_id,
            error_code: response.error.code,
            error_description: response.error.description,
            reason: response.error.reason,
          });
        } catch { /* best-effort */ }

        toast.error(`Payment failed: ${response.error.description}`);
        setProcessingPayment(false);
      });

      razorpay.open();
    } catch (err: any) {
      toast.error(err.message || 'Failed to initiate payment. Please try again.');
      setProcessingPayment(false);
    }
  };

  if (loading) return <CheckoutSkeleton />;
  if (!selectedPlan) return null;

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 relative">
      {/* Processing overlay */}
      {processingPayment && (
        <div className="fixed inset-0 z-50 bg-neutral-950/80 backdrop-blur-sm flex flex-col items-center justify-center gap-4">
          <div className="bg-neutral-900 border border-neutral-700 rounded-2xl p-8 flex flex-col items-center gap-4 max-w-xs w-full">
            <Loader2 className="w-12 h-12 text-indigo-400 animate-spin" />
            <h3 className="text-white font-bold text-lg text-center">Initialising Secure Payment</h3>
            <p className="text-neutral-400 text-sm text-center">Please do not close this tab.</p>
          </div>
        </div>
      )}



      <div className="relative max-w-5xl mx-auto px-6 py-10">
        {/* Back */}
        <Link
          to="/pricing"
          className="inline-flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400 hover:text-neutral-800 dark:hover:text-white transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Pricing
        </Link>

        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-white mb-2">Complete Your Purchase</h1>
          <p className="text-neutral-400">You're one step away from unlocking full Instagram automation.</p>
        </div>

        <div className="grid md:grid-cols-5 gap-8">
          {/* ── Left column ── */}
          <div className="md:col-span-3 space-y-6">
            {/* Plan info */}
            <div className="rounded-2xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-neutral-900 dark:text-white">{selectedPlan.display_name}</h2>
                  <p className="text-sm text-neutral-400 mt-0.5">{selectedPlan.description}</p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400">
                  Selected Plan
                </span>
              </div>

              {/* Billing selector */}
              <div className="mt-4">
                <p className="text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-3">Billing Cycle</p>
                <div className="space-y-2">
                  {(['monthly', 'annual'] as BillingCycle[]).map(cycle => (
                    <label
                      key={cycle}
                      htmlFor={`cycle-${cycle}`}
                      className={`
                        flex items-center justify-between p-4 rounded-xl border-2 cursor-pointer transition-all
                        ${billingCycle === cycle
                          ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                          : 'border-neutral-200 dark:border-neutral-700 hover:border-indigo-300 dark:hover:border-indigo-700'
                        }
                      `}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="radio"
                          id={`cycle-${cycle}`}
                          name="billing_cycle"
                          checked={billingCycle === cycle}
                          onChange={() => setBillingCycle(cycle)}
                          className="accent-indigo-600"
                        />
                        <div>
                          <div className="font-semibold text-neutral-900 dark:text-white text-sm flex items-center gap-2">
                            {cycle === 'monthly' ? 'Monthly Billing' : 'Annual Billing'}
                            {cycle === 'annual' && savings && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400">
                                Save {savings.percentage}%
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-neutral-400">
                            {cycle === 'annual' && selectedPlan.annual_price
                              ? `${formatPrice(selectedPlan.annual_price, 1, '$')}/year`
                              : `${formatPrice(selectedPlan.monthly_price, 1, '$')}/month`
                            }
                            {((previewData?.currency_details?.tax_amount ?? 1) > 0) && (
                              <span className="ml-1 opacity-75">
                                + {previewData?.currency_details?.tax_name ||
                                  (isIndianUser ? 'Estimated Taxes (GST @ 18%)' : 'Estimated Taxes @ 18%')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      {cycle === 'monthly' ? <Zap className="w-4 h-4 text-neutral-400" /> : <Sparkles className="w-4 h-4 text-indigo-500" />}
                    </label>
                  ))}
                </div>
              </div>

              {/* Features */}
              <div className="mt-6 pt-5 border-t border-neutral-100 dark:border-neutral-800">
                <p className="text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-3">What's Included</p>
                <ul className="space-y-2">
                  {features.map((f, i) => (
                    <li key={i} className="flex items-center gap-3 text-sm">
                      <div className="w-4 h-4 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center flex-shrink-0">
                        <Check className="w-2.5 h-2.5 text-indigo-600 dark:text-indigo-400" />
                      </div>
                      <span className="text-neutral-600 dark:text-neutral-300">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Payment method (Indian users only) */}
            {isIndianUser && (
              <div className="rounded-2xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6">
                <h3 className="font-semibold text-neutral-900 dark:text-white flex items-center gap-2 mb-4">
                  <CreditCard className="w-4 h-4 text-indigo-500" /> Payment Method
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: 'card', label: 'Card', icon: CreditCard },
                    { value: 'upi', label: 'UPI', icon: Smartphone },
                    { value: 'netbanking', label: 'Net Banking', icon: Building2 },
                    { value: 'wallet', label: 'Wallet', icon: Wallet },
                  ].map(({ value, label, icon: Icon }) => (
                    <label
                      key={value}
                      htmlFor={`method-${value}`}
                      className={`
                        flex items-center gap-2 p-3 rounded-xl border-2 cursor-pointer transition-all
                        ${paymentMethod === value
                          ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                          : 'border-neutral-200 dark:border-neutral-700 hover:border-indigo-300'
                        }
                      `}
                    >
                      <input
                        type="radio"
                        id={`method-${value}`}
                        name="payment_method"
                        checked={paymentMethod === value}
                        onChange={() => setPaymentMethod(value as PaymentMethodType)}
                        className="accent-indigo-600"
                      />
                      <Icon className="w-4 h-4 text-indigo-500" />
                      <span className="text-sm font-medium text-neutral-700 dark:text-neutral-200">{label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Trust badges */}
            <div className="flex items-center gap-6 text-xs text-neutral-400">
              <span className="flex items-center gap-1.5"><Shield className="w-4 h-4 text-emerald-500" /> Secure Payment</span>
              <span className="flex items-center gap-1.5"><Lock className="w-4 h-4 text-emerald-500" /> SSL Encrypted</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> PCI Compliant</span>
            </div>
          </div>

          {/* ── Right: Order summary ── */}
          <div className="md:col-span-2">
            <div className="sticky top-24">
              <div className="rounded-2xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6 shadow-xl shadow-neutral-200/50 dark:shadow-none">
                <h3 className="font-bold text-neutral-900 dark:text-white text-lg mb-5">Order Summary</h3>

                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Plan</span>
                    <span className="font-medium text-neutral-900 dark:text-white">{selectedPlan.display_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Billing</span>
                    <span className="font-medium text-neutral-900 dark:text-white capitalize">{billingCycle}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">
                      {previewData?.is_upgrade ? 'Prorated Subtotal' : 'Subtotal'}
                    </span>
                    <span className="font-medium text-neutral-900 dark:text-white">{displayPrice}</span>
                  </div>
                  {savings && savings.amount > 0 && (
                    <div className="flex justify-between text-emerald-600 dark:text-emerald-400">
                      <span>Annual savings</span>
                      <span className="font-medium">−{formatPrice(savings.amount, 1, '$')}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-neutral-400">
                    <span>
                      {previewData?.currency_details?.tax_name ||
                        (isIndianUser ? 'Estimated Taxes (GST @ 18%)' : 'Estimated Taxes @ 18%')}
                    </span>
                    <span>{taxUsd > 0 ? `+ $${taxUsd.toFixed(2)}` : 'included'}</span>
                  </div>
                </div>

                <div className="border-t border-neutral-100 dark:border-neutral-800 my-4" />

                <div className="flex justify-between items-center mb-6">
                  <span className="font-bold text-neutral-900 dark:text-white">Total Due</span>
                  <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{totalDisplay}</span>
                </div>

                <p className="text-xs text-neutral-400 text-center mb-4">
                  {billingCycle === 'annual' ? 'Billed annually · auto-renews in 12 months' : 'Billed monthly · cancel anytime'}
                </p>

                {previewData && previewData.currency_details && previewData.currency_details.local_currency !== 'USD' && (
                  <p className="text-xs font-semibold text-indigo-500 text-center mb-4 bg-indigo-50 dark:bg-indigo-900/20 py-2 rounded-lg">
                    You will be charged {previewData.currency_details.local_currency === 'INR' ? '₹' : previewData.currency_details.local_currency}{previewData.currency_details.final_local_amount.toFixed(2)} automatically by Razorpay.
                  </p>
                )}

                <button
                  id="pay-now-btn"
                  onClick={handlePayment}
                  disabled={processingPayment || !isScriptLoaded}
                  className="w-full py-3.5 px-6 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-500 to-purple-600 text-white
                    hover:from-indigo-600 hover:to-purple-700 shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50
                    disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2"
                >
                  {processingPayment ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Processing…</>
                  ) : !isScriptLoaded ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Loading Gateway…</>
                  ) : (
                    <><CreditCard className="w-4 h-4" /> Pay Now · {totalDisplay}</>
                  )}
                </button>

                <div className="mt-4 flex items-start gap-2 text-xs text-neutral-400 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-3">
                  <AlertCircle className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <p>Payments processed securely by Razorpay. Your card details are never stored on our servers.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
