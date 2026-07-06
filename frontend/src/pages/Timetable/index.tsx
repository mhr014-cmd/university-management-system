// Timetable page (FR-045). Layout matches docs/UI_Wireframes.md Section 9.
// Student/Teacher see a read-only weekly grid of their own schedule
// (GET /schedule/me); Teacher gets a "Request Change" action per cell
// (BR-004 — cannot edit directly). Admin sees a schedule-management panel
// instead of the grid (per the wireframe's Role Visibility note: Admin
// manages schedules "within Timetable's admin mode", not a separate page).
//
// Known limitation: the Admin panel's class_session_id fields are raw
// UUID text inputs, not dropdowns — no GET /schedule/class-sessions list
// endpoint exists (the Derived class-session/enrollment endpoints
// approved for Milestone 4 are deliberately create-only, matching the
// minimal-scope precedent from Milestone 1's reference-data CRUD). See
// PROJECT_PROGRESS.md's Milestone 4 entry.

import { useState, type FormEvent } from "react";
import { isAxiosError } from "axios";
import { AlertCircle, CalendarX2, CheckCircle2 } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import {
  useCreateChangeRequest,
  useCreateClassSession,
  useCreateEnrollment,
  useCreateScheduleEntry,
  useMySchedule,
  useScheduleConflicts,
  type DayOfWeek,
  type ScheduleMeEntry,
} from "../../features/schedule";
import { Button } from "../../components/ui/Button";
import { Card, CardTitle } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";
import { inputClass } from "../../components/ui/classNames";

const DAYS: DayOfWeek[] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function TimetablePage() {
  const { user } = useAuth();

  if (user?.role === "admin") {
    return <AdminSchedulePanel />;
  }
  return <MyScheduleGrid />;
}

