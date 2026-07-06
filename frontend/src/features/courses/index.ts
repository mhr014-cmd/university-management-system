// React Query hooks: courses (see docs/API_Contract.md Section 10.4-10.6).
//
// Added for Version 2.3 (Academic Setup) — the backend GET/POST/PUT/DELETE
// /courses endpoints existed since Milestone 1 (list/create) and Version
// 2.3 (update/delete), but had no frontend feature-hook file at all until
// now (per the pre-V2.3 architecture review's finding: Course had zero
// frontend presence, not even read-only).

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export interface Course {
  id: string;
  department_id: string;
  name: string;
  code: string;
  credit_hours: number;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface CourseInput {
  department_id: string;
  name: string;
  code: string;
  credit_hours: number;
}

const coursesQueryKey = (departmentId?: string) => ["courses", { departmentId }] as const;

export function useCourses(departmentId?: string, page = 1, pageSize = 100) {
  return useQuery({
    queryKey: [...coursesQueryKey(departmentId), page, pageSize],
    queryFn: async () =>
      (
        await apiClient.get<PaginatedResponse<Course>>("/courses", {
          params: { department_id: departmentId, page, page_size: pageSize },
        })
      ).data,
  });
}

export function useCreateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CourseInput) => (await apiClient.post<Course>("/courses", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
    },
  });
}

export function useUpdateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<CourseInput> }) =>
      (await apiClient.put<Course>(`/courses/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
    },
  });
}

export function useDeleteCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/courses/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
    },
  });
}
