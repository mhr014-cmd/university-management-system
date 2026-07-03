// React Query hooks: departments (see docs/API_Contract.md Section 10.1).
// Not enumerated in Implementation_Roadmap.md's Milestone 3 file list —
// added because the Admin: User Management page's department selector
// (docs/UI_Wireframes.md Section 10) needs it and no frontend wrapper for
// the Milestone 1 reference-data endpoints existed yet. Logged in
// docs/Proposal_vs_Engineering_Additions.md as a Derived addition.

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export interface Department {
  id: string;
  name: string;
  code: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export function useDepartments() {
  return useQuery({
    queryKey: ["departments"],
    queryFn: async () =>
      (await apiClient.get<PaginatedResponse<Department>>("/departments", { params: { page_size: 100 } })).data,
  });
}
