/**
 * Payment Types — ported from src/types/payments.ts
 * Single source of truth for all payment-related type definitions
 */

export type BillingCycle = 'monthly' | 'annual';
export type PaymentMethodType = 'card' | 'upi' | 'netbanking' | 'wallet';
export type SubscriptionStatus = 'active' | 'trial' | 'cancelled' | 'expired' | 'past_due';

export interface PlanFeatures {
  automations_limit?: number;
  dms_per_month?: number;
  credit_rollovers?: boolean;
  priority_support?: boolean;
  custom_domains?: boolean;
  remove_badge?: boolean;
  dedicated_support?: boolean;
  advanced_analytics?: boolean;
  api_access?: boolean;
  white_label?: boolean;
  ai_personalization?: boolean;
  ab_testing?: boolean;
  multi_account?: boolean;
  [key: string]: any;
}

export interface Plan {
  id: string;
  name: string;
  display_name: string;
  description: string;
  monthly_price: string;
  annual_price: string;
  annual_discount?: number;
  features: PlanFeatures;
  is_active: boolean;
  sort_order: number;
  allow_self_service_changes?: boolean;
  requires_admin_approval?: boolean;
}

export interface Subscription {
  id: string;
  plan: Plan;
  plan_name: string;
  billing_cycle: BillingCycle;
  status: SubscriptionStatus;
  start_date: string;
  current_period_start?: string;
  current_period_end?: string;
  next_billing_date?: string;
  auto_renew?: boolean;
  is_trial?: boolean;
  trial_ends_at?: string;
  days_until_renewal?: number;
  created_at: string;
  latest_payment_id?: string;
}

export interface CurrencyConversion {
  base_amount_usd: number;
  local_currency: string;
  local_amount: number;
  exchange_rate: number;
  currency_symbol: string;
  conversion_success: boolean;
  country_code: string;
}

export interface CurrencyState {
  userCurrency: string;
  currencySymbol: string;
  exchangeRate: number;
  localAmount: number;
  countryCode: string;
  isIndianUser: boolean;
}

export interface RazorpaySuccessResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  order_id: string;
  name: string;
  description: string;
  image?: string;
  prefill?: { name?: string; email?: string; contact?: string };
  method?: PaymentMethodType;
  config?: any;
  theme?: { color?: string; backdrop_color?: string };
  handler?: (response: RazorpaySuccessResponse) => void;
  modal?: { ondismiss?: () => void };
  retry?: { enabled: boolean };
}

export interface CreateOrderResponse {
  success: boolean;
  razorpay_key_id: string;
  order_id: string;
  amount: number;
  currency: string;
  error?: string;
}

export interface VerifyPaymentResponse {
  success: boolean;
  error?: string;
  subscription?: { tokens_added?: number; previous_tokens?: number };
  user_tokens?: { tokens_remaining: number };
}
