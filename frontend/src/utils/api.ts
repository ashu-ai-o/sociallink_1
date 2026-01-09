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

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/token/', { email, password });
    const { access, refresh } = response.data;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    return response.data;
  }

  async register(data: { email: string; username: string; password: string }) {
    const response = await this.client.post('/auth/register/', data);
    return response.data;
  }

  

  async logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // Instagram Accounts
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


  




  // Automations
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

  // Contacts
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


  // Analytics



  // Export analytics
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

  // AI Providers
  async getAIProviders() {
    const response = await this.client.get('/ai-providers/status/');
    return response.data;
  }

  async testAIProvider(data: any) {
    const response = await this.client.post('/ai-providers/test/', data);
    return response.data;
  }
}

export const api = new ApiClient();

