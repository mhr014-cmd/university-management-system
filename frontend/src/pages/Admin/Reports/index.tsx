// Admin: Reports page (Milestone 10). Layout matches
// docs/UI_Wireframes.md Section 18: report-type tabs (Attendance/Results/
// Fees), shared Department/Semester filter dropdowns, per-tab table.
//
// Attendance tab reuses the existing GET /attendance/reports endpoint
// (Milestone 5) — no duplicated logic. Results/Fees tabs use the new
// Milestone 10 endpoints GET /results/reports and GET /fees/reports.

import { useState } from "react";
import { FileBarChart } from "lucide-react";
import { useDepartments } from "../../../features/departments";
import { useSemesters } from "../../../features/semesters";
import { useStudents } from "../../../features/users";
import { useAttendanceReports } from "../../../features/attendance";
import { useResultsReport } from "../../../features/results";
import { useFeesReport } from "../../../features/fees";
import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { PageLoader } from "../../../components/ui/PageLoader";
import { inputClass } from "../../../components/ui/classNames";

type ReportTab = "attendance" | "results" | "fees";

export default function AdminReportsPage() {
  const [tab, setTab] = useState<ReportTab>("attendance");
  const [departmentId, setDepartmentId] = useState("");
  const [semesterId, setSemesterId] = useState("");
  const [studentId, setStudentId] = useState("");

  const { data: departments } = useDepartments();
  const { data: semesters } = useSemesters();
  const { data: students } = useStudents(undefined, 1, 100);

  const filters = {
    departmentId: departmentId || undefined,
    semesterId: semesterId || undefined,
    studentId: studentId || undefined,
  };

  const attendanceReport = useAttendanceReports(filters);
  const resultsReport = useResultsReport(filters);
  const feesReport = useFeesReport(filters);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Reports</h1>

      <div className="flex items-center gap-1 rounded-md border border-slate-200 p-1 text-sm dark:border-slate-700 w-fit">
        {(["attendance", "results", "fees"] as ReportTab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 capitalize transition-colors ${
              tab === t
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-4 text-sm">
        <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">All Departments</option>
          {departments?.items.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select value={semesterId} onChange={(e) => setSemesterId(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">All Semesters</option>
          {semesters?.items.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <select value={studentId} onChange={(e) => setStudentId(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">All Students</option>
          {students?.items.map((s) => (
            <option key={s.id} value={s.id}>
              {s.first_name} {s.last_name}
            </option>
          ))}
        </select>
      </div>

      {tab === "attendance" &&
        (attendanceReport.isLoading || !attendanceReport.data ? (
          <PageLoader />
        ) : attendanceReport.data.summary.length === 0 ? (
          <EmptyState icon={FileBarChart} title="No attendance records in this scope" description="Try a different department or semester filter." />
        ) : (
          <Card className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-4 py-2.5">Student</th>
                  <th className="px-4 py-2.5">Percentage</th>
                </tr>
              </thead>
              <tbody>
                {attendanceReport.data.summary.map((entry) => (
                  <tr
                    key={entry.student_id}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                  >
                    <td className="px-4 py-2.5">{entry.student_name}</td>
                    <td className="px-4 py-2.5">{entry.percentage.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        ))}

      {tab === "results" &&
        (resultsReport.isLoading || !resultsReport.data ? (
          <PageLoader />
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Card>
                <p className="text-sm text-slate-500 dark:text-slate-400">Pass Count</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {resultsReport.data.pass_count}
                </p>
              </Card>
              <Card>
                <p className="text-sm text-slate-500 dark:text-slate-400">Fail Count</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {resultsReport.data.fail_count}
                </p>
              </Card>
              <Card>
                <p className="text-sm text-slate-500 dark:text-slate-400">Average GPA</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {resultsReport.data.average_gpa.toFixed(2)}
                </p>
              </Card>
            </div>
            {resultsReport.data.grade_distribution.length === 0 ? (
              <EmptyState icon={FileBarChart} title="No published results in this scope" />
            ) : (
              <Card className="overflow-x-auto p-0">
                <table className="w-full text-left text-sm">
                  <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
                    <tr className="border-b border-slate-200 dark:border-slate-700">
                      <th className="px-4 py-2.5">Grade Letter</th>
                      <th className="px-4 py-2.5">Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resultsReport.data.grade_distribution.map((entry) => (
                      <tr
                        key={entry.grade_letter}
                        className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                      >
                        <td className="px-4 py-2.5">{entry.grade_letter}</td>
                        <td className="px-4 py-2.5">{entry.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            )}
          </div>
        ))}

      {tab === "fees" &&
        (feesReport.isLoading || !feesReport.data ? (
          <PageLoader />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <p className="text-sm text-slate-500 dark:text-slate-400">Collected</p>
              <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                {feesReport.data.total_collected.toFixed(2)}
              </p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500 dark:text-slate-400">Outstanding</p>
              <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                {feesReport.data.total_outstanding.toFixed(2)}
              </p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500 dark:text-slate-400">Overdue</p>
              <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                {feesReport.data.total_overdue.toFixed(2)}
              </p>
            </Card>
          </div>
        ))}
    </div>
  );
}
