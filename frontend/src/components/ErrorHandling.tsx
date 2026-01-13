// ============================================================================
// COMPREHENSIVE ERROR HANDLING SYSTEM
// ============================================================================

/**
 * Global error handling with:
 * - Error boundaries
 * - Toast notifications
 * - API error interceptors
 * - Loading states
 * - Retry mechanisms
 * - User-friendly messages
 */

import React, { Component, createContext, useContext, useState, type ErrorInfo, type ReactNode } from 'react';

import { XCircle, AlertCircle, CheckCircle, Info, X } from 'lucide-react';

// ============================================================================
// 1. TOAST NOTIFICATION SYSTEM
// ============================================================================

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextType {
  showToast: (type: ToastType, message: string, duration?: number) => void;
  showError: (message: string) => void;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showInfo: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (type: ToastType, message: string, duration = 5000) => {
    const id = Math.random().toString(36).substring(7);
    const toast: Toast = { id, type, message, duration };
    
    setToasts((prev) => [...prev, toast]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const showError = (message: string) => showToast('error', message);
  const showSuccess = (message: string) => showToast('success', message);
  const showWarning = (message: string) => showToast('warning', message);
  const showInfo = (message: string) => showToast('info', message);

  return (
    <ToastContext.Provider value={{ showToast, showError, showSuccess, showWarning, showInfo }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};

const ToastContainer: React.FC<{ toasts: Toast[]; onRemove: (id: string) => void }> = ({
  toasts,
  onRemove,
}) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{ toast: Toast; onRemove: (id: string) => void }> = ({
  toast,
  onRemove,
}) => {
  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <XCircle className="w-5 h-5" />,
    warning: <AlertCircle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />,
  };

  const colors = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };

  return (
    <div
      className={`${colors[toast.type]} border rounded-lg p-4 shadow-lg flex items-start gap-3 animate-slide-in`}
    >
      <div className="flex-shrink-0 mt-0.5">{icons[toast.type]}</div>
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => onRemove(toast.id)}
        className="flex-shrink-0 hover:opacity-70 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};


// ============================================================================
// 2. ERROR BOUNDARY
// ============================================================================

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Send to error tracking service (e.g., Sentry)
    // logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white border border-gray-200 rounded-xl p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Oops! Something went wrong
            </h2>
            <p className="text-gray-600 mb-6">
              We're sorry, but something unexpected happened. Please try refreshing the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}


// ============================================================================
// 3. API ERROR HANDLER (Add to src/lib/api.ts)
// ============================================================================

export const getErrorMessage = (error: any): string => {
  // Handle different error types
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        return data.detail || data.error || 'Invalid request. Please check your input.';
      case 401:
        return 'Your session has expired. Please log in again.';
      case 403:
        return 'You don\'t have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 429:
        return 'Too many requests. Please try again in a moment.';
      case 500:
        return 'Server error. Our team has been notified.';
      case 502:
      case 503:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        return data.detail || data.error || 'An unexpected error occurred.';
    }
  } else if (error.request) {
    // Request made but no response received
    return 'Unable to connect to server. Please check your internet connection.';
  } else {
    // Error in request setup
    return error.message || 'An unexpected error occurred.';
  }
};


// ============================================================================
// 4. LOADING STATE HOOK
// ============================================================================

interface LoadingState {
  isLoading: boolean;
  error: string | null;
  startLoading: () => void;
  stopLoading: () => void;
  setError: (error: string) => void;
  clearError: () => void;
}

export const useLoadingState = (): LoadingState => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setErrorState] = useState<string | null>(null);

  const startLoading = () => {
    setIsLoading(true);
    setErrorState(null);
  };

  const stopLoading = () => {
    setIsLoading(false);
  };

  const setError = (error: string) => {
    setErrorState(error);
    setIsLoading(false);
  };

  const clearError = () => {
    setErrorState(null);
  };

  return {
    isLoading,
    error,
    startLoading,
    stopLoading,
    setError,
    clearError,
  };
};


// ============================================================================
// 5. ASYNC ACTION HOOK (with automatic error handling)
// ============================================================================

