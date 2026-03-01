import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { api } from '../../utils/api';

interface User {
  id: string;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  bio?: string;
  profile_picture?: string;
  is_email_verified?: boolean;
  two_factor_enabled?: boolean;
  plan: 'free' | 'pro' | 'enterprise';
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  // 2FA state
  requires2FA: boolean;
  twoFAEmail: string | null;
  twoFAPassword: string | null;
  // Email verification
  requiresVerification: boolean;
  verificationEmail: string | null;
  onboardingCompleted: boolean;
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,
  error: null,
  requires2FA: false,
  twoFAEmail: null,
  twoFAPassword: null,
  requiresVerification: false,
  verificationEmail: null,
  onboardingCompleted: localStorage.getItem('onboarding_completed') === 'true',
};

// Async Thunks
export const login = createAsyncThunk(
  'auth/login',
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await api.login(email, password);
      return { ...response, email, password };
    } catch (error: any) {
      const errorData = error.response?.data;
      // Handle email verification required (403)
      if (errorData?.requires_verification) {
        return rejectWithValue({
          message: errorData.error || 'Email verification required',
          requires_verification: true,
          email: errorData.email,
        });
      }
      // Extract error message from DRF's various error formats
      let message = 'Login failed';
      if (errorData?.detail) {
        message = errorData.detail;
      } else if (errorData?.error) {
        message = errorData.error;
      } else if (errorData?.message) {
        message = errorData.message;
      } else if (errorData?.non_field_errors) {
        message = Array.isArray(errorData.non_field_errors)
          ? errorData.non_field_errors.join(' ')
          : errorData.non_field_errors;
      } else if (typeof errorData === 'object' && errorData !== null) {
        // Handle field-specific errors like {"email": ["..."]}
        const firstKey = Object.keys(errorData)[0];
        if (firstKey) {
          const val = errorData[firstKey];
          message = Array.isArray(val) ? val.join(' ') : String(val);
        }
      }
      return rejectWithValue({ message });
    }
  }
);

export const verify2FA = createAsyncThunk(
  'auth/verify2FA',
  async (
    { email, password, token }: { email: string; password: string; token: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await api.verifyLogin2FA({ email, password, token });
      return response;
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.detail || error.response?.data?.error || 'Invalid 2FA code'
      );
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (
    data: { email: string; username: string; password: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await api.register(data);
      return response;
    } catch (error: any) {
      const errorData = error.response?.data;
      let message = 'Registration failed';
      if (errorData?.message) {
        message = errorData.message;
      } else if (errorData?.detail) {
        message = errorData.detail;
      } else if (errorData?.non_field_errors) {
        message = Array.isArray(errorData.non_field_errors)
          ? errorData.non_field_errors.join(' ')
          : errorData.non_field_errors;
      } else if (typeof errorData === 'object' && errorData !== null) {
        // Handle field-specific errors like {"email": ["Already registered."]}
        const messages: string[] = [];
        for (const key of Object.keys(errorData)) {
          const val = errorData[key];
          const text = Array.isArray(val) ? val.join(' ') : String(val);
          messages.push(text);
        }
        if (messages.length > 0) message = messages.join(' ');
      }
      return rejectWithValue({ message });
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.requires2FA = false;
      state.twoFAEmail = null;
      state.twoFAPassword = null;
      state.requiresVerification = false;
      state.verificationEmail = null;
      state.onboardingCompleted = false;
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('onboarding_step');
    },
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    clear2FA: (state) => {
      state.requires2FA = false;
      state.twoFAEmail = null;
      state.twoFAPassword = null;
    },
    clearVerification: (state) => {
      state.requiresVerification = false;
      state.verificationEmail = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.requires2FA = false;
        state.requiresVerification = false;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;

        if (action.payload.requires_2fa) {
          // 2FA required — don't complete login yet
          state.requires2FA = true;
          state.twoFAEmail = action.payload.email;
          state.twoFAPassword = action.payload.password;
        } else {
          // Normal login success
          state.isAuthenticated = true;
          state.token = action.payload.tokens?.access || null;
          state.refreshToken = action.payload.tokens?.refresh || null;
          state.user = action.payload.user || null;
          state.requires2FA = false;
          state.twoFAEmail = null;
          state.twoFAPassword = null;
        }
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        const payload = action.payload as any;
        state.error = payload?.message || 'Login failed';

        if (payload?.requires_verification) {
          state.requiresVerification = true;
          state.verificationEmail = payload.email;
        }
      })
      // Verify 2FA
      .addCase(verify2FA.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(verify2FA.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.token = action.payload.tokens?.access || null;
        state.refreshToken = action.payload.tokens?.refresh || null;
        state.user = action.payload.user || null;
        state.requires2FA = false;
        state.twoFAEmail = null;
        state.twoFAPassword = null;
      })
      .addCase(verify2FA.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Register
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload.tokens) {
          state.isAuthenticated = true;
          state.token = action.payload.tokens.access;
          state.refreshToken = action.payload.tokens.refresh;
        }
        state.user = action.payload.user || null;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { logout, setUser, clearError, clear2FA, clearVerification } = authSlice.actions;
export default authSlice.reducer;
