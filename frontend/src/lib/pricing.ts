/**
 * Pricing Utilities — ported from src/lib/pricing.ts
 * Adapted for DmMe (Instagram automation) plan features
 */

import type { Plan } from '../types/payments';
import { PLAN_NAMES } from './paymentConstants';

export const formatPrice = (
  price: string | number,
  exchangeRate: number = 1,
  currencySymbol: string = '₹'
): string => {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price;
  if (numPrice === 0) return 'Free';

  if (exchangeRate !== 1) {
    const convertedPrice = numPrice * exchangeRate;
    return `${currencySymbol}${convertedPrice.toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`;
  }

  return `$${numPrice.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
};

export const calculateSavings = (
  monthlyPrice: string,
  annualPrice: string
): { amount: number; percentage: string } => {
  const monthly = parseFloat(monthlyPrice) * 12;
  const annual = parseFloat(annualPrice);
  const savings = monthly - annual;
  const percentage = ((savings / monthly) * 100).toFixed(0);
  return { amount: savings, percentage };
};

/**
 * Build a human-readable feature list from plan.features JSON
 */
export const getPlanFeatures = (plan: Plan): string[] => {
  const features = plan.features;
  const list: string[] = [];

  if (typeof features === 'object' && features !== null) {
    if (features.automations_limit != null) {
      list.push(
        features.automations_limit === -1 || features.automations_limit === 9999
          ? 'Unlimited automations'
          : `${features.automations_limit} active automations`
      );
    }
    if (features.dms_per_month != null) {
      list.push(
        features.dms_per_month === -1 || features.dms_per_month === 9999
          ? 'Unlimited DMs / month'
          : `${features.dms_per_month.toLocaleString()} DMs / month`
      );
    }
    if (features.advanced_analytics) list.push('Advanced analytics');
    if (features.ai_personalization) list.push('AI-powered personalization');
    if (features.ab_testing) list.push('A/B testing');
    if (features.credit_rollovers) list.push('Credit rollovers');
    if (features.priority_support) list.push('Priority support');
    if (features.dedicated_support) list.push('Dedicated account manager');
    if (features.api_access) list.push('API access');
    if (features.white_label) list.push('White-label solution');
    if (features.multi_account) list.push('Multi-account management');
    if (features.remove_badge) list.push('Remove DmMe branding');
    if (features.custom_domains) list.push('Custom domains');
  }

  // Fallback for plans without structured features
  if (list.length === 0) {
    const name = plan.name.toLowerCase();
    if (name === PLAN_NAMES.FREE) {
      return ['2 active automations', '500 DMs/month', 'Basic analytics', 'Email support'];
    }
    if (name === PLAN_NAMES.PRO) {
      return ['10 active automations', '5,000 DMs/month', 'Advanced analytics', 'Priority support', 'AI personalization'];
    }
    if (name === PLAN_NAMES.BUSINESS) {
      return ['Unlimited automations', 'Unlimited DMs', 'Custom analytics', 'Dedicated support', 'API access'];
    }
  }

  return list;
};

export const isFreePlan = (plan: Plan): boolean =>
  parseFloat(plan.monthly_price) === 0 ||
  plan.name.toLowerCase() === PLAN_NAMES.FREE ||
  plan.name.toLowerCase() === PLAN_NAMES.STARTER;

export const isPopularPlan = (plan: Plan): boolean =>
  plan.name.toLowerCase() === PLAN_NAMES.PRO;

export const isBestValuePlan = (plan: Plan): boolean =>
  plan.name.toLowerCase() === PLAN_NAMES.BUSINESS;
