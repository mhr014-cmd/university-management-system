// Component test: Timetable — Admin Schedule Panel (Version 2.3 polish pass).
// The Create Class Session / Enroll Student / Create Schedule Entry forms
// were converted from FormData-based uncontrolled inputs to per-field
// controlled state so their course_id/teacher_id/semester_id/room_id/
// student_id fields could become SearchableSelect pickers — this file
// covers that conversion, which previously had no test coverage at all.

import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, AxiosHeaders } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";
import TimetablePage from "../../src/pages/Timetable";
import { ToastProvider } from "../../src/components/ui/Toast";

vi.mock("../../src/auth/AuthContext", () => ({
  useAuth: () => ({ user: { role: "admin" }, isAuthenticated: true, login: vi.fn(), logout: vi.fn() }),
}));

const coursesData = {
  items: [{ id: "course-1", department_id: "dept-1", name: "Intro to CS", code: "CS101", credit_hours: 3 }],
  total: 1,
  page: 1,
  page_size: 100,
};
vi.mock("../../src/features/courses", () => ({
  useCourses: () => ({ data: coursesData, isLoading: false }),
}));

const roomsData = {
  items: [{ id: "room-1", name: "Room 101", building: "Main", capacity: 30 }],
  total: 1,
  page: 1,
  page_size: 100,
};
vi.mock("../../src/features/rooms", () => ({
  useRooms: () => ({ data: roomsData, isLoading: false }),
}));

const semestersData = {
  items: [{ id: "sem-1", name: "Fall 2025", start_date: "2025-09-01", end_date: "2025-12-20" }],
  total: 1,
  page: 1,
  page_size: 100,
};
vi.mock("../../src/features/semesters", () => ({
  useSemesters: () => ({ data: semestersData, isLoading: false }),
}));

const studentsData = {
  items: [
    {
      id: "student-1",
      user_id: "u1",
      email: "student@example.com",
      first_name: "John",
      last_name: "Smith",
      department_id: "dept-1",
      is_active: true,
      created_at: "2025-01-01",
    },
  ],
  total: 1,
  page: 1,
  page_size: 100,
};
const teachersData = {
  items: [
    {
      id: "teacher-1",
      user_id: "u2",
      email: "teacher@example.com",
      first_name: "Jane",
      last_name: "Doe",
      department_id: "dept-1",
      is_active: true,
      created_at: "2025-01-01",
    },
  ],
  total: 1,
  page: 1,
  page_size: 100,
};
vi.mock("../../src/features/users", () => ({
  useStudents: () => ({ data: studentsData, isLoading: false }),
  useTeachers: () => ({ data: teachersData, isLoading: false }),
  useMyChildren: () => ({ data: { children: [] }, isLoading: false }),
}));

const mutateAsyncCreateClassSession = vi.fn();
const mutateAsyncCreateEnrollment = vi.fn();
const mutateAsyncCreateScheduleEntry = vi.fn();
const mutateAsyncResolveChangeRequest = vi.fn();
const useScheduleChangeRequestsMock = vi.fn(() => ({ data: { items: [] }, isLoading: false }));

vi.mock("../../src/features/schedule", () => ({
  useCreateClassSession: () => ({ mutateAsync: mutateAsyncCreateClassSession, isPending: false }),
  useCreateEnrollment: () => ({ mutateAsync: mutateAsyncCreateEnrollment, isPending: false }),
  useCreateScheduleEntry: () => ({ mutateAsync: mutateAsyncCreateScheduleEntry, isPending: false }),
  useCreateChangeRequest: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useMySchedule: () => ({ data: undefined, isLoading: false }),
  useScheduleConflicts: () => ({ data: undefined, refetch: vi.fn() }),
  useScheduleChangeRequests: () => useScheduleChangeRequestsMock(),
  useResolveScheduleChangeRequest: () => ({ mutateAsync: mutateAsyncResolveChangeRequest, isPending: false }),
}));

function renderPage() {
  return render(
    <ToastProvider>
      <TimetablePage />
    </ToastProvider>,
  );
}

