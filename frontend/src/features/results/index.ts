// React Query hooks: results (summary, approval workflow, transcript)
// See docs/API_Contract.md Section 5.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

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

export interface ResultsReportResponse {
  scope: { department_id: string | null; semester_id: string | null; student_id: string | null };
  grade_distribution: GradeDistributionEntry[];
  pass_count: number;
  fail_count: number;
  average_gpa: number;
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

export function useDownloadTranscript() {
  return useMutation({
    mutationFn: async (studentId: string) => {
      const response = await apiClient.get(`/results/${studentId}/transcript`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "transcript.pdf";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
  });
}
