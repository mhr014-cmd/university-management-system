// React Query hooks: results (summary, approval workflow, transcript)
// See docs/API_Contract.md Section 5.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";
import { blobFromEnvelope, downloadBlob, exportReport } from "../../lib/exportClient";

export type ResultStatus = "submitted" | "published" | "rejected";
export type ApprovalDecision = "approve" | "reject";

export interface ResultCourseEntry {
  course_id: string;
  course_name: string;
  grade_letter: string;
  grade_point: number;
}

export interface ResultSemesterEntry {
  semester_id: string;
  semester_name: string;
  gpa: number;
  courses: ResultCourseEntry[];
}

export interface ResultsMeResponse {
  student_id: string;
  semesters: ResultSemesterEntry[];
}

export interface ResultSubmitEntry {
  student_id: string;
  grade_letter: string;
  grade_point: number;
}

export interface ResultSubmitResponse {
  exam_id: string;
  status: ResultStatus;
  submitted_at: string;
}

export interface PendingResultDetailEntry {
  result_id: string;
  student_id: string;
  student_name: string;
  grade_letter: string | null;
  grade_point: number | null;
}

export interface PendingResultQueueEntry {
  exam_id: string | null;
  exam_title: string | null;
  course_id: string;
  course_name: string;
  submitted_by_teacher_id: string;
  submitted_by_teacher_name: string;
  submitted_at: string;
  status: ResultStatus;
  results: PendingResultDetailEntry[];
}

export interface PendingResultsResponse {
  items: PendingResultQueueEntry[];
}

export interface ResultApprovalResponse {
  id: string;
  status: ResultStatus;
  approved_at: string | null;
}

export interface GradeDistributionEntry {
  grade_letter: string;
  count: number;
}

export interface ResultDetailEntry {
  student_id: string;
  student_name: string;
  course_name: string;
  exam_title: string | null;
  grade_letter: string;
  grade_point: number;
}

export interface ResultsReportResponse {
  scope: { department_id: string | null; semester_id: string | null; student_id: string | null };
  grade_distribution: GradeDistributionEntry[];
  pass_count: number;
  fail_count: number;
  average_gpa: number;
  details: ResultDetailEntry[];
}

export function useMyResults(params?: { semesterId?: string; studentId?: string }) {
  return useQuery({
    queryKey: ["results", "me", params],
    queryFn: async () =>
      (
        await apiClient.get<ResultsMeResponse>("/results/me", {
          params: { semester_id: params?.semesterId, student_id: params?.studentId },
        })
      ).data,
    // Don't fire a guaranteed-403 request before a Parent has picked a
    // child — same gating as useMyAttendance/useMySchedule/useExams.
    enabled: params?.studentId !== "",
  });
}

export function useSubmitResults() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ examId, results }: { examId: string; results: ResultSubmitEntry[] }) =>
      (await apiClient.post<ResultSubmitResponse>(`/results/${examId}/submit`, { results })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["results"] });
    },
  });
}

export function usePendingResults(status?: ResultStatus) {
  return useQuery({
    queryKey: ["results", "pending", status],
    queryFn: async () =>
      (await apiClient.get<PendingResultsResponse>("/results/pending", { params: { status } })).data,
  });
}

export function useApproveOrRejectResult() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      resultId,
      decision,
      comment,
    }: {
      resultId: string;
      decision: ApprovalDecision;
      comment?: string;
    }) =>
      (
        await apiClient.post<ResultApprovalResponse>(`/results/${resultId}/approve`, {
          decision,
          comment,
        })
      ).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["results"] });
    },
  });
}

export function useResultsReport(params?: { departmentId?: string; semesterId?: string; studentId?: string }) {
  return useQuery({
    queryKey: ["results", "reports", params],
    queryFn: async () =>
      (
        await apiClient.get<ResultsReportResponse>("/results/reports", {
          params: {
            department_id: params?.departmentId,
            semester_id: params?.semesterId,
            student_id: params?.studentId,
          },
        })
      ).data,
  });
}

// Feature 1 (final-verification-pass addition): Teacher Results View —
// GET /results/exam/{examId}, teacher-only, scoped server-side to exams
// the caller created.
export interface TeacherResultEntry {
  result_id: string;
  student_id: string;
  student_name: string;
  grade_letter: string | null;
  grade_point: number | null;
  status: ResultStatus;
  submitted_at: string;
  approved_at: string | null;
}

export interface TeacherExamResultsResponse {
  exam_id: string;
  exam_title: string;
  course_name: string;
  results: TeacherResultEntry[];
}

export function useExamResultsForTeacher(examId?: string) {
  return useQuery({
    queryKey: ["results", "exam", examId],
    queryFn: async () => (await apiClient.get<TeacherExamResultsResponse>(`/results/exam/${examId}`)).data,
    enabled: Boolean(examId),
  });
}

// Reports-module consistency enhancement: Results now supports the same
// Print/PDF/Excel export actions Attendance already had — reuses
// lib/exportClient.ts's exportReport() exactly like
// useExportAttendanceReportPdf/Excel (features/attendance/index.ts).
export function useExportResultsReportPdf() {
  return useMutation({
    mutationFn: async (params?: { departmentId?: string; semesterId?: string; studentId?: string }) =>
      exportReport(
        "/results/reports/pdf",
        {
          department_id: params?.departmentId,
          semester_id: params?.semesterId,
          student_id: params?.studentId,
        },
        "results-report.pdf",
      ),
  });
}

export function useExportResultsReportExcel() {
  return useMutation({
    mutationFn: async (params?: { departmentId?: string; semesterId?: string; studentId?: string }) =>
      exportReport(
        "/results/reports/excel",
        {
          department_id: params?.departmentId,
          semester_id: params?.semesterId,
          student_id: params?.studentId,
        },
        "results-report.xlsx",
      ),
  });
}

export function useDownloadTranscript() {
  return useMutation({
    mutationFn: async (studentId: string) => {
      // Base64 JSON envelope, not a raw blob response — see
      // lib/exportClient.ts's docstring.
      const response = await apiClient.get(`/results/${studentId}/transcript`);
      downloadBlob(blobFromEnvelope(response.data), response.data.filename ?? "transcript.pdf");
    },
  });
}
