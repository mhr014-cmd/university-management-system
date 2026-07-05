// React Query hooks: attendance (summary, marking, corrections, reports)
// See docs/API_Contract.md Section 4.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export type AttendanceStatus = "present" | "absent" | "late" | "excused";

export interface AttendanceDateRecord {
  date: string;
  status: AttendanceStatus;
}

export interface ClassSessionAttendanceSummary {
  class_session_id: string;
  course_name: string;
  percentage: number;
  low_attendance_warning: boolean;
  records: AttendanceDateRecord[];
}

export interface AttendanceMeResponse {
  overall_percentage: number;
  low_attendance_warning: boolean;
  by_class_session: ClassSessionAttendanceSummary[];
}

export interface AttendanceRecordInput {
  student_id: string;
  status: AttendanceStatus;
}

export interface AttendanceMarkInput {
  class_session_id: string;
  attendance_date: string;
  records: AttendanceRecordInput[];
}

export interface AttendanceRecord {
  id: string;
  student_id: string;
  class_session_id: string;
  marked_by_teacher_id: string;
  attendance_date: string;
  status: AttendanceStatus;
}

export interface ClassAttendanceEntry {
  id: string;
  student_id: string;
  date: string;
  status: AttendanceStatus;
}

export interface ClassAttendanceResponse {
  class_session_id: string;
  records: ClassAttendanceEntry[];
}

export interface AttendanceReportEntry {
  student_id: string;
  student_name: string;
  percentage: number;
}

export interface AttendanceReportResponse {
  scope: { department_id: string | null; semester_id: string | null };
  summary: AttendanceReportEntry[];
}

export function useMyAttendance(params?: { classSessionId?: string; dateFrom?: string; dateTo?: string }) {
  return useQuery({
    queryKey: ["attendance", "me", params],
    queryFn: async () =>
      (
        await apiClient.get<AttendanceMeResponse>("/attendance/me", {
          params: {
            class_session_id: params?.classSessionId,
            date_from: params?.dateFrom,
            date_to: params?.dateTo,
          },
        })
      ).data,
  });
}

export function useMarkAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: AttendanceMarkInput) =>
      (await apiClient.post<AttendanceRecord[]>("/attendance", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
  });
}

export function useUpdateAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: AttendanceStatus }) =>
      (await apiClient.put<AttendanceRecord>(`/attendance/${id}`, { status })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
  });
}

export function useClassAttendance(classId?: string, params?: { dateFrom?: string; dateTo?: string }) {
  return useQuery({
    queryKey: ["attendance", "class", classId, params],
    queryFn: async () =>
      (
        await apiClient.get<ClassAttendanceResponse>(`/attendance/${classId}`, {
          params: { date_from: params?.dateFrom, date_to: params?.dateTo },
        })
      ).data,
    enabled: Boolean(classId),
  });
}

export function useAttendanceReports(params?: { departmentId?: string; semesterId?: string }) {
  return useQuery({
    queryKey: ["attendance", "reports", params],
    queryFn: async () =>
      (
        await apiClient.get<AttendanceReportResponse>("/attendance/reports", {
          params: { department_id: params?.departmentId, semester_id: params?.semesterId },
        })
      ).data,
  });
}
