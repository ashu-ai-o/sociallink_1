import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { Toaster } from 'react-hot-toast';
import { store } from './store';
import './index.css';
import { OfflineNotice } from './components/OfflineNotice';
import { MainLayout } from './components/layout/MainLayout';
import { AuthLayout } from './components/layout/AuthLayout';
import { OnboardingFlow } from './components/Onboarding/OnboardingFlow';
import { useState, useEffect } from 'react';
import { api } from './utils/api';

// Pages
import { AuthPage } from './pages/Auth/AuthPage';
import { ResetPasswordPage } from './pages/Auth/ResetPasswordPage';
import { ChangePasswordPage } from './pages/Auth/ChangePasswordPage';
import { DashboardPage } from './pages/Dashboard/DashboardPage';
import { AutomationsPage } from './pages/Automations/AutomationsPage';
import { CreateAutomationPage } from './pages/Automations/CreateAutomationPage';
import { EditAutomationPage } from './pages/Automations/EditAutomationPage';
import { AnalyticsPage } from './pages/Analytics/AnalyticsPage';
import { ContactsPage } from './pages/Contacts/ContactsPage';
import { SettingsPage } from './pages/SettingsPage';
import { NotificationSettings } from './pages/NotificationSettings';
import { FeedbackPage } from './pages/FeedbackPage';
import { PricingPage } from './pages/Static/PricingPage';
import { CheckoutPage } from './pages/CheckoutPage';
import { AboutPage } from './pages/Static/AboutPage';
import { ContactUsPage } from './pages/Static/ContactUsPage';
import { PrivacyPolicyPage } from './pages/Static/PrivacyPolicyPage';
import { TermsOfServicePage } from './pages/Static/TermsOfServicePage';
import { Footer } from './components/layout/Footer';

// ============================================================
// Auth validation — verifies token on app startup
// Clears stale tokens and redirects to login if invalid
// ============================================================
const AuthValidator = ({ children }: { children: React.ReactNode }) => {
  const [checking, setChecking] = useState(true);
  const [isValid, setIsValid] = useState(false);

  useEffect(() => {
    const validateToken = async () => {
      const token = localStorage.getItem('access_token');

      // No token at all — not authenticated
      if (!token) {
        setIsValid(false);
        setChecking(false);
        return;
      }

      try {
        // Try to verify the token with the backend
        const profile = await api.getUserProfile();
        console.log('[AuthValidator] Fetched profile:', profile);
        localStorage.setItem('onboarding_completed', String(profile.onboarding_completed));
        localStorage.setItem('onboarding_step', String(profile.onboarding_step || 0));
        setIsValid(true);
      } catch (error: any) {
        // Token is invalid, expired, or backend is unreachable
        // Clear everything and force re-login
        console.warn('[AuthValidator] Token validation failed, clearing auth state', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('onboarding_completed');
        localStorage.removeItem('onboarding_step');
        setIsValid(false);
      } finally {
        setChecking(false);
      }
    };

    validateToken();
  }, []);

  // Show loading spinner while validating
  if (checking) {
    return (
      <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">Verifying session...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

// Protected Route — requires valid token
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('access_token');
  if (!token) return <Navigate to="/auth" replace />;
  return <>{children}</>;
};

// Onboarding Check — requires valid token + onboarding completed
const OnboardingCheck = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('access_token');
  const onboardingCompletedContext = localStorage.getItem('onboarding_completed');
  const onboardingCompleted = onboardingCompletedContext === 'true' || onboardingCompletedContext === true?.toString();

  if (!token) return <Navigate to="/auth" replace />;
  if (!onboardingCompleted) return <Navigate to="/onboarding" replace />;
  return <>{children}</>;
};

// Root redirect — checks auth before sending anywhere
const RootRedirect = () => {
  const token = localStorage.getItem('access_token');
  if (!token) return <Navigate to="/auth" replace />;

  const onboardingCompletedContext = localStorage.getItem('onboarding_completed');
  const onboardingCompleted = onboardingCompletedContext === 'true' || onboardingCompletedContext === true?.toString();

  if (!onboardingCompleted) return <Navigate to="/onboarding" replace />;
  return <Navigate to="/dashboard" replace />;
};

// Layout for public static pages
const PublicLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex flex-col min-h-screen">
      <div className="flex-grow">
        {children}
      </div>
      <Footer />
    </div>
  );
};

