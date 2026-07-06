// React Query hooks: departments (see docs/API_Contract.md Section 10.1-10.3).
// Not enumerated in Implementation_Roadmap.md's Milestone 3 file list —
// added because the Admin: User Management page's department selector
// (docs/UI_Wireframes.md Section 10) needs it and no frontend wrapper for
// the Milestone 1 reference-data endpoints existed yet. Logged in
// docs/Proposal_vs_Engineering_Additions.md as a Derived addition.
//
// Create/update/delete added for Version 2.3 (Academic Setup) — the
// backend endpoints existed since Milestone 1/Version 2.3 but had no
// frontend consumer at all until the Academic Setup pages.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

export interface DepartmentInput {
  name: string;
  code: string;
}

const departmentsQueryKey = ["departments"] as const;

export function useDepartments() {
  return useQuery({
    queryKey: departmentsQueryKey,
    queryFn: async () =>
      (await apiClient.get<PaginatedResponse<Department>>("/departments", { params: { page_size: 100 } })).data,
  });
}

export function useCreateDepartment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: DepartmentInput) =>
      (await apiClient.post<Department>("/departments", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: departmentsQueryKey });
    },
  });
}

export function useUpdateDepartment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<DepartmentInput> }) =>
      (await apiClient.put<Department>(`/departments/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: departmentsQueryKey });
    },
  });
}

export function useDeleteDepartment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/departments/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: departmentsQueryKey });
    },
  });
}
