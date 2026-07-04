// React Query hooks: semesters (see docs/API_Contract.md Section 10.4).
// Not enumerated in Implementation_Roadmap.md's Milestone 8 file list —
// added because the Admin: Fee Dashboard's "New Fee Structure" form
// (docs/UI_Wireframes.md Section 12) needs a Semester selector and no
// frontend wrapper for the Milestone 1 reference-data endpoint existed
// yet — same precedent as features/departments/index.ts (Milestone 3).
// Logged in docs/Proposal_vs_Engineering_Additions.md as a Derived
// addition.

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export interface Semester {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export function useSemesters() {
  return useQuery({
    queryKey: ["semesters"],
    queryFn: async () =>
      (await apiClient.get<PaginatedResponse<Semester>>("/semesters", { params: { page_size: 100 } })).data,
  });
}
