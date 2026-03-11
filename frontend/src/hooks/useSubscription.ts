/**
 * useSubscription Hook — ported from src/hooks/useSubscription.ts
 * Adapted to use the existing api.ts client instead of raw axios + AuthContext
 */

import { useEffect, useState, useCallback } from 'react';
import { api } from '../utils/api';
import type { Plan, Subscription, BillingCycle } from '../types/payments';
import { isFreePlan } from '../lib/pricing';

interface UseSubscriptionReturn {
  currentSubscription: Subscription | null;
  loading: boolean;
  isCurrentPlan: (plan: Plan, billingCycle: BillingCycle) => boolean;
  isDowngrade: (plan: Plan, billingCycle: BillingCycle) => boolean;
  canPurchasePlan: (plan: Plan, billingCycle: BillingCycle) => boolean;
  getPlanButtonText: (plan: Plan, billingCycle: BillingCycle) => string;
  fetchSubscription: () => Promise<void>;
}

export const useSubscription = (): UseSubscriptionReturn => {
  const [currentSubscription, setCurrentSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!localStorage.getItem('access_token');

  const fetchSubscription = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    try {
      const data = await api.getSubscription();
      if (data?.subscription) {
        setCurrentSubscription(data.subscription);
      } else if (data?.id) {
        // Direct subscription object
        setCurrentSubscription(data);
      }
    } catch {
      // No subscription is fine
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  const isCurrentPlan = useCallback((plan: Plan, billingCycle: BillingCycle): boolean => {
    if (!currentSubscription?.plan) return false;
    const isFree = isFreePlan(plan);
    if (isFree && parseFloat(currentSubscription.plan.monthly_price) === 0) return true;
    return currentSubscription.plan.id === plan.id && currentSubscription.billing_cycle === billingCycle;
  }, [currentSubscription]);

  const isDowngrade = useCallback((plan: Plan, billingCycle: BillingCycle): boolean => {
    if (!currentSubscription?.plan) return false;
    const currentIsFree = parseFloat(currentSubscription.plan.monthly_price) === 0;
    if (currentIsFree) return false;

    const currentTierPrice = parseFloat(currentSubscription.plan.monthly_price);
    const targetTierPrice = parseFloat(plan.monthly_price);

    if (targetTierPrice < currentTierPrice) return true;
    if (targetTierPrice === currentTierPrice && currentSubscription.plan.id === plan.id) {
      if (currentSubscription.billing_cycle === 'annual' && billingCycle === 'monthly') return true;
    }
    return false;
  }, [currentSubscription]);

  const canPurchasePlan = useCallback((plan: Plan, billingCycle: BillingCycle): boolean => {
    if (!isAuthenticated || !currentSubscription) return true;
    if (currentSubscription.status !== 'active' && currentSubscription.status !== 'trial') return true;
    if (isCurrentPlan(plan, billingCycle)) return false;
    if (isDowngrade(plan, billingCycle)) return false;
    return true;
  }, [isAuthenticated, currentSubscription, isCurrentPlan, isDowngrade]);

  const getPlanButtonText = useCallback((plan: Plan, billingCycle: BillingCycle): string => {
    if (plan.requires_admin_approval) return 'Contact Sales';
    if (!isAuthenticated) return 'Get Started';
    if (!currentSubscription) return 'Subscribe Now';

    if (isCurrentPlan(plan, billingCycle)) return 'Current Plan';
    if (isDowngrade(plan, billingCycle)) return 'Downgrade Not Allowed';

    const isFree = isFreePlan(plan);
    if (!isFree && currentSubscription.plan?.id === plan.id && currentSubscription.billing_cycle !== billingCycle) {
      return billingCycle === 'annual' ? 'Switch to Annual' : 'Switch to Monthly';
    }

    const currentIsFree = parseFloat(currentSubscription.plan?.monthly_price ?? '0') === 0;
    if (currentIsFree && !isFree) return 'Upgrade Now';

    return 'Upgrade Now';
  }, [isAuthenticated, currentSubscription, isCurrentPlan, isDowngrade]);

  return {
    currentSubscription,
    loading,
    isCurrentPlan,
    isDowngrade,
    canPurchasePlan,
    getPlanButtonText,
    fetchSubscription,
  };
};
