// Axios client configuration.
// Two instances: `apiClient` for versioned business endpoints (/api/v1/*),
// and `rootClient` for unversioned infrastructure endpoints (currently only
// /health — see docs/Proposal_vs_Engineering_Additions.md for why it sits
// outside /api/v1). `apiClient` attaches the access token to every request
// and silently refreshes once on a 401 before retrying, per CLAUDE.md
// Section 7 ("token attachment, silent refresh... centralized here").

import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { clearSession, getAccessToken, getRefreshToken, setTokens } from "../auth/tokenStorage";

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

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;
  try {
    const response = await axios.post<{ access_token: string; refresh_token: string }>(
      `${API_BASE_URL}/auth/refresh`,
      { refresh_token: refreshToken },
    );
    setTokens(response.data.access_token, response.data.refresh_token);
    return response.data.access_token;
  } catch {
    clearSession();
    return null;
  }
}

// Public auth endpoints must never trigger the refresh-and-retry flow: a
// 401 from /auth/login (wrong password) or /auth/refresh (invalid refresh
// token) is itself the meaningful result the caller needs to see and
// display inline, not a signal that a stored access token expired.
// Without this exclusion, a failed login attempt was found (via live
// browser testing) to trigger a doomed refresh attempt — there's no
// refresh token yet — which then force-navigated to /login and wiped the
// login form's own error state before the user ever saw it.
const AUTH_ENDPOINTS_EXCLUDED_FROM_REFRESH = ["/auth/login", "/auth/refresh"];

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableConfig | undefined;
    const isExcluded = AUTH_ENDPOINTS_EXCLUDED_FROM_REFRESH.some((path) =>
      originalRequest?.url?.includes(path),
    );
    if (error.response?.status === 401 && originalRequest && !originalRequest._retried && !isExcluded) {
      originalRequest._retried = true;
      // Deduplicate concurrent refresh attempts (e.g. several requests
      // failing with 401 at once) into a single /auth/refresh call.
      refreshPromise ??= refreshAccessToken();
      const newAccessToken = await refreshPromise;
      refreshPromise = null;
      if (newAccessToken) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      }
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);
