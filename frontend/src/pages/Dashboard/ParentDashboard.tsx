// Parent Dashboard widgets (Milestone 10, production-polish audit update).
// Fee Status, Recent Results, and Attendance % are backed by GET /fees/me,
// GET /results/me, and GET /attendance/me, all with a student_id, verified
// server-side against parent_student_link (attendance access added in the
// post-M11 gap-closure pass — see Requirement_Traceability_Matrix.md).
// Upcoming Exams (gap closure) reuses GET /exams with the same student_id
// Parent-scoping convention, now that exam_service.list_exams() has a
// Parent branch — see Proposal_vs_Engineering_Additions.md.
//
// GET /users/me/children (added in the production-polish audit) now
// enumerates a Parent's linked children, so the child is selected from a
// dropdown (auto-selected when there's exactly one) instead of requiring a
// manually-typed Student ID.

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Award, Bell, CalendarClock, PieChart, Users, Wallet } from "lucide-react";
import { useMyAttendance } from "../../features/attendance";
import { useExams } from "../../features/exams";
import { useMyFees } from "../../features/fees";
import { useNotifications } from "../../features/notifications";
import { useMyResults } from "../../features/results";
import { useMyChildren } from "../../features/users";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { inputClass } from "../../components/ui/classNames";
import { DashboardCard } from "./DashboardCard";

