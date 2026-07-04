// React Query hooks: schedule (timetable, conflicts, change requests, and
// the Derived class-session/enrollment creation endpoints — see
// docs/API_Contract.md Section 7).

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export type DayOfWeek = "Mon" | "Tue" | "Wed" | "Thu" | "Fri" | "Sat" | "Sun";

export interface ScheduleMeEntry {
  schedule_entry_id: string;
  class_session_id: string;
  course_name: string;
  room_name: string;
  day_of_week: DayOfWeek;
  start_time: string;
  end_time: string;
}

export interface ScheduleConflict {
  type: "room" | "teacher";
  conflicting_entry_ids: string[];
  day_of_week: DayOfWeek;
  overlap_start: string;
  overlap_end: string;
}

export interface ScheduleEntryInput {
  class_session_id: string;
  room_id: string;
  teacher_id: string;
  day_of_week: DayOfWeek;
  start_time: string;
  end_time: string;
}

export interface ClassSessionInput {
  course_id: string;
  teacher_id: string;
  semester_id: string;
  section_label: string;
}

export interface EnrollmentInput {
  student_id: string;
  class_session_id: string;
}

export interface RequestedChangeInput {
  day_of_week?: DayOfWeek;
  start_time?: string;
  end_time?: string;
  room_id?: string;
}

export function useMySchedule() {
  return useQuery({
    queryKey: ["schedule", "me"],
    queryFn: async () => (await apiClient.get<{ entries: ScheduleMeEntry[] }>("/schedule/me")).data,
  });
}

export function useScheduleConflicts(semesterId?: string) {
  return useQuery({
    queryKey: ["schedule", "conflicts", semesterId],
    queryFn: async () =>
      (
        await apiClient.get<{ conflicts: ScheduleConflict[] }>("/schedule/conflicts", {
          params: { semester_id: semesterId },
        })
      ).data,
    enabled: false,
  });
}

export function useCreateScheduleEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ScheduleEntryInput) => (await apiClient.post("/schedule", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
    },
  });
}

export function useCreateClassSession() {
  return useMutation({
    mutationFn: async (payload: ClassSessionInput) =>
      (await apiClient.post<{ id: string }>("/schedule/class-sessions", payload)).data,
  });
}

export function useCreateEnrollment() {
  return useMutation({
    mutationFn: async (payload: EnrollmentInput) =>
      (await apiClient.post<{ id: string }>("/schedule/enrollments", payload)).data,
  });
}

export function useCreateChangeRequest() {
  return useMutation({
    mutationFn: async (payload: { schedule_entry_id: string; requested_change: RequestedChangeInput }) =>
      (await apiClient.post("/schedule/change-requests", payload)).data,
  });
}

export interface RosterEntry {
  student_id: string;
  first_name: string;
  last_name: string;
}

export function useClassSessionRoster(classSessionId?: string) {
  return useQuery({
    queryKey: ["schedule", "class-sessions", classSessionId, "roster"],
    queryFn: async () =>
      (
        await apiClient.get<{ class_session_id: string; students: RosterEntry[] }>(
          `/schedule/class-sessions/${classSessionId}/roster`,
        )
      ).data,
    enabled: Boolean(classSessionId),
  });
}
