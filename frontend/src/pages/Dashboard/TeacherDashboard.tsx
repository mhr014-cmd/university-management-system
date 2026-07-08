// Teacher Dashboard widgets (Milestone 10) — docs/UI_Wireframes.md Section 2
// Role Visibility: Classes Today, Pending Grading count.
//
// Schedule-change-request status widget is intentionally omitted — no
// endpoint exists to query "my pending schedule-change-request status"
// for the calling Teacher (approved Milestone 10 Finding C; see
// docs/UI_Wireframes.md Section 2 Known Limitations).
//
// Pending Grading is computed client-side from the existing per-exam
// results endpoint (approved Finding B — no backend aggregate endpoint
// was added for this count): for every one of the Teacher's own exams
// not yet published, count submissions still awaiting a grade.

import { useQueries } from "@tanstack/react-query";
import { CalendarDays, ClipboardList } from "lucide-react";
import { apiClient } from "../../lib/apiClient";
import { useMySchedule } from "../../features/schedule";
import { useExams, type ExamResultsResponse } from "../../features/exams";
import { RecentNotificationsCard } from "../../components/RecentNotificationsCard";
import { DashboardCard } from "./DashboardCard";

const DAY_ABBREVIATIONS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

export function TeacherDashboard() {
  const { data: schedule } = useMySchedule();
  const { data: exams } = useExams({ pageSize: 100 });

  const today = DAY_ABBREVIATIONS[new Date().getDay()];
  const classesToday = (schedule?.entries ?? []).filter((entry) => entry.day_of_week === today);

  const ungradedCandidateExams = (exams?.items ?? []).filter(
    (e) => e.status === "open" || e.status === "closed",
  );

  const resultsQueries = useQueries({
    queries: ungradedCandidateExams.map((exam) => ({
      queryKey: ["exams", exam.id, "results"],
      queryFn: async () => (await apiClient.get<ExamResultsResponse>(`/exams/${exam.id}/results`)).data,
    })),
  });

  const pendingGradingCount = resultsQueries.reduce((sum, query) => {
    const submissions = query.data?.submissions ?? [];
    return sum + submissions.filter((s) => s.status !== "graded").length;
  }, 0);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <DashboardCard title="Classes Today" icon={CalendarDays} to="/timetable">
          {classesToday.length === 0 ? (
            <p className="text-sm text-slate-400 dark:text-slate-500">No classes scheduled today.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {classesToday.map((entry) => (
                <li key={entry.schedule_entry_id}>
                  {entry.course_name} — {entry.start_time}–{entry.end_time} ({entry.room_name})
                </li>
              ))}
            </ul>
          )}
          <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">
            View timetable
          </span>
        </DashboardCard>

        <DashboardCard title="Pending Grading" icon={ClipboardList} to="/exams">
          <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{pendingGradingCount}</p>
          <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">
            View exams
          </span>
        </DashboardCard>
      </div>

      <RecentNotificationsCard />
    </div>
  );
}
