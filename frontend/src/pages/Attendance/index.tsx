// Attendance page (FR-026). Layout matches docs/UI_Wireframes.md Section 7:
// overall percentage bar with low-attendance warning badge (BR-008, 80%
// threshold), class filter, date range filter, and a records table.
// Entirely read-only for Student/Parent (per the wireframe's Buttons
// note: "No mutating actions").
//
// Gap closure (post-M11 audit): Calendar view (a month-grid rendering of
// the same GET /attendance/me data — no new endpoint) replaces the
// previous placeholder message.
//
// Gap closure (GC-2): GET /attendance/me already accepted Parent +
// student_id server-side, but this page never offered a Parent a way to
// pick which linked child to view, so a Parent following the "Attendance"
// nav link got a 403 the page didn't handle. Reuses the exact child-
// selector pattern already proven in Timetable.tsx's ParentScheduleGrid
// (useMyChildren, auto-select the first/only child) — no new hook, no
// new endpoint, no change to the Student path below.

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CalendarDays, ChevronLeft, ChevronRight, Users } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import {
  useExportAttendanceReportCsv,
  useExportAttendanceReportExcel,
  useExportAttendanceReportPdf,
  useMyAttendance,
} from "../../features/attendance";
import type { AttendanceStatus } from "../../features/attendance";
import { useMyChildren } from "../../features/users";
import { Badge, type BadgeTone } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";
import { ProgressBar } from "../../components/ui/ProgressBar";
import { ReportToolbar } from "../../components/ui/ReportToolbar";
import { inputClass } from "../../components/ui/classNames";

type ViewMode = "table" | "calendar";

const statusTone: Record<AttendanceStatus, BadgeTone> = {
  present: "green",
  absent: "red",
  late: "amber",
  excused: "blue",
};

const statusDotClass: Record<AttendanceStatus, string> = {
  present: "bg-green-500",
  absent: "bg-red-500",
  late: "bg-amber-500",
  excused: "bg-blue-500",
};

const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

interface AttendanceRecordWithCourse {
  date: string;
  status: AttendanceStatus;
  course_name: string;
}