export function ParentDashboard() {
  const { data: childrenData, isLoading: childrenLoading, isError: childrenError } = useMyChildren();
  const children = useMemo(() => childrenData?.children ?? [], [childrenData]);

  const [selectedStudentId, setSelectedStudentId] = useState("");

  useEffect(() => {
    if (!selectedStudentId && children.length > 0) {
      setSelectedStudentId(children[0].id);
    }
  }, [children, selectedStudentId]);

  const { data: fees, isError: feesError } = useMyFees({ studentId: selectedStudentId || undefined });
  const { data: results, isError: resultsError } = useMyResults({ studentId: selectedStudentId || undefined });
  const { data: attendance, isError: attendanceError } = useMyAttendance({ studentId: selectedStudentId });
  const { data: exams, isError: examsError } = useExams({ studentId: selectedStudentId });

  const mostRecentSemester = results?.semesters[0];
  const nextDueInvoice = (fees?.invoices ?? [])
    .filter((i) => i.status !== "paid")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];

  // Upcoming = not yet closed/published, with a scheduled date to show —
  // same client-side-computed-summary precedent as Teacher Dashboard's
  // Pending Grading widget (no dedicated "upcoming" filter on the backend).
  const upcomingExams = (exams?.items ?? [])
    .filter((e) => e.scheduled_at && (e.status === "scheduled" || e.status === "open"))
    .sort((a, b) => (a.scheduled_at as string).localeCompare(b.scheduled_at as string))
    .slice(0, 5);

  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-2 flex items-center gap-2">
          <Users className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Linked Child</p>
        </div>
        {childrenLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading your linked children...</p>
        ) : childrenError ? (
          <p className="text-sm text-red-600 dark:text-red-400">Unable to load linked children.</p>
        ) : children.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No children linked yet"
            description="Contact an administrator to link a child's record to your account."
          />
        ) : (
          <select
            value={selectedStudentId}
            onChange={(e) => setSelectedStudentId(e.target.value)}
            className={inputClass}
          >
            {children.map((child) => (
              <option key={child.id} value={child.id}>
                {child.first_name} {child.last_name}
              </option>
            ))}
          </select>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {!selectedStudentId ? (
          <DashboardCard title="Fee Status" icon={Wallet}>
            <p className="text-sm text-slate-400 dark:text-slate-500">Select a child above.</p>
          </DashboardCard>
        ) : feesError ? (
          <DashboardCard title="Fee Status" icon={Wallet}>
            <p className="text-sm text-red-600 dark:text-red-400">Not linked, or fee data unavailable.</p>
          </DashboardCard>
        ) : (
          <DashboardCard title="Fee Status" icon={Wallet}>
            <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {fees?.outstanding_balance.toFixed(2) ?? "—"}
            </p>
            {nextDueInvoice && (
              <p className="text-xs text-slate-500 dark:text-slate-400">Due: {nextDueInvoice.due_date}</p>
            )}
          </DashboardCard>
        )}

        {!selectedStudentId ? (
          <DashboardCard title="Attendance %" icon={PieChart}>
            <p className="text-sm text-slate-400 dark:text-slate-500">Select a child above.</p>
          </DashboardCard>
        ) : attendanceError ? (
          <DashboardCard title="Attendance %" icon={PieChart}>
            <p className="text-sm text-red-600 dark:text-red-400">Not linked, or attendance data unavailable.</p>
          </DashboardCard>
        ) : (
          <DashboardCard title="Attendance %" icon={PieChart}>
            <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {attendance?.overall_percentage.toFixed(1) ?? "—"}%
            </p>
            {attendance?.low_attendance_warning && (
              <p className="text-xs text-amber-600 dark:text-amber-400">Below 80% — low attendance warning</p>
            )}
          </DashboardCard>
        )}
        {!selectedStudentId ? (
          <DashboardCard title="Upcoming Exams" icon={CalendarClock}>
            <p className="text-sm text-slate-400 dark:text-slate-500">Select a child above.</p>
          </DashboardCard>
        ) : examsError ? (
          <DashboardCard title="Upcoming Exams" icon={CalendarClock}>
            <p className="text-sm text-red-600 dark:text-red-400">Not linked, or exam data unavailable.</p>
          </DashboardCard>
        ) : upcomingExams.length === 0 ? (
          <DashboardCard title="Upcoming Exams" icon={CalendarClock}>
            <p className="text-sm text-slate-400 dark:text-slate-500">No upcoming exams scheduled.</p>
          </DashboardCard>
        ) : (
          <DashboardCard title="Upcoming Exams" icon={CalendarClock}>
            <ul className="space-y-1.5">
              {upcomingExams.map((exam) => (
                <li key={exam.id} className="flex items-baseline justify-between text-sm">
                  <span className="text-slate-700 dark:text-slate-300">
                    {exam.title} <span className="text-slate-400 dark:text-slate-500">({exam.course_name})</span>
                  </span>
                  <span className="shrink-0 pl-2 text-xs text-slate-500 dark:text-slate-400">
                    {new Date(exam.scheduled_at as string).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          </DashboardCard>
        )}
      </div>

      <Card>
        <div className="mb-2 flex items-center gap-2">
          <Award className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Recent Results</p>
        </div>
        {!selectedStudentId ? (
          <p className="text-sm text-slate-400 dark:text-slate-500">Select a child above.</p>
        ) : resultsError ? (
          <p className="text-sm text-red-600 dark:text-red-400">Not linked, or result data unavailable.</p>
        ) : !mostRecentSemester || mostRecentSemester.courses.length === 0 ? (
          <EmptyState icon={Award} title="No published results yet" />
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
      </Card>

      <RecentNotificationsCard />
    </div>
  );
}

// Gap closure (production-readiness audit): the Notifications feature
// already existed (GET /notifications, generic across every role) but had
// no dashboard-level presence for Parent, only the standalone
// Notifications page. Reuses the existing hook, no new endpoint.
function RecentNotificationsCard() {
  const { data, isLoading } = useNotifications({ pageSize: 5 });

  return (
    <Card>
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Latest Notifications</p>
        </div>
        <Link to="/notifications" className="text-xs font-medium text-slate-600 hover:underline dark:text-slate-300">
          View all
        </Link>
      </div>
      {isLoading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading notifications...</p>
      ) : !data || data.items.length === 0 ? (
        <EmptyState icon={Bell} title="No notifications yet" />
      ) : (
        <ul className="space-y-2">
          {data.items.map((notification) => (
            <li key={notification.id} className="flex items-start gap-2 text-sm">
              <span
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                  notification.is_read ? "border border-slate-400" : "bg-slate-900 dark:bg-slate-100"
                }`}
              />
              <span className={notification.is_read ? "text-slate-500 dark:text-slate-400" : "font-medium text-slate-900 dark:text-slate-100"}>
                {notification.message}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
