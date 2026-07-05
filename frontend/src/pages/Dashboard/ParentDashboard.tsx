// Parent Dashboard widgets (Milestone 10, production-polish audit update).
// Fee Status and Recent Results are backed by GET /fees/me and
// GET /results/me with a student_id, verified server-side against
// parent_student_link. Attendance % and Upcoming Exams render an honest
// "Not available" state — no endpoint exposes either to the Parent role.
//
// GET /users/me/children (added in the production-polish audit) now
// enumerates a Parent's linked children, so the child is selected from a
// dropdown (auto-selected when there's exactly one) instead of requiring a
// manually-typed Student ID.

import { useEffect, useMemo, useState } from "react";
import { useMyFees } from "../../features/fees";
import { useMyResults } from "../../features/results";
import { useMyChildren } from "../../features/users";
import { DashboardCard, NotAvailableCard } from "./DashboardCard";

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

  const mostRecentSemester = results?.semesters[0];
  const nextDueInvoice = (fees?.invoices ?? [])
    .filter((i) => i.status !== "paid")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];

  return (
    <div className="space-y-4">
      <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
        <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">Linked Child</p>
        {childrenLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading your linked children...</p>
        ) : childrenError ? (
          <p className="text-sm text-red-600 dark:text-red-400">Unable to load linked children.</p>
        ) : children.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No children are linked to your account yet. Contact an administrator if this is unexpected.
          </p>
        ) : (
          <select
            value={selectedStudentId}
            onChange={(e) => setSelectedStudentId(e.target.value)}
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          >
            {children.map((child) => (
              <option key={child.id} value={child.id}>
                {child.first_name} {child.last_name}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {!selectedStudentId ? (
          <DashboardCard title="Fee Status">
            <p className="text-sm text-slate-500 dark:text-slate-400">Select a child above.</p>
          </DashboardCard>
        ) : feesError ? (
          <DashboardCard title="Fee Status">
            <p className="text-sm text-red-600 dark:text-red-400">Not linked, or fee data unavailable.</p>
          </DashboardCard>
        ) : (
          <DashboardCard title="Fee Status">
            <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {fees?.outstanding_balance.toFixed(2) ?? "—"}
            </p>
            {nextDueInvoice && (
              <p className="text-xs text-slate-500 dark:text-slate-400">Due: {nextDueInvoice.due_date}</p>
            )}
          </DashboardCard>
        )}

        <NotAvailableCard title="Attendance %" />
        <NotAvailableCard title="Upcoming Exams" />
      </div>

      <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
        <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">Recent Results</p>
        {!selectedStudentId ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Select a child above.</p>
        ) : resultsError ? (
          <p className="text-sm text-red-600 dark:text-red-400">Not linked, or result data unavailable.</p>
        ) : !mostRecentSemester || mostRecentSemester.courses.length === 0 ? (
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
      </div>
    </div>
  );
}
