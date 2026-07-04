// Vite configuration — placeholder.
// See docs/System_Architecture.md Section 12 for the fixed frontend stack
// (React 18 + TypeScript, served from a CDN per Section 8 Deployment Architecture).

/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  // Milestone 11: component tests (CLAUDE.md §10) via Vitest + React
  // Testing Library. jsdom provides the DOM environment vitest needs to
  // render components outside a real browser.
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
  },
});
