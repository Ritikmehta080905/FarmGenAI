import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import AppProviders from './AppProviders';
import AppRoutes from '@/routes/AppRoutes';
import SessionExpiredDialog from '@/components/dialogs/SessionExpiredDialog';
import { useSessionTimeout } from '@/hooks/useSessionTimeout';
import CommandPalette from '@/components/ui/CommandPalette';

function AppContent() {
  useSessionTimeout(30); // 30 minute idle timeout

  return (
    <BrowserRouter>
      <CommandPalette />
      <SessionExpiredDialog />
      <AppRoutes />
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AppProviders>
      <AppContent />
    </AppProviders>
  );
}
