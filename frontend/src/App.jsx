import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import AppRoutes from './routes/AppRoutes'
import SessionExpiredDialog from './components/dialogs/SessionExpiredDialog'
import { useSessionTimeout } from './hooks/useSessionTimeout'
import ErrorBoundary from './components/ui/ErrorBoundary'
import OfflineBanner from './components/ui/OfflineBanner'
import CommandPalette from './components/ui/CommandPalette'

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

// Inner component to safely use Auth hooks inside the AuthProvider
function AppContent() {
  useSessionTimeout(30); // 30 minute timeout

  return (
    <BrowserRouter>
      <CommandPalette />
      <SessionExpiredDialog />
      <AppRoutes />
    </BrowserRouter>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <NotificationProvider>
          <AuthProvider>
            <OfflineBanner />
            <AppContent />
          </AuthProvider>
        </NotificationProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
