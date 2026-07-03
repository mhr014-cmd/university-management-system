// Root application component.
// Wires providers (React Query, theme) and the router together.

import { RouterProvider } from "react-router-dom";
import { AppProviders } from "./providers";
import { router } from "./router";

export function App() {
  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  );
}
