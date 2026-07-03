// Auth context — holds current user/role/token presence; consumed by
// RouteGuard and the top navigation shell. See System_Architecture.md
// Section 3.4. Session is restored from localStorage on mount so a page
// reload doesn't force a re-login (see tokenStorage.ts for the tradeoff
// this implies).

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { apiClient } from "../lib/apiClient";
import { clearSession, getAccessToken, getStoredUser, setSession, type StoredUser } from "./tokenStorage";

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: StoredUser;
}

interface AuthContextValue {
  user: StoredUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<StoredUser | null>(() =>
    getAccessToken() ? getStoredUser() : null,
  );

  useEffect(() => {
    // Access token in localStorage but no cached user (e.g. storage was
    // partially cleared) — treat as logged out rather than guessing.
    if (getAccessToken() && !getStoredUser()) {
      clearSession();
      setUser(null);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiClient.post<LoginResponse>("/auth/login", { email, password });
    const { access_token, refresh_token, user: loggedInUser } = response.data;
    setSession(access_token, refresh_token, loggedInUser);
    setUser(loggedInUser);
  };

  const logout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      // Clear client-side state even if the network call fails (e.g.
      // token already expired) — the user's intent to log out locally
      // should always succeed.
      clearSession();
      setUser(null);
    }
  };

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, login, logout }),
    [user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
