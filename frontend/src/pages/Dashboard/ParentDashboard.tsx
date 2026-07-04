// Parent Dashboard widgets (Milestone 10) — approved Finding E: build only
// from data that is genuinely available. Fee Status and Recent Results are
// implemented (both already Parent-accessible via GET /fees/me and
// GET /results/me with a student_id, verified server-side against
// parent_student_link). Attendance % and Upcoming Exams render an honest
// "Not available" state — no endpoint exposes either to the Parent role.
//
// No endpoint anywhere enumerates a Parent's linked children (same known
// gap noted in ResultsView/FeeCentre since Milestones 7-8), so there is no
// dropdown "child selector" to populate. A manual Student ID field is the
// only genuinely-available way for a Parent to select which linked child
// to view — consistent with that documented gap, not a new limitation.

import { useState } from "react";
import { useMyFees } from "../../features/fees";
import { useMyResults } from "../../features/results";
import { DashboardCard, NotAvailableCard } from "./DashboardCard";

export function ParentDashboard() {
  const [studentId, setStudentId] = useState("");
  const [submittedStudentId, setSubmittedStudentId] = useState("");

  const { data: fees, isError: feesError } = useMyFees({ studentId: submittedStudentId || undefined });
  const { data: results, isError: resultsError } = useMyResults({ studentId: submittedStudentId || undefined });

  const mostRecentSemester = results?.semesters[0];
  const nextDueInvoice = (fees?.invoices ?? [])
    .filter((i) => i.status !== "paid")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];

  return (
    <div className="space-y-4">
      <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
        <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">
          Linked Child — enter your child's Student ID to view their Fee Status and Recent Results.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            placeholder="Student ID"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <button
            type="button"
            onClick={() => setSubmittedStudentId(studentId)}
            disabled={!studentId}
            className="rounded bg-slate-900 px-3 py-1 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
          >
            View
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {!submittedStudentId ? (
          <DashboardCard title="Fee Status">
            <p className="text-sm text-slate-500 dark:text-slate-400">Enter a Student ID above.</p>
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
        {!submittedStudentId ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Enter a Student ID above.</p>
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
                <tr key={course.course_id} className="border-b border-slate-100 dark:border-slate-800">
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
