// Component test: Parent Dashboard — Upcoming Exams widget (gap closure).
// GET /exams now has a Parent branch (ownership-checked by student_id),
// replacing the previous "Not available" placeholder. This covers only
// the new widget — Fee Status/Attendance %/Recent Results are unchanged
// and already covered by their own feature areas.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, beforeEach, expect, it, vi } from "vitest";
import { ParentDashboard } from "../../src/pages/Dashboard/ParentDashboard";

function renderDashboard() {
  return render(
    <MemoryRouter>
      <ParentDashboard />
    </MemoryRouter>,
  );
}

const childrenData = {
  children: [
    { id: "student-1", first_name: "John", last_name: "Smith" },
    { id: "student-2", first_name: "Amy", last_name: "Smith" },
  ],
};
vi.mock("../../src/features/users", () => ({
  useMyChildren: () => ({ data: childrenData, isLoading: false, isError: false }),
}));

vi.mock("../../src/features/fees", () => ({
  useMyFees: () => ({ data: { outstanding_balance: 0, invoices: [] }, isError: false }),
}));

vi.mock("../../src/features/results", () => ({
  useMyResults: () => ({ data: { semesters: [] }, isError: false }),
}));

vi.mock("../../src/features/attendance", () => ({
  useMyAttendance: () => ({ data: { overall_percentage: 100, low_attendance_warning: false }, isError: false }),
}));

vi.mock("../../src/features/notifications", () => ({
  useNotifications: () => ({ data: { items: [], unread_count: 0, total: 0 }, isLoading: false }),
}));

const examsData = {
  items: [
    { id: "exam-1", title: "Midterm", course_name: "Intro to CS", status: "open", scheduled_at: "2026-08-01T09:00:00Z" },
    { id: "exam-2", title: "Quiz 2", course_name: "Intro to CS", status: "scheduled", scheduled_at: "2026-07-20T09:00:00Z" },
    { id: "exam-3", title: "Old Final", course_name: "Intro to CS", status: "published", scheduled_at: "2026-01-01T09:00:00Z" },
    { id: "exam-4", title: "No Date Yet", course_name: "Intro to CS", status: "scheduled", scheduled_at: null },
  ],
  total: 4,
  page: 1,
  page_size: 20,
};
const useExamsMock = vi.fn(() => ({ data: examsData, isError: false }));
vi.mock("../../src/features/exams", () => ({
  useExams: (...args: unknown[]) => useExamsMock(...args),
}));

describe("ParentDashboard — Upcoming Exams widget", () => {
  beforeEach(() => {
    useExamsMock.mockClear();
  });

  it("scopes the exams query to the selected child", () => {
    renderDashboard();
    expect(useExamsMock).toHaveBeenCalledWith({ studentId: "student-1" });
  });

  it("lists only scheduled/open exams with a date, sorted soonest-first, excluding published/undated ones", () => {
    renderDashboard();

    const list = screen.getByText("Quiz 2").closest("ul") as HTMLElement;
    const itemTexts = Array.from(list.querySelectorAll("li")).map((li) => li.textContent);

    expect(itemTexts[0]).toContain("Quiz 2");
    expect(itemTexts[1]).toContain("Midterm");
    expect(screen.queryByText("Old Final")).not.toBeInTheDocument();
    expect(screen.queryByText("No Date Yet")).not.toBeInTheDocument();
  });

  it("shows an empty state when there are no upcoming exams", () => {
    useExamsMock.mockReturnValue({ data: { items: [], total: 0, page: 1, page_size: 20 }, isError: false });
    renderDashboard();
    expect(screen.getByText("No upcoming exams scheduled.")).toBeInTheDocument();
  });

  it("re-scopes to the newly selected child when switched", async () => {
    const user = userEvent.setup();
    renderDashboard();

    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[0], "student-2");

    expect(useExamsMock).toHaveBeenLastCalledWith({ studentId: "student-2" });
  });
});
