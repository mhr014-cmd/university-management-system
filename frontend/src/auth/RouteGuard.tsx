// Route guard — redirects unauthenticated users to Login. Client-side UX
// convenience only — server-side RBAC (app/middleware/rbac.py) is the
// actual enforcement, per System_Architecture.md Section 6 and CLAUDE.md
// Section 7 ("Client-side RBAC hiding of UI elements is a UX convenience
// only — it is never a substitute for server-side enforcement").

import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function RouteGuard() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
