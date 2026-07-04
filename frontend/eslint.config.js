// ESLint flat config (Milestone 11 hardening).
//
// Minimal by design: ESLint's own recommended rules plus typescript-eslint's
// recommended TS rules, applied only to frontend/src. tsconfig.json's own
// strict compiler options (noUnusedLocals, noUnusedParameters, strict) and
// `npx tsc --noEmit` already catch the majority of correctness issues this
// project cares about — this config exists to complete the `lint` script
// package.json already committed to, not to introduce a second, competing
// style/rule system.

import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: { "react-hooks": reactHooks },
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Only the two long-standing hooks-correctness rules — not the
      // plugin's full "recommended" set, which (as of v7) also bundles
      // newer, stricter rules (e.g. set-state-in-effect) that would flag
      // an idiomatic pattern already used throughout Milestones 0-10
      // (syncing local state from a React Query result in useEffect).
      // Milestone 11 reviews/hardens; it does not refactor frozen,
      // working, tested code to satisfy a newly-added lint rule.
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
  },
);
