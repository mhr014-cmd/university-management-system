// Axios client configuration.
// Two instances: `apiClient` for versioned business endpoints (/api/v1/*,
// added starting Milestone 1+), and `rootClient` for unversioned
// infrastructure endpoints (currently only /health — see
// docs/Proposal_vs_Engineering_Additions.md for why it sits outside /api/v1).
// Auth token attachment (Authorization header, silent refresh) is added in
// Milestone 2 — see frontend/src/auth/tokenStorage.ts.

import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const API_ROOT_URL = import.meta.env.VITE_API_ROOT_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
});

export const rootClient = axios.create({
  baseURL: API_ROOT_URL,
  timeout: 10_000,
});
