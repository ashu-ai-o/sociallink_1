import axios from 'axios';
import type { AxiosInstance } from 'axios';

import { AxiosError } from 'axios';


const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiClient {
  public client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor with retry logic
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest: any = error.config;

        // Token refresh logic
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
              refresh: refreshToken,
            });

            const { access } = response.data;
            localStorage.setItem('access_token', access);
            originalRequest.headers.Authorization = `Bearer ${access}`;

            return this.client(originalRequest);
          } catch (refreshError) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/auth';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // ========================================================================
  // AUTH ENDPOINTS
  // ========================================================================

  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login/', { email, password });
    const data = response.data;

    // If login returns tokens directly (no 2FA), store them
    if (data.tokens) {
      localStorage.setItem('access_token', data.tokens.access);
      localStorage.setItem('refresh_token', data.tokens.refresh);
    }

    return data;
  }

  async register(data: { email: string; username: string; password: string; password2?: string }) {
    const payload = {
      ...data,
      password2: data.password2 || data.password,
    };
    const response = await this.client.post('/auth/register/', payload);
    return response.data;
  }

  async logout() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await this.client.post('/auth/logout/', { refresh_token: refreshToken });
      }
    } catch (error) {
      // Proceed with local cleanup even if API call fails
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  async logoutAllDevices(keepCurrent: boolean = true) {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await this.client.post('/auth/logout-all-devices/', {
      keep_current: keepCurrent,
      refresh_token: refreshToken
    });
    return response.data;
  }

  async logoutDevice(sessionId: string) {
    const response = await this.client.post(`/auth/logout-device/${sessionId}/`);
    return response.data;
  }

  // Check Username Availability
  async checkUsername(username: string) {
    const response = await this.client.get(`/auth/check-username/?username=${username}`);
    return response.data;
  }

  // Google OAuth
  async googleAuth(googleToken: string) {
    const response = await this.client.post('/auth/google/', { google_token: googleToken });
    const data = response.data;
    if (data.tokens) {
      localStorage.setItem('access_token', data.tokens.access);
      localStorage.setItem('refresh_token', data.tokens.refresh);
    }
    return data;
  }

  // Token verification
  async verifyToken() {
    const response = await this.client.get('/auth/verify-token/');
    return response.data;
  }

  // JWT token verify (SimpleJWT)
  async verifyJWTToken(token: string) {
    const response = await this.client.post('/auth/token/verify/', { token });
    return response.data;
  }

  // ========================================================================
  // EMAIL VERIFICATION
  // ========================================================================

  async verifyEmail(token: string) {
    const response = await this.client.get('/auth/verify-email/', { params: { token } });
    return response.data;
  }

  async resendVerificationEmail() {
    const response = await this.client.post('/auth/resend-verification/');
    return response.data;
  }

  // ========================================================================
  // PASSWORD MANAGEMENT (OTP-BASED)
  // ========================================================================

  // Change password (for logged-in users)
  async requestPasswordChangeOTP() {
    const response = await this.client.post('/auth/request-password-change-otp/');
    return response.data;
  }

  async verifyOTPAndChangePassword(data: { otp_code: string; new_password: string }) {
    const response = await this.client.post('/auth/verify-otp-and-change-password/', data);
    return response.data;
  }

  // Forgot password (for unauthenticated users)
  async requestForgotPasswordOTP(email: string) {
    const response = await this.client.post('/auth/forgot-password/', { email });
    return response.data;
  }

  async verifyForgotPasswordOTP(data: { email: string; otp_code: string; new_password?: string; verify_only?: boolean }) {
    const response = await this.client.post('/auth/forgot-password/verify/', data);
    return response.data;
  }

  // Legacy endpoints (keep for compatibility)
  async changePassword(data: { old_password: string; new_password: string }) {
    const response = await this.client.post('/auth/change-password/', data);
    return response.data;
  }

  // Legacy token-based password reset
  async requestPasswordReset(email: string) {
    const response = await this.client.post('/auth/password-reset/', { email });
    return response.data;
  }

  async confirmPasswordReset(data: { token: string; new_password: string }) {
    const response = await this.client.post('/auth/password-reset/confirm/', data);
    return response.data;
  }

  // Delete account
  async deleteAccount(password: string) {
    const response = await this.client.delete('/auth/delete-account/', {
      data: { password },
    });
    return response.data;
  }

  // ========================================================================
  // TWO-FACTOR AUTHENTICATION (2FA)
  // ========================================================================

  async setup2FA() {
    const response = await this.client.post('/auth/2fa/setup/');
    return response.data;
  }

  async verifySetup2FA(data: { token: string; secret: string }) {
    const response = await this.client.post('/auth/2fa/verify-setup/', data);
    return response.data;
  }

  async verifyLogin2FA(data: { email: string; password: string; token: string }) {
    const response = await this.client.post('/auth/2fa/verify-login/', data);
    const result = response.data;
    if (result.tokens) {
      localStorage.setItem('access_token', result.tokens.access);
      localStorage.setItem('refresh_token', result.tokens.refresh);
    }
    return result;
  }

  async disable2FA(data: { password: string; token: string }) {
    const response = await this.client.post('/auth/2fa/disable/', data);
    return response.data;
  }

  async get2FAStatus() {
    const response = await this.client.get('/auth/2fa/status/');
    return response.data;
  }

  async getBackupCodes() {
    const response = await this.client.get('/auth/2fa/backup-codes/');
    return response.data;
  }

  async regenerateBackupCodes(token: string) {
    const response = await this.client.post('/auth/2fa/regenerate-backup/', { token });
    return response.data;
  }

  // ========================================================================
  // SESSIONS
  // ========================================================================

  async getActiveSessions() {
    const response = await this.client.get('/auth/sessions/my-sessions/');
    return response.data;
  }

  async getSessionDetails(sessionId: string) {
    const response = await this.client.get(`/auth/sessions/${sessionId}/`);
    return response.data;
  }

  async endSession(sessionId: string) {
    const response = await this.client.post(`/auth/sessions/${sessionId}/end/`);
    return response.data;
  }

  async trackCustomEvent(data: { event_type: string; event_name: string; event_data?: any }) {
    const response = await this.client.post('/auth/sessions/track-event/', data);
    return response.data;
  }

  // ========================================================================
  // INSTAGRAM ACCOUNTS
  // ========================================================================

  async getInstagramAccounts() {
    const response = await this.client.get('/instagram-accounts/');
    return response.data;
  }

  async connectInstagramAccount(data: any) {
    const response = await this.client.post('/instagram-accounts/', data);
    return response.data;
  }

  async disconnectInstagramAccount(id: string) {
    await this.client.delete(`/instagram-accounts/${id}/disconnect/`);
  }

  // Instagram OAuth
  async initiateInstagramOAuth() {
    const response = await this.client.get('/auth/instagram/oauth/');
    return response.data;
  }

  async disconnectInstagram(accountId: string) {
    const response = await this.client.delete(`/instagram-accounts/${accountId}/disconnect/`);
    return response.data;
  }

  async refreshInstagramStats(accountId: string) {
    const response = await this.client.post(`/instagram-accounts/${accountId}/refresh_stats/`);
    return response.data;
  }

  async getInstagramPosts(accountId: string) {
    const response = await this.client.get(`/instagram-accounts/${accountId}/posts/`);
    return response.data;
  }

  async getInstagramProfileStats(accountId: string) {
    const response = await this.client.get(`/instagram-accounts/${accountId}/profile_stats/`);
    return response.data;
  }

  // ========================================================================
  // AUTOMATIONS
  // ========================================================================

  async getAutomations(params?: any) {
    const response = await this.client.get('/automations/', { params });
    return response.data;
  }

  async getAutomation(id: string) {
    const response = await this.client.get(`/automations/${id}/`);
    return response.data;
  }

  async createAutomation(data: any) {
    const response = await this.client.post('/automations/', data);
    return response.data;
  }

  async updateAutomation(id: string, data: any) {
    const response = await this.client.patch(`/automations/${id}/`, data);
    return response.data;
  }

  async deleteAutomation(id: string) {
    await this.client.delete(`/automations/${id}/`);
  }

  async toggleAutomation(id: string) {
    const response = await this.client.post(`/automations/${id}/toggle/`);
    return response.data;
  }

  async getAutomationAnalytics(id: string, days: number = 30) {
    const response = await this.client.get(`/automations/${id}/analytics/`, {
      params: { days },
    });
    return response.data;
  }

  async duplicateAutomation(id: string) {
    const response = await this.client.post(`/automations/${id}/duplicate/`);
    return response.data;
  }

  // ========================================================================
  // CONTACTS
  // ========================================================================

  async getContacts(params?: any) {
    const response = await this.client.get('/contacts/', { params });
    return response.data;
  }

  async getContact(id: string) {
    const response = await this.client.get(`/contacts/${id}/`);
    return response.data;
  }

  async searchContacts(query: string) {
    const response = await this.client.get('/contacts/search/', {
      params: { q: query },
    });
    return response.data;
  }

  // Export contacts
  async exportContacts(format: 'csv' | 'xlsx' = 'csv') {
    const response = await this.client.get('/contacts/export/', {
      params: { format },
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(response.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `contacts_${Date.now()}.${format}`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  // Export triggers
  async exportTriggers(format: 'csv' | 'xlsx' = 'csv', automationId?: string) {
    const response = await this.client.get('/triggers/export/', {
      params: { format, automation_id: automationId },
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(response.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `triggers_${Date.now()}.${format}`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  // ========================================================================
  // ANALYTICS
  // ========================================================================

  async exportAnalytics(period: '7d' | '30d' | '90d' = '30d') {
    const response = await this.client.get('/analytics/dashboard/export_analytics/', {
      params: { period },
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(response.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics_report_${Date.now()}.xlsx`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  async getDashboardStats(period: '7d' | '30d' | '90d' = '30d') {
    const response = await this.client.get('/analytics/dashboard/', {
      params: { period },
    });
    return response.data;
  }

  async getAutomationPerformance() {
    const response = await this.client.get('/analytics/automations/');
    return response.data;
  }

  // Advanced Analytics
  async getDashboardOverview(period: string = '30d') {
    const response = await this.client.get('/analytics/dashboard/overview/', {
      params: { period },
    });
    return response.data;
  }

  async getTopPerformers(limit: number = 10) {
    const response = await this.client.get('/analytics/dashboard/top_performers/', {
      params: { limit },
    });
    return response.data;
  }

  async getRealtimeStats() {
    const response = await this.client.get('/analytics/dashboard/realtime_stats/');
    return response.data;
  }

  async getRateLimitStatus() {
    const response = await this.client.get('/analytics/dashboard/rate_limit_status/');
    return response.data;
  }

  // ========================================================================
  // AI PROVIDERS
  // ========================================================================

  async getAIProviders() {
    const response = await this.client.get('/ai-providers/status/');
    return response.data;
  }

  async testAIProvider(data: any) {
    const response = await this.client.post('/ai-providers/test/', data);
    return response.data;
  }

  // ========================================================================
  // USER PROFILE
  // ========================================================================

  async getUserProfile() {
    const response = await this.client.get('/auth/profile/');
    return response.data;
  }

  async updateUserProfile(data: any) {
    const response = await this.client.patch('/auth/profile/', data);
    return response.data;
  }

  async updateUserProfileWithImage(formData: FormData) {
    const response = await this.client.patch('/auth/profile/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  // ========================================================================
  // EMAIL & NOTIFICATION PREFERENCES
  // ========================================================================

  async getEmailPreferences() {
    const response = await this.client.get('/auth/email-preferences/');
    return response.data;
  }

  async updateEmailPreferences(preferences: any) {
    const response = await this.client.put('/auth/email-preferences/', preferences);
    return response.data;
  }

  async getNotificationPreferences() {
    const response = await this.client.get('/auth/notification-preferences/');
    return response.data;
  }

  async updateNotificationPreferences(preferences: any) {
    const response = await this.client.put('/auth/notification-preferences/', preferences);
    return response.data;
  }

  async getEmailHistory() {
    const response = await this.client.get('/auth/email-history/');
    return response.data;
  }

  // ========================================================================
  // FEEDBACK
  // ========================================================================

  async submitFeedback(data: {
    category: string;
    title: string;
    message: string;
    rating?: number;
    priority?: string;
    page_url?: string;
  }) {
    const response = await this.client.post('/auth/feedback/', data);
    return response.data;
  }

  async getMyFeedback() {
    const response = await this.client.get('/auth/feedback/mine/');
    return response.data;
  }

  // ========================================================================
  // ENTERPRISE CONTACT
  // ========================================================================

  async submitEnterpriseContact(data: {
    first_name: string;
    last_name: string;
    email: string;
    phone?: string;
    company_name: string;
    company_size: string;
    job_title?: string;
    project_details: string;
    budget_range?: string;
    timeline?: string;
  }) {
    const response = await this.client.post('/auth/contact/enterprise/', data);
    return response.data;
  }

  // ========================================================================
  // COOKIE CONSENT
  // ========================================================================

  async syncCookiePreferences(data: any) {
    const response = await this.client.post('/auth/cookie-consent/sync/', data);
    return response.data;
  }

  async getCookiePreferences() {
    const response = await this.client.get('/auth/cookie-consent/preferences/');
    return response.data;
  }

  async trackAnonymousCookieConsent(data: any) {
    const response = await this.client.post('/auth/cookie-consent/track-anonymous/', data);
    return response.data;
  }

  // ========================================================================
  // AUTOMATION TESTING
  // ========================================================================

  async testAutomationTrigger(id: string, data: any) {
    const response = await this.client.post(`/automations/${id}/test_trigger/`, data);
    return response.data;
  }

  async testAIEnhancement(data: any) {
    const response = await this.client.post('/automations/test_ai_enhancement/', data);
    return response.data;
  }

  // ========================================================================
  // EXPORT FUNCTIONS
  // ========================================================================

  async exportContactsFile(format: 'csv' | 'xlsx') {
    const response = await this.client.get('/contacts/export/', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  async exportTriggersFile(format: 'csv' | 'xlsx', automationId?: string) {
    const response = await this.client.get('/triggers/export/', {
      params: { format, automation_id: automationId },
      responseType: 'blob',
    });
    return response.data;
  }

  // ========================================================================
  // ONBOARDING
  // ========================================================================

  async completeOnboarding() {
    const response = await this.client.post('/auth/complete-onboarding/');
    return response.data;
  }

  async saveOnboardingStep(step: number) {
    const response = await this.client.post('/auth/onboarding-step/', { step });
    return response.data;
  }
}

export const api = new ApiClient();
