// React Query hooks: attendance (summary, marking, corrections, reports)
// See docs/API_Contract.md Section 4.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";
import { exportReport } from "../../lib/exportClient";

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
  scope: { department_id: string | null; semester_id: string | null; student_id: string | null };
  summary: AttendanceReportEntry[];
}

export function useMyAttendance(
  params?: { classSessionId?: string; dateFrom?: string; dateTo?: string; studentId?: string },
) {
  return useQuery({
    queryKey: ["attendance", "me", params],
    queryFn: async () =>
      (
        await apiClient.get<AttendanceMeResponse>("/attendance/me", {
          params: {
            class_session_id: params?.classSessionId,
            date_from: params?.dateFrom,
            date_to: params?.dateTo,
            // Parent scoping (gap closure): required for Parent, ignored
            // for Student — mirrors useMyFees/useMyResults's student_id.
            student_id: params?.studentId,
          },
        })
      ).data,
    // Don't fire a guaranteed-403 request before a Parent has picked a
    // child — same gating as useMySchedule's Parent path.
    enabled: params?.studentId !== "",
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

export function useAttendanceReports(params?: { departmentId?: string; semesterId?: string; studentId?: string }) {
  return useQuery({
    queryKey: ["attendance", "reports", params],
    queryFn: async () =>
      (
        await apiClient.get<AttendanceReportResponse>("/attendance/reports", {
          params: {
            department_id: params?.departmentId,
            semester_id: params?.semesterId,
            student_id: params?.studentId,
          },
        })
      ).data,
  });
}

// Named "export" (not "download") since these trigger report generation
// on the backend before the file comes back — reporting infrastructure
// vertical slice (Version 1.2); reuses lib/exportClient.ts's shared
// request-then-download behavior, which future Results/Fees/Timetable/
// Users report exports should reuse the same way.
export function useExportAttendanceReportPdf() {
  return useMutation({
    mutationFn: async (params?: { departmentId?: string; semesterId?: string; studentId?: string }) =>
      exportReport(
        "/attendance/reports/pdf",
        {
          department_id: params?.departmentId,
          semester_id: params?.semesterId,
          student_id: params?.studentId,
        },
        "attendance-report.pdf",
      ),
  });
}

export function useExportAttendanceReportExcel() {
  return useMutation({
    mutationFn: async (params?: { departmentId?: string; semesterId?: string; studentId?: string }) =>
      exportReport(
        "/attendance/reports/excel",
        {
          department_id: params?.departmentId,
          semester_id: params?.semesterId,
          student_id: params?.studentId,
        },
        "attendance-report.xlsx",
      ),
  });
}
