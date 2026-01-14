import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { Toaster } from 'react-hot-toast';
import { store } from './store';
import './index.css';
import { OfflineNotice } from './components/OfflineNotice';
import { MainLayout } from './components/layout/MainLayout';
import { AuthLayout } from './components/layout/AuthLayout';
import { OnboardingFlow } from './components/Onboarding/OnboardingFlow';

// Pages
import { AuthPage } from './pages/Auth/AuthPage';
import { ResetPasswordPage } from './pages/Auth/ResetPasswordPage';
import { ChangePasswordPage } from './pages/Auth/ChangePasswordPage';
import { DashboardPage } from './pages/Dashboard/DashboardPage';
import { AutomationsPage } from './pages/Automations/AutomationsPage';
import { CreateAutomationPage } from './pages/Automations/CreateAutomationPage';
import { AnalyticsPage } from './pages/Analytics/AnalyticsPage';
import { ContactsPage } from './pages/Contacts/ContactsPage';
import { SettingsPage } from './pages/SettingsPage';
import { NotificationSettings } from './pages/NotificationSettings';
import { PricingPage } from './pages/Static/PricingPage';
import { AboutPage } from './pages/Static/AboutPage';
import { ContactUsPage } from './pages/Static/ContactUsPage';

// Protected Route Component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('access_token');
  if (!token) return <Navigate to="/auth" replace />;
  return <>{children}</>;
};

// Onboarding Check Route
const OnboardingCheck = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('access_token');
  const onboardingCompleted = localStorage.getItem('onboarding_completed') === 'true';

  if (!token) return <Navigate to="/auth" replace />;
  if (!onboardingCompleted) return <Navigate to="/onboarding" replace />;
  return <>{children}</>;
};

function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3000,
              className: '',
              style: {
                background: 'transparent',
                boxShadow: 'none',
                padding: 0,
              },
              success: {
                className: 'bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white border border-neutral-200 dark:border-neutral-800 shadow-soft-lg rounded-xl px-4 py-3',
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                className: 'bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white border border-neutral-200 dark:border-neutral-800 shadow-soft-lg rounded-xl px-4 py-3',
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
          <OfflineNotice />

          <Routes>
            {/* Public Routes */}
            <Route path="/auth" element={<AuthLayout><AuthPage /></AuthLayout>} />
            <Route path="/auth/reset-password" element={<AuthLayout><ResetPasswordPage /></AuthLayout>} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/contact" element={<ContactUsPage />} />

            {/* Onboarding Route */}
            <Route path="/onboarding" element={
              <ProtectedRoute>
                <OnboardingFlow />
              </ProtectedRoute>
            } />

            {/* Protected Routes with Main Layout */}
            <Route path="/*" element={
              <OnboardingCheck>
                <MainLayout>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/automations" element={<AutomationsPage />} />
                    <Route path="/automations/create" element={<CreateAutomationPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/contacts" element={<ContactsPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="/settings/notifications" element={<NotificationSettings />} />
                    <Route path="/settings/change-password" element={<ChangePasswordPage />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </MainLayout>
              </OnboardingCheck>
            } />
          </Routes>
        </div>
      </BrowserRouter>
    </Provider>
  );
}

export default App;
