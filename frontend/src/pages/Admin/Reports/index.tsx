// Admin: Reports page (Milestone 10). Layout matches
// docs/UI_Wireframes.md Section 18: report-type tabs (Attendance/Results/
// Fees), shared Department/Semester filter dropdowns, per-tab table.
//
// Attendance tab reuses the existing GET /attendance/reports endpoint
// (Milestone 5) — no duplicated logic. Results/Fees tabs use the new
// Milestone 10 endpoints GET /results/reports and GET /fees/reports.

import { useState } from "react";
import { useDepartments } from "../../../features/departments";
import { useSemesters } from "../../../features/semesters";
import { useAttendanceReports } from "../../../features/attendance";
import { useResultsReport } from "../../../features/results";
import { useFeesReport } from "../../../features/fees";

type ReportTab = "attendance" | "results" | "fees";

export default function AdminReportsPage() {
  const [tab, setTab] = useState<ReportTab>("attendance");
  const [departmentId, setDepartmentId] = useState("");
  const [semesterId, setSemesterId] = useState("");

  const { data: departments } = useDepartments();
  const { data: semesters } = useSemesters();

  const filters = { departmentId: departmentId || undefined, semesterId: semesterId || undefined };

  const attendanceReport = useAttendanceReports(filters);
  const resultsReport = useResultsReport(filters);
  const feesReport = useFeesReport(filters);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Reports</h1>

      <div className="flex items-center gap-2 text-sm">
        {(["attendance", "results", "fees"] as ReportTab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 capitalize ${
              tab === t
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                : "border border-slate-300 dark:border-slate-600"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-4 text-sm">
        <select
          value={departmentId}
          onChange={(e) => setDepartmentId(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
        >
          <option value="">All Departments</option>
          {departments?.items.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          value={semesterId}
          onChange={(e) => setSemesterId(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
        >
          <option value="">All Semesters</option>
          {semesters?.items.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {tab === "attendance" &&
        (attendanceReport.isLoading || !attendanceReport.data ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading...</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="py-2">Student</th>
                <th className="py-2">Percentage</th>
              </tr>
            </thead>
            <tbody>
              {attendanceReport.data.summary.map((entry) => (
                <tr key={entry.student_id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2">{entry.student_id}</td>
                  <td className="py-2">{entry.percentage.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}

      {tab === "results" &&
        (resultsReport.isLoading || !resultsReport.data ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading...</p>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
                <p className="text-sm text-slate-500 dark:text-slate-400">Pass Count</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {resultsReport.data.pass_count}
                </p>
              </div>
              <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
                <p className="text-sm text-slate-500 dark:text-slate-400">Fail Count</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {resultsReport.data.fail_count}
                </p>
              </div>
              <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
                <p className="text-sm text-slate-500 dark:text-slate-400">Average GPA</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {resultsReport.data.average_gpa.toFixed(2)}
                </p>
              </div>
            </div>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="py-2">Grade Letter</th>
                  <th className="py-2">Count</th>
                </tr>
              </thead>
              <tbody>
                {resultsReport.data.grade_distribution.map((entry) => (
                  <tr key={entry.grade_letter} className="border-b border-slate-100 dark:border-slate-800">
                    <td className="py-2">{entry.grade_letter}</td>
                    <td className="py-2">{entry.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {resultsReport.data.grade_distribution.length === 0 && (
              <p className="text-sm text-slate-500 dark:text-slate-400">No published results in this scope.</p>
            )}
          </div>
        ))}

      {tab === "fees" &&
        (feesReport.isLoading || !feesReport.data ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading...</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
              <p className="text-sm text-slate-500 dark:text-slate-400">Collected</p>
              <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                {feesReport.data.total_collected.toFixed(2)}
              </p>
            </div>
            <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
              <p className="text-sm text-slate-500 dark:text-slate-400">Outstanding</p>
              <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                {feesReport.data.total_outstanding.toFixed(2)}
              </p>
            </div>
            <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
              <p className="text-sm text-slate-500 dark:text-slate-400">Overdue</p>
              <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                {feesReport.data.total_overdue.toFixed(2)}
              </p>
            </div>
          </div>
        ))}
    </div>
  );
}