function MyScheduleGrid() {
  const { user } = useAuth();
  const { data, isLoading } = useMySchedule();
  const [requestingEntry, setRequestingEntry] = useState<ScheduleMeEntry | null>(null);

  if (isLoading) {
    return <PageLoader label="Loading timetable..." />;
  }

  const entriesByDay = new Map<DayOfWeek, ScheduleMeEntry[]>();
  for (const entry of data?.entries ?? []) {
    const list = entriesByDay.get(entry.day_of_week) ?? [];
    list.push(entry);
    entriesByDay.set(entry.day_of_week, list);
  }
  const daysWithClasses = DAYS.filter((day) => entriesByDay.has(day));
  const visibleDays = daysWithClasses.length > 0 ? daysWithClasses : DAYS.slice(0, 5);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Timetable</h1>
      {(data?.entries.length ?? 0) === 0 ? (
        <EmptyState
          icon={CalendarX2}
          title="No classes scheduled"
          description="Your weekly timetable will appear here once classes are scheduled."
        />
      ) : (
        <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${visibleDays.length}, minmax(0, 1fr))` }}>
          {visibleDays.map((day) => (
            <div key={day} className="space-y-2">
              <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{day}</h2>
              {(entriesByDay.get(day) ?? [])
                .sort((a, b) => a.start_time.localeCompare(b.start_time))
                .map((entry) => (
                  <Card key={entry.schedule_entry_id} hoverable className="p-3 text-xs">
                    <div className="font-medium text-slate-900 dark:text-slate-100">{entry.course_name}</div>
                    <div className="text-slate-500 dark:text-slate-400">{entry.room_name}</div>
                    <div className="text-slate-500 dark:text-slate-400">
                      {entry.start_time.slice(0, 5)}–{entry.end_time.slice(0, 5)}
                    </div>
                    {user?.role === "teacher" && (
                      <Button variant="secondary" size="sm" className="mt-1.5" onClick={() => setRequestingEntry(entry)}>
                        Request Change
                      </Button>
                    )}
                  </Card>
                ))}
            </div>
          ))}
        </div>
      )}
      {requestingEntry && (
        <RequestChangeModal entry={requestingEntry} onClose={() => setRequestingEntry(null)} />
      )}
    </div>
  );
}

function RequestChangeModal({ entry, onClose }: { entry: ScheduleMeEntry; onClose: () => void }) {
  const createChangeRequest = useCreateChangeRequest();
  const [dayOfWeek, setDayOfWeek] = useState<DayOfWeek>(entry.day_of_week);
  const [startTime, setStartTime] = useState(entry.start_time.slice(0, 5));
  const [endTime, setEndTime] = useState(entry.end_time.slice(0, 5));
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (startTime >= endTime) {
      setError("Start time must be before end time.");
      return;
    }
    try {
      await createChangeRequest.mutateAsync({
        schedule_entry_id: entry.schedule_entry_id,
        requested_change: { day_of_week: dayOfWeek, start_time: `${startTime}:00`, end_time: `${endTime}:00` },
      });
      setSuccess(true);
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 422) {
        setError("Invalid requested time range.");
      } else {
        setError("Could not submit the request. Please try again.");
      }
    }
  };

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-900">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Request Schedule Change</h2>
        {success ? (
          <>
            <div className="flex items-start gap-2 rounded-md border border-green-200 bg-green-50 px-3 py-2.5 text-sm text-green-700 dark:border-green-900 dark:bg-green-950/50 dark:text-green-300">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>Request submitted — pending Admin confirmation.</span>
            </div>
            <Button variant="secondary" onClick={onClose}>Close</Button>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            {error && (
              <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{error}</span>
              </div>
            )}
            <select value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value as DayOfWeek)} className={inputClass}>
              {DAYS.map((day) => (
                <option key={day} value={day}>{day}</option>
              ))}
            </select>
            <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className={inputClass} />
            <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className={inputClass} />
            <div className="flex justify-end gap-2 pt-1">
              <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
              <Button type="submit" isLoading={createChangeRequest.isPending}>Submit Request</Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function AdminSchedulePanel() {
  const createClassSession = useCreateClassSession();
  const createEnrollment = useCreateEnrollment();
  const createScheduleEntry = useCreateScheduleEntry();
  const conflictsQuery = useScheduleConflicts();

  const [csResult, setCsResult] = useState<string | null>(null);
  const [entryError, setEntryError] = useState<string | null>(null);
  const [entrySuccess, setEntrySuccess] = useState(false);

  const handleCreateClassSession = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const result = await createClassSession.mutateAsync({
        course_id: String(form.get("course_id")),
        teacher_id: String(form.get("teacher_id")),
        semester_id: String(form.get("semester_id")),
        section_label: String(form.get("section_label")),
      });
      setCsResult(`Created class session: ${result.id}`);
    } catch {
      setCsResult("Could not create class session — check the referenced IDs.");
    }
  };

  const handleCreateEnrollment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await createEnrollment.mutateAsync({
      student_id: String(form.get("student_id")),
      class_session_id: String(form.get("class_session_id")),
    });
  };

  const handleCreateEntry = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setEntryError(null);
    setEntrySuccess(false);
    const form = new FormData(event.currentTarget);
    try {
      await createScheduleEntry.mutateAsync({
        class_session_id: String(form.get("class_session_id")),
        room_id: String(form.get("room_id")),
        teacher_id: String(form.get("teacher_id")),
        day_of_week: form.get("day_of_week") as DayOfWeek,
        start_time: `${form.get("start_time")}:00`,
        end_time: `${form.get("end_time")}:00`,
      });
      setEntrySuccess(true);
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setEntryError("This time slot conflicts with an existing room or teacher booking.");
      } else if (isAxiosError(err) && err.response?.status === 422) {
        setEntryError("Invalid time range or referenced ID.");
      } else {
        setEntryError("Could not create the schedule entry.");
      }
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Timetable — Admin</h1>

      <Card>
        <form onSubmit={handleCreateClassSession} className="space-y-2">
          <CardTitle>Create Class Session</CardTitle>
          <input name="course_id" required placeholder="Course ID" className={inputClass} />
          <input name="teacher_id" required placeholder="Teacher ID" className={inputClass} />
          <input name="semester_id" required placeholder="Semester ID" className={inputClass} />
          <input name="section_label" required placeholder="Section Label" className={inputClass} />
          <Button type="submit" isLoading={createClassSession.isPending}>Create</Button>
          {csResult && <p className="text-xs text-slate-500 dark:text-slate-400">{csResult}</p>}
        </form>
      </Card>

      <Card>
        <form onSubmit={handleCreateEnrollment} className="space-y-2">
          <CardTitle>Enroll Student</CardTitle>
          <input name="student_id" required placeholder="Student ID" className={inputClass} />
          <input name="class_session_id" required placeholder="Class Session ID" className={inputClass} />
          <Button type="submit" isLoading={createEnrollment.isPending}>Enroll</Button>
        </form>
      </Card>

      <Card>
        <form onSubmit={handleCreateEntry} className="space-y-2">
          <CardTitle>Create Schedule Entry</CardTitle>
          {entryError && (
            <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{entryError}</span>
            </div>
          )}
          {entrySuccess && (
            <div className="flex items-start gap-2 rounded-md border border-green-200 bg-green-50 px-3 py-2.5 text-sm text-green-700 dark:border-green-900 dark:bg-green-950/50 dark:text-green-300">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>Schedule entry created.</span>
            </div>
          )}
          <input name="class_session_id" required placeholder="Class Session ID" className={inputClass} />
          <input name="room_id" required placeholder="Room ID" className={inputClass} />
          <input name="teacher_id" required placeholder="Teacher ID" className={inputClass} />
          <select name="day_of_week" required className={inputClass}>
            {DAYS.map((day) => (
              <option key={day} value={day}>{day}</option>
            ))}
          </select>
          <input name="start_time" type="time" required className={inputClass} />
          <input name="end_time" type="time" required className={inputClass} />
          <Button type="submit" isLoading={createScheduleEntry.isPending}>Create Entry</Button>
        </form>
      </Card>

      <Card>
        <CardTitle>Conflict Detection</CardTitle>
        <Button variant="secondary" className="mt-2" onClick={() => conflictsQuery.refetch()}>
          Check Conflicts
        </Button>
        {conflictsQuery.data && (
          <ul className="mt-2 text-xs text-slate-600 dark:text-slate-300">
            {conflictsQuery.data.conflicts.length === 0 && <li>No conflicts found.</li>}
            {conflictsQuery.data.conflicts.map((conflict, i) => (
              <li key={i}>
                {conflict.type} conflict on {conflict.day_of_week} ({conflict.overlap_start}–{conflict.overlap_end})
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
