// Root application component.
// Wires providers (React Query, theme), the router, and the root error
// boundary (Milestone 11 — see docs/System_Architecture.md §10) together.

import { RouterProvider } from "react-router-dom";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { AppProviders } from "./providers";
import { router } from "./router";

export function App() {
  return (
    <ErrorBoundary>
      <AppProviders>
        <RouterProvider router={router} />
      </AppProviders>
    </ErrorBoundary>
  );
}
