// Student Dashboard widgets (Milestone 10) — docs/UI_Wireframes.md Section 2
// Role Visibility: Upcoming Exams, Attendance %, Fee Status, Recent Results.
// All data sourced from existing endpoints already used elsewhere
// (ExamList, Attendance, FeeCentre, ResultsView) — no new backend scope.

import { Link } from "react-router-dom";
import { useExams } from "../../features/exams";
import { useMyAttendance } from "../../features/attendance";
import { useMyFees } from "../../features/fees";
import { useMyResults } from "../../features/results";
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
      <DashboardCard title="Upcoming Exams">
        {upcoming.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No upcoming exams.</p>
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
        <Link to="/exams" className="mt-2 inline-block text-sm text-slate-900 underline dark:text-slate-100">
          View all
        </Link>
      </DashboardCard>

      <DashboardCard title="Attendance %">
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
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading...</p>
        )}
        <Link to="/attendance" className="mt-2 inline-block text-sm text-slate-900 underline dark:text-slate-100">
          View all
        </Link>
      </DashboardCard>

      <DashboardCard title="Fee Status">
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
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading...</p>
        )}
        <Link to="/fees" className="mt-2 inline-block text-sm text-slate-900 underline dark:text-slate-100">
          View Fee Centre
        </Link>
      </DashboardCard>

      <div className="rounded border border-slate-200 p-4 dark:border-slate-700 sm:col-span-3">
        <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">Recent Results</p>
        {!mostRecentSemester || mostRecentSemester.courses.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No published results yet.</p>
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
        <Link to="/results" className="mt-2 inline-block text-sm text-slate-900 underline dark:text-slate-100">
          View full results
        </Link>
      </div>
    </div>
  );
}
