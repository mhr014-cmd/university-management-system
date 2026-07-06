// Teacher: Attendance Marker page (FR-027, FR-029). Layout matches
// docs/UI_Wireframes.md Section 15: Class + Date selectors, a roster
// table with a per-row Status dropdown, "Mark all present" bulk
// shortcut, and Save. If the selected date already has records, the
// page loads in "correction" mode (pre-filled, calling PUT instead of
// POST on save), per the wireframe's Validation note.
//
// The Class selector reuses GET /schedule/me (this Teacher's own
// entries) rather than a dedicated class-session list endpoint — no
// such list endpoint exists (see PROJECT_PROGRESS.md's Milestone 4
// entry on the deliberately create-only Derived scheduling endpoints).

import { useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import { Users } from "lucide-react";
import { useClassSessionRoster, useMySchedule } from "../../../features/schedule";
import type { RosterEntry } from "../../../features/schedule";
import { useClassAttendance, useMarkAttendance, useUpdateAttendance } from "../../../features/attendance";
import type { AttendanceStatus } from "../../../features/attendance";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { inputClass } from "../../../components/ui/classNames";

const STATUS_OPTIONS: AttendanceStatus[] = ["present", "absent", "late", "excused"];

export default function AttendanceMarkerPage() {
  const { data: schedule } = useMySchedule();
  const [classSessionId, setClassSessionId] = useState("");
  const [attendanceDate, setAttendanceDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [statuses, setStatuses] = useState<Record<string, AttendanceStatus>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uniqueClassSessions = useMemo(() => {
    const seen = new Map<string, string>();
    for (const entry of schedule?.entries ?? []) {
      seen.set(entry.class_session_id, entry.course_name);
    }
    return Array.from(seen.entries()).map(([id, name]) => ({ id, name }));
  }, [schedule]);

  const { data: roster } = useClassSessionRoster(classSessionId || undefined);
  const { data: existingAttendance } = useClassAttendance(classSessionId || undefined, {
    dateFrom: attendanceDate,
    dateTo: attendanceDate,
  });
  const markAttendance = useMarkAttendance();
  const updateAttendance = useUpdateAttendance();

  const isCorrectionMode = (existingAttendance?.records.length ?? 0) > 0;

  useEffect(() => {
    if (!roster) return;
    const next: Record<string, AttendanceStatus> = {};
    for (const student of roster.students) {
      const existing = existingAttendance?.records.find((r) => r.student_id === student.student_id);
      next[student.student_id] = existing?.status ?? "present";
    }
    setStatuses(next);
  }, [roster, existingAttendance]);

  const handleMarkAllPresent = () => {
    setStatuses((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(next)) next[key] = "present";
      return next;
    });
  };

  const handleSave = async () => {
    setMessage(null);
    setError(null);
    try {
      if (isCorrectionMode) {
        for (const student of roster?.students ?? []) {
          const record = existingAttendance?.records.find((r) => r.student_id === student.student_id);
          const newStatus = statuses[student.student_id];
          if (record && newStatus && record.status !== newStatus) {
            await updateAttendance.mutateAsync({ id: record.id, status: newStatus });
          }
        }
        setMessage("Attendance corrected.");
        return;
      }
      await markAttendance.mutateAsync({
        class_session_id: classSessionId,
        attendance_date: attendanceDate,
        records: Object.entries(statuses).map(([student_id, status]) => ({ student_id, status })),
      });
      setMessage("Attendance saved.");
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setError("Attendance already recorded for this date.");
      } else {
        setError("Could not save attendance. Please try again.");
      }
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Mark Attendance</h1>

      <div className="flex items-center gap-4 text-sm">
        <select value={classSessionId} onChange={(e) => setClassSessionId(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">Select Class</option>
          {uniqueClassSessions.map((cls) => (
            <option key={cls.id} value={cls.id}>
              {cls.name}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={attendanceDate}
          onChange={(e) => setAttendanceDate(e.target.value)}
          className={`w-auto ${inputClass}`}
        />
      </div>

      {message && (
        <div className="rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
          {message}
        </div>
      )}
      {error && (
        <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {classSessionId && roster && (
        <>
          {roster.students.length === 0 ? (
            <EmptyState icon={Users} title="No students enrolled" description="No students are enrolled in this class session." />
          ) : (
            <Card className="overflow-x-auto p-0">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
                  <tr className="border-b border-slate-200 dark:border-slate-700">
                    <th className="px-4 py-2.5">Student</th>
                    <th className="px-4 py-2.5">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {roster.students.map((student: RosterEntry) => (
                    <tr
                      key={student.student_id}
                      className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                    >
                      <td className="px-4 py-2.5">{student.first_name} {student.last_name}</td>
                      <td className="px-4 py-2.5">
                        <select
                          value={statuses[student.student_id] ?? "present"}
                          onChange={(e) =>
                            setStatuses((prev) => ({ ...prev, [student.student_id]: e.target.value as AttendanceStatus }))
                          }
                          className={`w-auto ${inputClass}`}
                        >
                          {STATUS_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                              {option.charAt(0).toUpperCase() + option.slice(1)}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}

          <div className="flex items-center justify-between">
            <Button variant="secondary" onClick={handleMarkAllPresent}>
              Mark all present
            </Button>
            <Button onClick={handleSave} isLoading={markAttendance.isPending || updateAttendance.isPending}>
              Save Attendance
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
