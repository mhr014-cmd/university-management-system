// Health API connectivity check — React Query hook wrapping GET /health.
// Used by the Dashboard shell (Milestone 0) to verify the frontend can
// reach the backend and that the backend can reach the database.

import { useQuery } from "@tanstack/react-query";
import { rootClient } from "./apiClient";

export interface HealthCheckResponse {
  status: "ok" | "degraded";
  environment: string;
  database: "ok" | "unreachable";
}

async function fetchHealth(): Promise<HealthCheckResponse> {
  const response = await rootClient.get<HealthCheckResponse>("/health");
  return response.data;
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    retry: false,
    refetchInterval: 30_000,
  });
}
