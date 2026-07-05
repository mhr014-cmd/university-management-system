// Attendance page (FR-026). Layout matches docs/UI_Wireframes.md Section 7:
// overall percentage bar with low-attendance warning badge (BR-008, 80%
// threshold), class filter, date range filter, and a records table.
// Entirely read-only for Student/Parent (per the wireframe's Buttons
// note: "No mutating actions").
//
// Known simplification: only the Table view is implemented. The
// wireframe's Calendar view (a month-grid alternative rendering of the
// same data) is not built — the toggle is present but Calendar mode
// shows a placeholder message. See PROJECT_PROGRESS.md's Milestone 5
// entry.

import { useState } from "react";
import { useMyAttendance } from "../../features/attendance";

type ViewMode = "table" | "calendar";

export default function AttendancePage() {
  const [view, setView] = useState<ViewMode>("table");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [classSessionId, setClassSessionId] = useState("");

  const { data, isLoading } = useMyAttendance({
    classSessionId: classSessionId || undefined,
    dateFrom: dateFrom || undefined,
    dateTo: dateTo || undefined,
  });

  if (isLoading || !data) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading attendance...</p>;
  }

  const allRecords = data.by_class_session.flatMap((cls) =>
    cls.records.map((record) => ({ ...record, course_name: cls.course_name })),
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Attendance</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setView("table")}
            className={`rounded px-3 py-1 text-sm ${view === "table" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "border border-slate-300 dark:border-slate-600"}`}
          >
            Table view
          </button>
          <button
            type="button"
            onClick={() => setView("calendar")}
            className={`rounded px-3 py-1 text-sm ${view === "calendar" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "border border-slate-300 dark:border-slate-600"}`}
          >
            Calendar view
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4 text-sm">
        <select
          value={classSessionId}
          onChange={(e) => setClassSessionId(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
        >
          <option value="">All Classes</option>
          {data.by_class_session.map((cls) => (
            <option key={cls.class_session_id} value={cls.class_session_id}>
              {cls.course_name}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
        />
        <span>to</span>
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
        />
      </div>

      <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold">Overall: {data.overall_percentage}%</span>
          <div className="h-2 w-40 rounded bg-slate-200 dark:bg-slate-700">
            <div
              className="h-2 rounded bg-slate-900 dark:bg-slate-100"
              style={{ width: `${Math.min(data.overall_percentage, 100)}%` }}
            />
          </div>
          {data.low_attendance_warning && (
            <span className="rounded border border-amber-300 bg-amber-50 px-2 py-1 text-xs text-amber-700 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300">
              ⚠ Below 80%
            </span>
          )}
        </div>
      </div>

      {view === "table" ? (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="py-2">Date</th>
              <th className="py-2">Class</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {allRecords
              .sort((a, b) => b.date.localeCompare(a.date))
              .map((record, i) => (
                <tr
                  key={i}
                  className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="py-2">{record.date}</td>
                  <td className="py-2">{record.course_name}</td>
                  <td className="py-2 capitalize">{record.status}</td>
                </tr>
              ))}
          </tbody>
        </table>
      ) : null}
      {view === "table" && allRecords.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">No attendance records yet.</p>
      )}
      {view !== "table" && (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Calendar view is not yet implemented — use Table view.
        </p>
      )}
    </div>
  );
}