function CalendarMonthView({ records }: { records: AttendanceRecordWithCourse[] }) {
  const recordsByDate = useMemo(() => {
    const map = new Map<string, AttendanceRecordWithCourse[]>();
    for (const record of records) {
      const list = map.get(record.date) ?? [];
      list.push(record);
      map.set(record.date, list);
    }
    return map;
  }, [records]);

  const mostRecentDate = records.length > 0 ? records.map((r) => r.date).sort().slice(-1)[0] : undefined;
  const initialMonth = mostRecentDate ? new Date(`${mostRecentDate}T00:00:00`) : new Date();
  const [visibleMonth, setVisibleMonth] = useState(new Date(initialMonth.getFullYear(), initialMonth.getMonth(), 1));

  const year = visibleMonth.getFullYear();
  const month = visibleMonth.getMonth();
  const firstWeekday = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (number | null)[] = [
    ...Array.from({ length: firstWeekday }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  const formatDateKey = (day: number) => {
    const mm = String(month + 1).padStart(2, "0");
    const dd = String(day).padStart(2, "0");
    return `${year}-${mm}-${dd}`;
  };

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <Button
          variant="secondary"
          size="sm"
          aria-label="Previous month"
          onClick={() => setVisibleMonth(new Date(year, month - 1, 1))}
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </Button>
        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          {visibleMonth.toLocaleDateString(undefined, { month: "long", year: "numeric" })}
        </span>
        <Button
          variant="secondary"
          size="sm"
          aria-label="Next month"
          onClick={() => setVisibleMonth(new Date(year, month + 1, 1))}
        >
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-slate-500 dark:text-slate-400">
        {WEEKDAY_LABELS.map((label) => (
          <div key={label} className="py-1">{label}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {cells.map((day, i) => {
          if (day === null) {
            return <div key={`blank-${i}`} className="aspect-square rounded-md" />;
          }
          const dateKey = formatDateKey(day);
          const dayRecords = recordsByDate.get(dateKey) ?? [];
          return (
            <div
              key={dateKey}
              className="flex aspect-square flex-col items-center justify-start gap-0.5 rounded-md border border-slate-100 p-1 dark:border-slate-800"
              title={dayRecords.map((r) => `${r.course_name}: ${r.status}`).join(", ") || undefined}
            >
              <span className="text-xs text-slate-600 dark:text-slate-300">{day}</span>
              <div className="flex flex-wrap justify-center gap-0.5">
                {dayRecords.map((r, idx) => (
                  <span key={idx} className={`h-1.5 w-1.5 rounded-full ${statusDotClass[r.status]}`} aria-hidden="true" />
                ))}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
        {(Object.keys(statusDotClass) as AttendanceStatus[]).map((status) => (
          <span key={status} className="flex items-center gap-1">
            <span className={`h-1.5 w-1.5 rounded-full ${statusDotClass[status]}`} aria-hidden="true" />
            {status}
          </span>
        ))}
      </div>
    </Card>
  );
}

export default function AttendancePage() {
  const { user } = useAuth();

  if (user?.role === "parent") {
    return <ParentAttendanceView />;
  }
  return <AttendanceContent />;
}

// Reuses the exact child-selector pattern already proven in
// Timetable.tsx's ParentScheduleGrid (useMyChildren, auto-select the
// first/only linked child) — same component, same convention.
function ParentAttendanceView() {
  const { data: childrenData, isLoading: childrenLoading, isError: childrenError } = useMyChildren();
  const children = useMemo(() => childrenData?.children ?? [], [childrenData]);
  const [selectedStudentId, setSelectedStudentId] = useState("");

  useEffect(() => {
    if (!selectedStudentId && children.length > 0) {
      setSelectedStudentId(children[0].id);
    }
  }, [children, selectedStudentId]);

  const selectedChild = children.find((c) => c.id === selectedStudentId);
  const exportPdf = useExportAttendanceReportPdf();
  const exportExcel = useExportAttendanceReportExcel();
  const exportCsv = useExportAttendanceReportCsv();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Attendance</h1>
        {selectedStudentId && (
          <ReportToolbar
            onExportPdf={() => exportPdf.mutate({ studentId: selectedStudentId })}
            onExportExcel={() => exportExcel.mutate({ studentId: selectedStudentId })}
            onExportCsv={() => exportCsv.mutate({ studentId: selectedStudentId })}
            isExportingPdf={exportPdf.isPending}
            isExportingExcel={exportExcel.isPending}
            isExportingCsv={exportCsv.isPending}
          />
        )}
      </div>
      <Card data-print-hidden>
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
      {selectedStudentId && selectedChild && (
        <div data-print-region className="space-y-4">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Viewing attendance for:{" "}
            <span className="font-medium text-slate-900 dark:text-slate-100">
              {selectedChild.first_name} {selectedChild.last_name}
            </span>
          </p>
          <AttendanceContent studentId={selectedStudentId} showHeading={false} />
        </div>
      )}
    </div>
  );
}

function AttendanceContent({ studentId, showHeading = true }: { studentId?: string; showHeading?: boolean }) {
  const [view, setView] = useState<ViewMode>("table");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [classSessionId, setClassSessionId] = useState("");

  const { data, isLoading } = useMyAttendance({
    classSessionId: classSessionId || undefined,
    dateFrom: dateFrom || undefined,
    dateTo: dateTo || undefined,
    studentId,
  });

  if (isLoading || !data) {
    return <PageLoader label="Loading attendance..." />;
  }

  const allRecords = data.by_class_session.flatMap((cls) =>
    cls.records.map((record) => ({ ...record, course_name: cls.course_name })),
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        {showHeading && (
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Attendance</h1>
        )}
        <div className="ml-auto flex gap-1 rounded-md border border-slate-200 p-1 dark:border-slate-700">
          <button
            type="button"
            onClick={() => setView("table")}
            className={`rounded px-3 py-1 text-sm font-medium transition-colors ${view === "table" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"}`}
          >
            Table view
          </button>
          <button
            type="button"
            onClick={() => setView("calendar")}
            className={`rounded px-3 py-1 text-sm font-medium transition-colors ${view === "calendar" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"}`}
          >
            Calendar view
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-sm">
        <select value={classSessionId} onChange={(e) => setClassSessionId(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">All Classes</option>
          {data.by_class_session.map((cls) => (
            <option key={cls.class_session_id} value={cls.class_session_id}>
              {cls.course_name}
            </option>
          ))}
        </select>
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className={`w-auto ${inputClass}`} />
        <span className="text-slate-400">to</span>
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className={`w-auto ${inputClass}`} />
      </div>

      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">Overall: {data.overall_percentage}%</span>
          <ProgressBar value={data.overall_percentage} />
          {data.low_attendance_warning && (
            <span className="flex items-center gap-1 rounded-full border border-amber-300 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300">
              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
              Below 80%
            </span>
          )}
        </div>
      </Card>

      {view === "table" ? (
        allRecords.length === 0 ? (
          <EmptyState icon={CalendarDays} title="No attendance records yet" />
        ) : (
          <Card className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-4 py-2.5">Date</th>
                  <th className="px-4 py-2.5">Class</th>
                  <th className="px-4 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody>
                {allRecords
                  .sort((a, b) => b.date.localeCompare(a.date))
                  .map((record, i) => (
                    <tr
                      key={i}
                      className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                    >
                      <td className="px-4 py-2.5">{record.date}</td>
                      <td className="px-4 py-2.5">{record.course_name}</td>
                      <td className="px-4 py-2.5">
                        <Badge tone={statusTone[record.status]}>{record.status}</Badge>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </Card>
        )
      ) : allRecords.length === 0 ? (
        <EmptyState icon={CalendarDays} title="No attendance records yet" />
      ) : (
        <CalendarMonthView records={allRecords} />
      )}
    </div>
  );
}
