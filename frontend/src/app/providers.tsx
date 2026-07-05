// App-level providers.
// Wraps the app in React Query's QueryClientProvider, the theme context,
// and the Auth context (frontend/src/auth/AuthContext.tsx).

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/ui/Toast";
import { ThemeProvider } from "./ThemeProvider";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>{children}</AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
