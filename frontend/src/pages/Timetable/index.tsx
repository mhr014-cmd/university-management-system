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
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading timetable...</p>;
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
      <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Timetable</h1>
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${visibleDays.length}, minmax(0, 1fr))` }}>
        {visibleDays.map((day) => (
          <div key={day} className="space-y-2">
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{day}</h2>
            {(entriesByDay.get(day) ?? [])
              .sort((a, b) => a.start_time.localeCompare(b.start_time))
              .map((entry) => (
                <div
                  key={entry.schedule_entry_id}
                  className="rounded border border-slate-200 p-2 text-xs dark:border-slate-700"
                >
                  <div className="font-medium">{entry.course_name}</div>
                  <div className="text-slate-500 dark:text-slate-400">{entry.room_name}</div>
                  <div className="text-slate-500 dark:text-slate-400">
                    {entry.start_time.slice(0, 5)}–{entry.end_time.slice(0, 5)}
                  </div>
                  {user?.role === "teacher" && (
                    <button
                      type="button"
                      onClick={() => setRequestingEntry(entry)}
                      className="mt-1 rounded border border-slate-300 px-2 py-1 text-xs dark:border-slate-600"
                    >
                      Request Change
                    </button>
                  )}
                </div>
              ))}
          </div>
        ))}
      </div>
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
    <div className="fixed inset-0 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm space-y-3 rounded bg-white p-6 dark:bg-slate-900">
        <h2 className="text-sm font-semibold">Request Schedule Change</h2>
        {success ? (
          <>
            <div className="rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
              Request submitted — pending Admin confirmation.
            </div>
            <button type="button" onClick={onClose} className="rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600">
              Close
            </button>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            {error && (
              <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
                {error}
              </div>
            )}
            <select value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value as DayOfWeek)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800">
              {DAYS.map((day) => (
                <option key={day} value={day}>{day}</option>
              ))}
            </select>
            <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
            <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={onClose} className="rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600">Cancel</button>
              <button type="submit" disabled={createChangeRequest.isPending} className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900">
                {createChangeRequest.isPending ? "Submitting..." : "Submit Request"}
              </button>
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
      <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Timetable — Admin</h1>

      <form onSubmit={handleCreateClassSession} className="space-y-2 rounded border border-slate-200 p-4 dark:border-slate-700">
        <h2 className="text-sm font-semibold">Create Class Session</h2>
        <input name="course_id" required placeholder="Course ID" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input name="teacher_id" required placeholder="Teacher ID" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input name="semester_id" required placeholder="Semester ID" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input name="section_label" required placeholder="Section Label" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <button type="submit" className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900">Create</button>
        {csResult && <p className="text-xs text-slate-500 dark:text-slate-400">{csResult}</p>}
      </form>

      <form onSubmit={handleCreateEnrollment} className="space-y-2 rounded border border-slate-200 p-4 dark:border-slate-700">
        <h2 className="text-sm font-semibold">Enroll Student</h2>
        <input name="student_id" required placeholder="Student ID" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input name="class_session_id" required placeholder="Class Session ID" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <button type="submit" className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900">Enroll</button>
      </form>

      <form onSubmit={handleCreateEntry} className="space-y-2 rounded border border-slate-200 p-4 dark:border-slate-700">
        <h2 className="text-sm font-semibold">Create Schedule Entry</h2>
        {entryError && (
          <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {entryError}
          </div>
        )}
        {entrySuccess && (
          <div className="rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
            Schedule entry created.
          </div>
        )}
        <input name="class_session_id" required placeholder="Class Session ID" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input name="room_id" required placeholder="Room ID" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input name="teacher_id" required placeholder="Teacher ID" className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <select name="day_of_week" required className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800">
          {DAYS.map((day) => (
            <option key={day} value={day}>{day}</option>
          ))}
        </select>
        <input name="start_time" type="time" required className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input name="end_time" type="time" required className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <button type="submit" className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900">Create Entry</button>
      </form>

      <div className="space-y-2 rounded border border-slate-200 p-4 dark:border-slate-700">
        <h2 className="text-sm font-semibold">Conflict Detection</h2>
        <button
          type="button"
          onClick={() => conflictsQuery.refetch()}
          className="rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600"
        >
          Check Conflicts
        </button>
        {conflictsQuery.data && (
          <ul className="text-xs">
            {conflictsQuery.data.conflicts.length === 0 && <li>No conflicts found.</li>}
            {conflictsQuery.data.conflicts.map((conflict, i) => (
              <li key={i}>
                {conflict.type} conflict on {conflict.day_of_week} ({conflict.overlap_start}–{conflict.overlap_end})
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
