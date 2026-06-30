import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { router } from './router';
import { useAuthStore } from './store/auth';
import { useThemeStore } from './store/theme';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppInit({ children }: { children: React.ReactNode }) {
  const init = useAuthStore((s) => s.init);
  const theme = useThemeStore((s) => s.theme);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    init();
    // Apply theme class from store
    document.documentElement.classList.toggle('dark', theme === 'dark');
    setReady(true);
  }, [init, theme]);

  if (!ready) return null;

  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInit>
        <RouterProvider router={router} />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              borderRadius: '12px',
              padding: '12px 16px',
              fontSize: '14px',
            },
          }}
        />
      </AppInit>
    </QueryClientProvider>
  );
}