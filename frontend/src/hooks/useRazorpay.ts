/**
 * useRazorpay Hook — ported from src/hooks/useRazorpay.ts
 * Handles Razorpay script loading + payment window opening
 */

import { useEffect, useState, useCallback, useRef } from 'react';

declare global {
  interface Window {
    Razorpay: any;
  }
}

interface UseRazorpayReturn {
  isScriptLoaded: boolean;
  scriptError: string | null;
  openPayment: (options: any) => void;
}

const RAZORPAY_SCRIPT_URL = 'https://checkout.razorpay.com/v1/checkout.js';

export const useRazorpay = (): UseRazorpayReturn => {
  const [isScriptLoaded, setIsScriptLoaded] = useState(false);
  const [scriptError, setScriptError] = useState<string | null>(null);
  const scriptRef = useRef<HTMLScriptElement | null>(null);

  useEffect(() => {
    if (window.Razorpay) {
      setIsScriptLoaded(true);
      return;
    }

    const existingScript = document.querySelector(`script[src="${RAZORPAY_SCRIPT_URL}"]`);
    if (existingScript) {
      existingScript.addEventListener('load', () => setIsScriptLoaded(true));
      return;
    }

    const script = document.createElement('script');
    script.src = RAZORPAY_SCRIPT_URL;
    script.async = true;

    script.onload = () => {
      setIsScriptLoaded(true);
      setScriptError(null);
    };

    script.onerror = () => {
      setScriptError('Failed to load payment gateway. Please refresh and try again.');
      setIsScriptLoaded(false);
    };

    document.body.appendChild(script);
    scriptRef.current = script;

    return () => {
      if (scriptRef.current && document.body.contains(scriptRef.current)) {
        document.body.removeChild(scriptRef.current);
        scriptRef.current = null;
      }
    };
  }, []);

  const openPayment = useCallback((options: any) => {
    if (!window.Razorpay) {
      setScriptError('Payment gateway not available. Please refresh and try again.');
      return;
    }
    try {
      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (err: any) {
      setScriptError(`Payment gateway error: ${err.message || 'Unknown error'}`);
    }
  }, []);

  return { isScriptLoaded, scriptError, openPayment };
};
