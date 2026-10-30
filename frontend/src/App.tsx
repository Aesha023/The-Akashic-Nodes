import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DemoModeProvider } from './context/DemoModeContext';
import { AuthProvider } from './context/AuthContext';
import { AppShell } from './components/layout/AppShell';
import './i18n';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <DemoModeProvider>
        <AuthProvider>
          <AppShell />
        </AuthProvider>
      </DemoModeProvider>
    </QueryClientProvider>
  );
};

export default App;
