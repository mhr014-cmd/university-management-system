// Token storage helpers.
// Per System_Architecture.md Section 5.2, access tokens should live in
// short-lived client storage and refresh tokens in more durable storage.
// Our API returns both tokens directly in the JSON response body (see
// API_Contract.md Section 1) rather than as Set-Cookie headers, so an
// httpOnly cookie isn't achievable without a backend-for-frontend layer
// this project doesn't have. Pragmatic tradeoff, made explicit rather than
// silently assumed: both tokens are mirrored to localStorage so a session
// survives a page reload, which does carry XSS exposure risk beyond what
// an httpOnly cookie would have. Revisit if a BFF layer is ever added.

const ACCESS_TOKEN_KEY = "ict_education_access_token";
const REFRESH_TOKEN_KEY = "ict_education_refresh_token";
const USER_KEY = "ict_education_user";

export interface StoredUser {
  id: string;
  email: string;
  role: string;
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredUser(): StoredUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
}

export function setSession(accessToken: string, refreshToken: string, user: StoredUser): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearSession(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