async function pickOption(user: ReturnType<typeof userEvent.setup>, trigger: HTMLElement, optionName: string) {
  await user.click(trigger);
  const listbox = screen.getByRole("listbox");
  await user.click(within(listbox).getByRole("option", { name: optionName }));
}

describe("Timetable Admin Schedule Panel", () => {
  beforeEach(() => {
    mutateAsyncCreateClassSession.mockReset();
    mutateAsyncCreateEnrollment.mockReset();
    mutateAsyncCreateScheduleEntry.mockReset();
    mutateAsyncResolveChangeRequest.mockReset();
    useScheduleChangeRequestsMock.mockReset();
    useScheduleChangeRequestsMock.mockReturnValue({ data: { items: [] }, isLoading: false });
  });

  it("submits course_id/teacher_id/semester_id/section_label when creating a class session", async () => {
    mutateAsyncCreateClassSession.mockResolvedValue({ id: "cs-1" });
    const user = userEvent.setup();
    renderPage();

    const form = screen.getByText("Create Class Session").closest("form") as HTMLElement;
    await pickOption(user, within(form).getByRole("button", { name: "Select Course" }), "Intro to CS (CS101)");
    await pickOption(user, within(form).getByRole("button", { name: "Select Teacher" }), "Jane Doe");
    await pickOption(user, within(form).getByRole("button", { name: "Select Semester" }), "Fall 2025");
    await user.type(within(form).getByPlaceholderText("Section Label"), "Section A");
    await user.click(within(form).getByRole("button", { name: "Create" }));

    expect(mutateAsyncCreateClassSession).toHaveBeenCalledWith({
      course_id: "course-1",
      teacher_id: "teacher-1",
      semester_id: "sem-1",
      section_label: "Section A",
    });
  });

  it("keeps the Create button disabled until course/teacher/semester are all selected", async () => {
    const user = userEvent.setup();
    renderPage();

    const form = screen.getByText("Create Class Session").closest("form") as HTMLElement;
    const submit = within(form).getByRole("button", { name: "Create" });
    expect(submit).toBeDisabled();

    await pickOption(user, within(form).getByRole("button", { name: "Select Course" }), "Intro to CS (CS101)");
    expect(submit).toBeDisabled();

    await pickOption(user, within(form).getByRole("button", { name: "Select Teacher" }), "Jane Doe");
    await pickOption(user, within(form).getByRole("button", { name: "Select Semester" }), "Fall 2025");
    expect(submit).not.toBeDisabled();
  });

  it("submits student_id (from SearchableSelect) and the typed class_session_id when enrolling a student", async () => {
    mutateAsyncCreateEnrollment.mockResolvedValue({ id: "enroll-1" });
    const user = userEvent.setup();
    renderPage();

    const form = screen.getByText("Enroll Student").closest("form") as HTMLElement;
    await pickOption(user, within(form).getByRole("button", { name: "Select Student" }), "John Smith");
    await user.type(within(form).getByPlaceholderText("Class Session ID"), "cs-123");
    await user.click(within(form).getByRole("button", { name: "Enroll" }));

    expect(mutateAsyncCreateEnrollment).toHaveBeenCalledWith({
      student_id: "student-1",
      class_session_id: "cs-123",
    });
  });

  it("submits room_id/teacher_id (from SearchableSelect) when creating a schedule entry", async () => {
    mutateAsyncCreateScheduleEntry.mockResolvedValue({ id: "entry-1" });
    const user = userEvent.setup();
    renderPage();

    const form = screen.getByText("Create Schedule Entry").closest("form") as HTMLElement;
    await user.type(within(form).getByPlaceholderText("Class Session ID"), "cs-999");
    await pickOption(user, within(form).getByRole("button", { name: "Select Room" }), "Room 101 — Main");
    await pickOption(user, within(form).getByRole("button", { name: "Select Teacher" }), "Jane Doe");

    const timeInputs = form.querySelectorAll('input[type="time"]');
    fireEvent.change(timeInputs[0], { target: { value: "09:00" } });
    fireEvent.change(timeInputs[1], { target: { value: "10:00" } });

    await user.click(within(form).getByRole("button", { name: "Create Entry" }));

    expect(mutateAsyncCreateScheduleEntry).toHaveBeenCalledWith({
      class_session_id: "cs-999",
      room_id: "room-1",
      teacher_id: "teacher-1",
      day_of_week: "Mon",
      start_time: "09:00:00",
      end_time: "10:00:00",
    });
  });

  it("shows a conflict-specific message when creating a schedule entry returns 409", async () => {
    mutateAsyncCreateScheduleEntry.mockRejectedValue(
      new AxiosError("Conflict", "409", undefined, undefined, {
        status: 409,
        statusText: "Conflict",
        headers: new AxiosHeaders(),
        config: { headers: new AxiosHeaders() },
        data: { error: { message: "conflict" } },
      }),
    );
    const user = userEvent.setup();
    renderPage();

    const form = screen.getByText("Create Schedule Entry").closest("form") as HTMLElement;
    await user.type(within(form).getByPlaceholderText("Class Session ID"), "cs-999");
    await pickOption(user, within(form).getByRole("button", { name: "Select Room" }), "Room 101 — Main");
    await pickOption(user, within(form).getByRole("button", { name: "Select Teacher" }), "Jane Doe");

    const timeInputs = form.querySelectorAll('input[type="time"]');
    fireEvent.change(timeInputs[0], { target: { value: "09:00" } });
    fireEvent.change(timeInputs[1], { target: { value: "10:00" } });

    await user.click(within(form).getByRole("button", { name: "Create Entry" }));

    expect(await screen.findByText(/conflicts with an existing room or teacher booking/i)).toBeInTheDocument();
  });
});

