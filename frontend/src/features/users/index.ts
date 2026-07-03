// React Query hooks: users (profile, student/teacher management).
// See docs/API_Contract.md Section 2. Components call these hooks, never
// apiClient directly, per CLAUDE.md Section 7.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export interface UserProfile {
  first_name: string;
  last_name: string;
  profile_photo_url: string | null;
  department_id: string | null;
}

export interface Me {
  id: string;
  email: string;
  role: string;
  profile: UserProfile;
}

export interface MeUpdateInput {
  first_name?: string;
  last_name?: string;
  profile_photo_url?: string;
}

export interface StudentOrTeacher {
  id: string;
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  department_id: string;
  is_active: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface StudentCreateInput {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  department_id: string;
  enrollment_date: string;
}

export interface TeacherCreateInput {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  department_id: string;
  hire_date?: string;
}

export interface StudentOrTeacherUpdateInput {
  first_name?: string;
  last_name?: string;
  department_id?: string;
  is_active?: boolean;
}

const meQueryKey = ["users", "me"] as const;
const studentsQueryKey = (departmentId?: string) => ["users", "students", { departmentId }] as const;
const teachersQueryKey = (departmentId?: string) => ["users", "teachers", { departmentId }] as const;

export function useMe() {
  return useQuery({
    queryKey: meQueryKey,
    queryFn: async () => (await apiClient.get<Me>("/users/me")).data,
  });
}

export function useUpdateMe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: MeUpdateInput) => (await apiClient.put<Me>("/users/me", payload)).data,
    onSuccess: (data) => {
      queryClient.setQueryData(meQueryKey, data);
    },
  });
}

export function useStudents(departmentId?: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: [...studentsQueryKey(departmentId), page, pageSize],
    queryFn: async () =>
      (
        await apiClient.get<PaginatedResponse<StudentOrTeacher>>("/users/students", {
          params: { department_id: departmentId, page, page_size: pageSize },
        })
      ).data,
  });
}

export function useCreateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: StudentCreateInput) =>
      (await apiClient.post<StudentOrTeacher>("/users/students", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "students"] });
    },
  });
}

export function useUpdateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: StudentOrTeacherUpdateInput }) =>
      (await apiClient.put<StudentOrTeacher>(`/users/students/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "students"] });
    },
  });
}

export function useDeactivateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      (await apiClient.delete<{ id: string; is_active: boolean }>(`/users/students/${id}`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "students"] });
    },
  });
}

export function useTeachers(departmentId?: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: [...teachersQueryKey(departmentId), page, pageSize],
    queryFn: async () =>
      (
        await apiClient.get<PaginatedResponse<StudentOrTeacher>>("/users/teachers", {
          params: { department_id: departmentId, page, page_size: pageSize },
        })
      ).data,
  });
}

export function useCreateTeacher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TeacherCreateInput) =>
      (await apiClient.post<StudentOrTeacher>("/users/teachers", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "teachers"] });
    },
  });
}

export function useUpdateTeacher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: StudentOrTeacherUpdateInput }) =>
      (await apiClient.put<StudentOrTeacher>(`/users/teachers/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "teachers"] });
    },
  });
}