export const useAsyncAction = () => {
  const { showError, showSuccess } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const execute = async <T,>(
    action: () => Promise<T>,
    options?: {
      successMessage?: string;
      errorMessage?: string;
      onSuccess?: (result: T) => void;
      onError?: (error: any) => void;
    }
  ): Promise<T | undefined> => {
    setIsLoading(true);

    try {
      const result = await action();
      
      if (options?.successMessage) {
        showSuccess(options.successMessage);
      }
      
      options?.onSuccess?.(result);
      return result;
    } catch (error: any) {
      const errorMessage = options?.errorMessage || getErrorMessage(error);
      showError(errorMessage);
      options?.onError?.(error);
      return undefined;
    } finally {
      setIsLoading(false);
    }
  };

  return { execute, isLoading };
};


// ============================================================================
// 6. RETRY MECHANISM
// ============================================================================

export const withRetry = async <T,>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: any;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry on client errors (4xx)
      if (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof (error as any).response?.status === 'number' &&
        (error as any).response.status >= 400 &&
        (error as any).response.status < 500
      ) {
        throw error;
      }

      // Wait before retrying (exponential backoff)
      if (i < maxRetries - 1) {
        await new Promise((resolve) => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
  }

  throw lastError;
};


// ============================================================================
// 7. LOADING SPINNER COMPONENT
// ============================================================================

export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex items-center justify-center">
      <div
        className={`${sizes[size]} border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin`}
      />
    </div>
  );
};

export const LoadingOverlay: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-gray-600 font-medium">Loading...</p>
      </div>
    </div>
  );
};


// ============================================================================
// 8. ERROR MESSAGE COMPONENT
// ============================================================================

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry, onDismiss }) => {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800">{message}</p>
          {(onRetry || onDismiss) && (
            <div className="mt-3 flex gap-2">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                >
                  Try Again
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="px-3 py-1 border border-red-300 text-red-700 text-sm rounded hover:bg-red-50 transition-colors"
                >
                  Dismiss
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};


// ============================================================================
// 9. EMPTY STATE COMPONENT
// ============================================================================

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      {icon && (
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-center max-w-md mb-6">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};


// ============================================================================
// 10. USAGE EXAMPLE
// ============================================================================

export const ExampleUsage: React.FC = () => {
  const { execute, isLoading } = useAsyncAction();
  const { showSuccess, showError } = useToast();

  // Import your API module at the top of the file:
  // import { api } from '../lib/api'; // Adjust the import path as needed

  // For demonstration, here's a mock api object:
  const api = {
    createAutomation: async (data: { name: string }) => {
      // Simulate API call
      return new Promise((resolve) => setTimeout(() => resolve({ id: 1, ...data }), 500));
    },
  };

  const handleCreateAutomation = async () => {
    await execute(
      async () => {
        // Your API call
        const result = await api.createAutomation({ name: 'Test' });
        return result;
      },
      {
        successMessage: '✓ Automation created successfully!',
        errorMessage: 'Failed to create automation',
        onSuccess: (result) => {
          // Navigate or update state
          console.log('Created:', result);
        },
      }
    );
  };

  return (
    <div>
      <button onClick={handleCreateAutomation} disabled={isLoading}>
        {isLoading ? <LoadingSpinner size="sm" /> : 'Create Automation'}
      </button>
    </div>
  );
};


// ============================================================================
// 11. ADD TO APP.TSX
// ============================================================================

/*
import { ToastProvider } from './components/ErrorHandling';
import { ErrorBoundary } from './components/ErrorHandling';

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <Router>
          <!-- Your app components -->
        </Router>
      </ToastProvider>
    </ErrorBoundary>
  );
}
*/


// ============================================================================
// 12. ADD ANIMATIONS TO index.css
// ============================================================================

const cssAnimations = `
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
`;


// ============================================================================
// 13. NETWORK ERROR COMPONENT
// ============================================================================

export const NetworkError: React.FC<{ onRetry: () => void }> = ({ onRetry }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white border border-gray-200 rounded-xl p-8 text-center">
        <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-8 h-8 text-yellow-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Connection Lost</h2>
        <p className="text-gray-600 mb-6">
          Unable to connect to server. Please check your internet connection and try again.
        </p>
        <button
          onClick={onRetry}
          className="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    </div>
  );
};