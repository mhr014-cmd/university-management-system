// React Query hooks: exams (list, builder, submission, grading)
// See docs/API_Contract.md Section 3.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export type ExamType = "mcq" | "written" | "practical_coding" | "mixed";
export type ExamStatus = "draft" | "scheduled" | "open" | "closed" | "published";
export type QuestionType = "mcq" | "short_answer" | "descriptive" | "coding";
export type ExamSubmissionStatus = "in_progress" | "submitted" | "graded";

export interface QuestionOption {
  id: string;
  option_text: string;
  is_correct: boolean | null;
}

export interface QuestionOptionInput {
  option_text: string;
  is_correct: boolean;
}

export interface QuestionInput {
  question_text: string;
  question_type: QuestionType;
  marks: number;
  hint?: string;
  order_index: number;
  options: QuestionOptionInput[];
}

export interface Question {
  id: string;
  question_text: string;
  question_type: QuestionType;
  marks: number;
  hint: string | null;
  order_index: number;
  options: QuestionOption[] | null;
  awarded_marks: number | null;
  feedback: string | null;
}

export interface Exam {
  id: string;
  class_session_id: string;
  created_by_teacher_id: string;
  title: string;
  exam_type: ExamType;
  time_limit_minutes: number;
  status: ExamStatus;
  scheduled_at: string | null;
  created_at: string;
  updated_at: string;
  questions: Question[];
}

export interface ExamListItem {
  id: string;
  title: string;
  class_session_id: string;
  exam_type: ExamType;
  time_limit_minutes: number;
  status: ExamStatus;
  scheduled_at: string | null;
}

export interface ExamCreateInput {
  class_session_id: string;
  title: string;
  exam_type: ExamType;
  time_limit_minutes: number;
  questions: QuestionInput[];
}

export interface ExamUpdateInput {
  title?: string;
  exam_type?: ExamType;
  time_limit_minutes?: number;
  status?: ExamStatus;
  questions?: QuestionInput[];
}

export interface ExamStartResponse {
  submission_id: string;
  exam_id: string;
  status: ExamSubmissionStatus;
  started_at: string;
}

export interface AnswerInput {
  question_id: string;
  answer_text?: string;
  selected_option_id?: string;
}

export interface ExamSubmitResponse {
  submission_id: string;
  exam_id: string;
  status: ExamSubmissionStatus;
  submitted_at: string;
}

export interface GradeInput {
  answer_id: string;
  awarded_marks: number;
  feedback?: string;
}

export interface ExamGradeResponse {
  submission_id: string;
  status: ExamSubmissionStatus;
  total_awarded_marks: number;
}

export interface ExamResultsSubmissionSummary {
  student_id: string;
  submission_id: string;
  total_awarded_marks: number;
  status: ExamSubmissionStatus;
}

export interface ExamResultsResponse {
  exam_id: string;
  submissions: ExamResultsSubmissionSummary[];
}

export interface SubmissionQuestionDetail {
  question_id: string;
  question_text: string;
  question_type: QuestionType;
  marks: number;
  order_index: number;
  answer_id: string | null;
  answer_text: string | null;
  selected_option_id: string | null;
  awarded_marks: number | null;
  feedback: string | null;
}

export interface ExamSubmissionDetail {
  submission_id: string;
  exam_id: string;
  student_id: string;
  status: ExamSubmissionStatus;
  questions: SubmissionQuestionDetail[];
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export function useExams(params?: { classSessionId?: string; status?: string; page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: ["exams", params],
    queryFn: async () =>
      (
        await apiClient.get<PaginatedResponse<ExamListItem>>("/exams", {
          params: {
            class_session_id: params?.classSessionId,
            status: params?.status,
            page: params?.page ?? 1,
            page_size: params?.pageSize ?? 20,
          },
        })
      ).data,
  });
}

export function useExam(examId?: string) {
  return useQuery({
    queryKey: ["exams", examId],
    queryFn: async () => (await apiClient.get<Exam>(`/exams/${examId}`)).data,
    enabled: Boolean(examId),
  });
}

export function useCreateExam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ExamCreateInput) => (await apiClient.post<Exam>("/exams", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams"] });
    },
  });
}

export function useUpdateExam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: ExamUpdateInput }) =>
      (await apiClient.put<Exam>(`/exams/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams"] });
    },
  });
}

export function useDeleteExam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/exams/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams"] });
    },
  });
}

export function useStartExam() {
  return useMutation({
    mutationFn: async (examId: string) => (await apiClient.post<ExamStartResponse>(`/exams/${examId}/start`)).data,
  });
}

export function useSubmitExam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ examId, answers }: { examId: string; answers: AnswerInput[] }) =>
      (await apiClient.post<ExamSubmitResponse>(`/exams/${examId}/submit`, { answers })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams"] });
    },
  });
}

export function useGradeExam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      examId,
      submissionId,
      grades,
    }: {
      examId: string;
      submissionId: string;
      grades: GradeInput[];
    }) =>
      (
        await apiClient.post<ExamGradeResponse>(`/exams/${examId}/grade`, {
          submission_id: submissionId,
          grades,
        })
      ).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams"] });
    },
  });
}

export function useSubmissionDetail(examId?: string, submissionId?: string) {
  return useQuery({
    queryKey: ["exams", examId, "submissions", submissionId],
    queryFn: async () =>
      (await apiClient.get<ExamSubmissionDetail>(`/exams/${examId}/submissions/${submissionId}`)).data,
    enabled: Boolean(examId) && Boolean(submissionId),
  });
}

export function useExamResults(examId?: string) {
  return useQuery({
    queryKey: ["exams", examId, "results"],
    queryFn: async () => (await apiClient.get<ExamResultsResponse>(`/exams/${examId}/results`)).data,
    enabled: Boolean(examId),
  });
}
