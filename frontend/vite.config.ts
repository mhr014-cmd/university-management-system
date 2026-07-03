// Vite configuration — placeholder.
// See docs/System_Architecture.md Section 12 for the fixed frontend stack
// (React 18 + TypeScript, served from a CDN per Section 8 Deployment Architecture).

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
