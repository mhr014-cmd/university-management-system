// Student Dashboard widgets (Milestone 10) — docs/UI_Wireframes.md Section 2
// Role Visibility: Upcoming Exams, Attendance %, Fee Status, Recent Results.
// All data sourced from existing endpoints already used elsewhere
// (ExamList, Attendance, FeeCentre, ResultsView) — no new backend scope.

import { Award, CalendarClock, PieChart, Wallet } from "lucide-react";
import { useExams } from "../../features/exams";
import { useMyAttendance } from "../../features/attendance";
import { useMyFees } from "../../features/fees";
import { useMyResults } from "../../features/results";
import { RecentNotificationsCard } from "../../components/RecentNotificationsCard";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import { DashboardCard } from "./DashboardCard";

export function StudentDashboard() {
  const { data: exams } = useExams({ pageSize: 100 });
  const { data: attendance } = useMyAttendance();
  const { data: fees } = useMyFees();
  const { data: results } = useMyResults();

  const upcoming = (exams?.items ?? [])
    .filter((e) => (e.status === "scheduled" || e.status === "open") && e.scheduled_at)
    .sort((a, b) => (a.scheduled_at ?? "").localeCompare(b.scheduled_at ?? ""))
    .slice(0, 5);

  const nextDueInvoice = (fees?.invoices ?? [])
    .filter((i) => i.status !== "paid")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];

  const mostRecentSemester = results?.semesters[0];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <DashboardCard title="Upcoming Exams" icon={CalendarClock} to="/exams">
        {upcoming.length === 0 ? (
          <p className="text-sm text-slate-400 dark:text-slate-500">No upcoming exams.</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {upcoming.map((exam) => (
              <li key={exam.id}>
                {exam.title} — {exam.course_name} —{" "}
                {new Date(exam.scheduled_at!).toLocaleDateString()}
              </li>
            ))}
          </ul>
        )}
        <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">View all</span>
      </DashboardCard>

      <DashboardCard title="Attendance %" icon={PieChart} to="/attendance">
        {attendance ? (
          <>
            <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {attendance.overall_percentage.toFixed(1)}%
            </p>
            {attendance.low_attendance_warning && (
              <p className="mt-1 text-xs font-medium text-red-600 dark:text-red-400">Low attendance warning</p>
            )}
          </>
        ) : (
          <Skeleton className="h-8 w-20" />
        )}
        <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">View all</span>
      </DashboardCard>

      <DashboardCard title="Fee Status" icon={Wallet} to="/fees">
        {fees ? (
          <>
            <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {fees.outstanding_balance.toFixed(2)}
            </p>
            {nextDueInvoice && (
              <p className="text-xs text-slate-500 dark:text-slate-400">Due: {nextDueInvoice.due_date}</p>
            )}
          </>
        ) : (
          <Skeleton className="h-8 w-24" />
        )}
        <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">
          View Fee Centre
        </span>
      </DashboardCard>

      <Card to="/results" hoverable className="sm:col-span-3">
        <div className="mb-2 flex items-center gap-2">
          <Award className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Recent Results</p>
        </div>
        {!mostRecentSemester || mostRecentSemester.courses.length === 0 ? (
          <EmptyState icon={Award} title="No published results yet" description="Results will appear here once your teacher submits and an admin publishes them." />
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="py-2">Course</th>
                <th className="py-2">Grade</th>
                <th className="py-2">Semester</th>
              </tr>
            </thead>
            <tbody>
              {mostRecentSemester.courses.slice(0, 5).map((course) => (
                <tr
                  key={course.course_id}
                  className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="py-2">{course.course_name}</td>
                  <td className="py-2">{course.grade_letter}</td>
                  <td className="py-2">{mostRecentSemester.semester_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <span className="mt-2 inline-block text-sm font-medium text-slate-900 dark:text-slate-100">
          View full results →
        </span>
      </Card>

      <div className="sm:col-span-3">
        <RecentNotificationsCard />
      </div>
    </div>
  );
}
