// React Query hooks: auth (see docs/API_Contract.md Section 1).
// Login/logout themselves live on AuthContext (they mutate shared client
// session state, not just server state) — this module covers the
// remaining auth operation that doesn't need to touch the session:
// password change.

import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

interface PasswordChangeResponse {
  message: string;
}

async function changePassword(payload: PasswordChangeRequest): Promise<PasswordChangeResponse> {
  const response = await apiClient.put<PasswordChangeResponse>("/auth/password", payload);
  return response.data;
}

export function useChangePassword() {
  return useMutation({ mutationFn: changePassword });
}
