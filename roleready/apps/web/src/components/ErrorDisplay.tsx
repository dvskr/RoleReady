"use client";

import React from 'react';

interface ErrorDisplayProps {
  error?: Error | string;
  title?: string;
  description?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  variant?: 'default' | 'warning' | 'error' | 'info';
  showRetry?: boolean;
  showDismiss?: boolean;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  title = "Something went wrong",
  description,
  onRetry,
  onDismiss,
  variant = 'error',
  showRetry = true,
  showDismiss = false,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'warning':
        return {
          container: 'bg-yellow-50 border-yellow-200',
          icon: 'text-yellow-600',
          title: 'text-yellow-800',
          description: 'text-yellow-700',
          button: 'bg-yellow-600 hover:bg-yellow-700 text-white',
        };
      case 'error':
        return {
          container: 'bg-red-50 border-red-200',
          icon: 'text-red-600',
          title: 'text-red-800',
          description: 'text-red-700',
          button: 'bg-red-600 hover:bg-red-700 text-white',
        };
      case 'info':
        return {
          container: 'bg-blue-50 border-blue-200',
          icon: 'text-blue-600',
          title: 'text-blue-800',
          description: 'text-blue-700',
          button: 'bg-blue-600 hover:bg-blue-700 text-white',
        };
      default:
        return {
          container: 'bg-gray-50 border-gray-200',
          icon: 'text-gray-600',
          title: 'text-gray-800',
          description: 'text-gray-700',
          button: 'bg-gray-600 hover:bg-gray-700 text-white',
        };
    }
  };

  const styles = getVariantStyles();
  const errorMessage = error instanceof Error ? error.message : error;

  return (
    <div className={`rounded-lg border p-6 ${styles.container}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {variant === 'error' && (
            <svg className={`h-6 w-6 ${styles.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          )}
          {variant === 'warning' && (
            <svg className={`h-6 w-6 ${styles.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          )}
          {variant === 'info' && (
            <svg className={`h-6 w-6 ${styles.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </div>
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${styles.title}`}>
            {title}
          </h3>
          <div className={`mt-2 text-sm ${styles.description}`}>
            <p>{description || errorMessage || "An unexpected error occurred. Please try again."}</p>
          </div>
          <div className="mt-4 flex space-x-3">
            {showRetry && onRetry && (
              <button
                onClick={onRetry}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${styles.button}`}
              >
                Try Again
              </button>
            )}
            {showDismiss && onDismiss && (
              <button
                onClick={onDismiss}
                className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Specific error components for common scenarios
export const NetworkError: React.FC<{ onRetry?: () => void }> = ({ onRetry }) => (
  <ErrorDisplay
    title="Connection Problem"
    description="We're having trouble connecting to our servers. Please check your internet connection and try again."
    onRetry={onRetry}
    variant="warning"
  />
);

export const NotFoundError: React.FC<{ resource?: string }> = ({ resource = "page" }) => (
  <ErrorDisplay
    title="Not Found"
    description={`The ${resource} you're looking for doesn't exist or may have been moved.`}
    variant="info"
    showRetry={false}
  />
);

export const ServerError: React.FC<{ onRetry?: () => void }> = ({ onRetry }) => (
  <ErrorDisplay
    title="Server Error"
    description="Our servers are experiencing issues. We're working to fix this. Please try again in a few minutes."
    onRetry={onRetry}
    variant="error"
  />
);

export const ValidationError: React.FC<{ errors: string[] }> = ({ errors }) => (
  <ErrorDisplay
    title="Please fix the following issues:"
    description={errors.join('. ')}
    variant="warning"
    showRetry={false}
  />
);

export const PermissionError: React.FC = () => (
  <ErrorDisplay
    title="Access Denied"
    description="You don't have permission to perform this action. Please contact your administrator if you believe this is an error."
    variant="error"
    showRetry={false}
  />
);

export const TimeoutError: React.FC<{ onRetry?: () => void }> = ({ onRetry }) => (
  <ErrorDisplay
    title="Request Timeout"
    description="The request took too long to complete. This might be due to a slow connection or server load."
    onRetry={onRetry}
    variant="warning"
  />
);