import { GoogleOAuthProvider } from '@react-oauth/google';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

const GoogleOAuthWrapper = ({ children }: { children: React.ReactNode }) => {
  if (!GOOGLE_CLIENT_ID) return <>{children}</>;
  return <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>{children}</GoogleOAuthProvider>;
};

import { AnimatedBackground } from './components/layout/AnimatedBackground';

function App() {
  return (
    <Provider store={store}>
      <GoogleOAuthWrapper>
        <BrowserRouter>
          <AuthValidator>
            <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 flex flex-col relative overflow-hidden">
              <AnimatedBackground />
              <Toaster
                position="top-right"
                toastOptions={{
                  duration: 3000,
                  className: 'bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white border border-neutral-200 dark:border-neutral-800 shadow-soft-lg rounded-xl px-4 py-3',
                  style: {},
                  success: {
                    iconTheme: {
                      primary: '#10b981',
                      secondary: '#fff',
                    },
                  },
                  error: {
                    iconTheme: {
                      primary: '#ef4444',
                      secondary: '#fff',
                    },
                  },
                }}
              />
              <OfflineNotice />

              <Routes>
                {/* Root — redirect based on auth state */}
                <Route path="/" element={<RootRedirect />} />

                {/* Public Routes — accessible without login */}
                <Route path="/auth" element={<AuthLayout><AuthPage /></AuthLayout>} />
                <Route path="/auth/reset-password" element={<AuthLayout><ResetPasswordPage /></AuthLayout>} />
                <Route path="/pricing" element={<PublicLayout><PricingPage /></PublicLayout>} />
                <Route path="/checkout" element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
                <Route path="/about" element={<PublicLayout><AboutPage /></PublicLayout>} />
                <Route path="/contact" element={<PublicLayout><ContactUsPage /></PublicLayout>} />
                <Route path="/privacy-policy" element={<PublicLayout><PrivacyPolicyPage /></PublicLayout>} />
                <Route path="/terms-of-service" element={<PublicLayout><TermsOfServicePage /></PublicLayout>} />

                {/* Onboarding Route */}
                <Route path="/onboarding" element={
                  <ProtectedRoute>
                    <OnboardingFlow />
                  </ProtectedRoute>
                } />

                {/* Protected Routes — require login + onboarding */}
                <Route path="/dashboard" element={<OnboardingCheck><MainLayout><DashboardPage /></MainLayout></OnboardingCheck>} />
                <Route path="/automations" element={<OnboardingCheck><MainLayout><AutomationsPage /></MainLayout></OnboardingCheck>} />
                <Route path="/automations/create" element={<OnboardingCheck><MainLayout><CreateAutomationPage /></MainLayout></OnboardingCheck>} />
                <Route path="/automations/:id/edit" element={<OnboardingCheck><MainLayout><EditAutomationPage /></MainLayout></OnboardingCheck>} />
                <Route path="/analytics" element={<OnboardingCheck><MainLayout><AnalyticsPage /></MainLayout></OnboardingCheck>} />
                <Route path="/contacts" element={<OnboardingCheck><MainLayout><ContactsPage /></MainLayout></OnboardingCheck>} />
                <Route path="/settings" element={<OnboardingCheck><MainLayout><SettingsPage /></MainLayout></OnboardingCheck>} />
                <Route path="/settings/notifications" element={<OnboardingCheck><MainLayout><NotificationSettings /></MainLayout></OnboardingCheck>} />
                <Route path="/settings/change-password" element={<OnboardingCheck><MainLayout><ChangePasswordPage /></MainLayout></OnboardingCheck>} />
                <Route path="/feedback" element={<OnboardingCheck><MainLayout><FeedbackPage /></MainLayout></OnboardingCheck>} />

                {/* Catch-all — redirect to login or dashboard */}
                <Route path="*" element={<RootRedirect />} />
              </Routes>
            </div>
          </AuthValidator>
        </BrowserRouter>
      </GoogleOAuthWrapper>
    </Provider>
  );
}

export default App;
