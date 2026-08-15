import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { NotificationProvider } from '@/contexts/NotificationContext';
import ErrorBoundary from '@/components/ui/ErrorBoundary';
import OfflineBanner from '@/components/ui/OfflineBanner';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export function AppProviders({ children }) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <NotificationProvider>
          <AuthProvider>
            <OfflineBanner />
            {children}
          </AuthProvider>
        </NotificationProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default AppProviders;
