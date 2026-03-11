/**
 * Payment System Constants — ported from src/lib/constants.ts
 */

export const PLAN_NAMES = {
  FREE: 'free',
  STARTER: 'starter',
  PRO: 'pro',
  BUSINESS: 'business',
  ENTERPRISE: 'enterprise',
} as const;

export const SUBSCRIPTION_STATUSES = {
  ACTIVE: 'active',
  TRIAL: 'trial',
  CANCELLED: 'cancelled',
  EXPIRED: 'expired',
  PAST_DUE: 'past_due',
} as const;

export const BILLING_CYCLES = {
  MONTHLY: 'monthly',
  ANNUAL: 'annual',
} as const;

export const PAYMENT_METHODS = {
  CARD: 'card',
  UPI: 'upi',
  NETBANKING: 'netbanking',
  WALLET: 'wallet',
} as const;

export const RAZORPAY_THEME = {
  theme: {
    color: '#6366f1',
    backdrop_color: 'rgba(0, 0, 0, 0.85)',
  },
} as const;

export const API_ENDPOINTS = {
  PLANS: '/api/payments/plans/',
  SUBSCRIPTION: '/api/payments/subscription/',
  SUBSCRIPTION_CREATE: '/api/payments/subscription/create/',
  VERIFY: '/api/payments/verify/',
  VERIFY_FAILURE: '/api/payments/verify/failure/',
  CURRENCY_CONVERT: '/api/payments/currency/convert/',
  PAYMENT_METHODS: '/api/payments/payment-methods/',
} as const;
