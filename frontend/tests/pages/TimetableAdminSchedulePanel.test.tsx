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

vi.mock("../../src/features/schedule", () => ({
  useCreateClassSession: () => ({ mutateAsync: mutateAsyncCreateClassSession, isPending: false }),
  useCreateEnrollment: () => ({ mutateAsync: mutateAsyncCreateEnrollment, isPending: false }),
  useCreateScheduleEntry: () => ({ mutateAsync: mutateAsyncCreateScheduleEntry, isPending: false }),
  useCreateChangeRequest: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useMySchedule: () => ({ data: undefined, isLoading: false }),
  useScheduleConflicts: () => ({ data: undefined, refetch: vi.fn() }),
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
