// React Query hooks: semesters (see docs/API_Contract.md Section 10.4-10.6).
// Not enumerated in Implementation_Roadmap.md's Milestone 8 file list —
// added because the Admin: Fee Dashboard's "New Fee Structure" form
// (docs/UI_Wireframes.md Section 12) needs a Semester selector and no
// frontend wrapper for the Milestone 1 reference-data endpoint existed
// yet — same precedent as features/departments/index.ts (Milestone 3).
// Logged in docs/Proposal_vs_Engineering_Additions.md as a Derived
// addition.
//
// Create/update/delete added for Version 2.3 (Academic Setup) — the
// backend endpoints existed since Milestone 1/Version 2.3 but had no
// frontend consumer at all until the Academic Setup pages.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

export interface SemesterInput {
  name: string;
  start_date: string;
  end_date: string;
}

const semestersQueryKey = ["semesters"] as const;

export function useSemesters() {
  return useQuery({
    queryKey: semestersQueryKey,
    queryFn: async () =>
      (await apiClient.get<PaginatedResponse<Semester>>("/semesters", { params: { page_size: 100 } })).data,
  });
}

export function useCreateSemester() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SemesterInput) => (await apiClient.post<Semester>("/semesters", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: semestersQueryKey });
    },
  });
}

export function useUpdateSemester() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<SemesterInput> }) =>
      (await apiClient.put<Semester>(`/semesters/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: semestersQueryKey });
    },
  });
}

export function useDeleteSemester() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/semesters/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: semestersQueryKey });
    },
  });
}