describe("Pending Schedule Change Requests panel", () => {
  beforeEach(() => {
    mutateAsyncResolveChangeRequest.mockReset();
    useScheduleChangeRequestsMock.mockReset();
  });

  const pendingRequest = {
    id: "req-1",
    schedule_entry_id: "entry-1",
    course_name: "Intro to CS",
    section_label: "A",
    requested_by_teacher_id: "teacher-1",
    requested_by_teacher_name: "Jane Doe",
    current_day_of_week: "Mon",
    current_start_time: "09:00:00",
    current_end_time: "10:00:00",
    current_room_name: "Room 101",
    requested_change: { day_of_week: "Tue", start_time: "11:00:00", end_time: "12:00:00" },
    status: "pending",
    created_at: "2026-01-01T00:00:00Z",
    resolved_at: null,
  };

  it("shows a no-pending-requests message when the queue is empty", () => {
    useScheduleChangeRequestsMock.mockReturnValue({ data: { items: [] }, isLoading: false });
    renderPage();
    expect(screen.getByText("No pending requests.")).toBeInTheDocument();
  });

  it("lists a pending request with its current and requested values", () => {
    useScheduleChangeRequestsMock.mockReturnValue({ data: { items: [pendingRequest] }, isLoading: false });
    renderPage();

    expect(screen.getByText(/Intro to CS \(A\) — Jane Doe/)).toBeInTheDocument();
    expect(screen.getByText(/Current: Mon 09:00–10:00 in Room 101/)).toBeInTheDocument();
    expect(screen.getByText(/Day: Tue.*Time: 11:00–12:00/)).toBeInTheDocument();
  });

  it("approves a request, including any typed comment", async () => {
    useScheduleChangeRequestsMock.mockReturnValue({ data: { items: [pendingRequest] }, isLoading: false });
    mutateAsyncResolveChangeRequest.mockResolvedValue({ id: "req-1", status: "approved" });
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByPlaceholderText("Optional comment (shown to the Teacher)"), "Looks good");
    await user.click(screen.getByRole("button", { name: "Approve" }));

    expect(mutateAsyncResolveChangeRequest).toHaveBeenCalledWith({
      requestId: "req-1",
      decision: "approve",
      comment: "Looks good",
    });
  });

  it("rejects a request", async () => {
    useScheduleChangeRequestsMock.mockReturnValue({ data: { items: [pendingRequest] }, isLoading: false });
    mutateAsyncResolveChangeRequest.mockResolvedValue({ id: "req-1", status: "rejected" });
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Reject" }));

    expect(mutateAsyncResolveChangeRequest).toHaveBeenCalledWith({
      requestId: "req-1",
      decision: "reject",
      comment: undefined,
    });
  });
});
