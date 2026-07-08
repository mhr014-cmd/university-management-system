// Component test: ExamList page (audit fix, critical A1). GET /exams
// requires student_id for a Parent caller — this page previously had no
// child selector at all, so a Parent following the Dashboard's "Upcoming
// Exams" card hit a permanent "Loading exams..." dead end (403, never
// resolved). Covers the new Parent branch (one child / multiple children /
// no linked children) and confirms Student/Teacher behavior is unchanged.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, beforeEach, expect, it, vi } from "vitest";
import ExamListPage from "../../src/pages/ExamList";

function renderPage() {
  return render(
    <MemoryRouter>
      <ExamListPage />
    </MemoryRouter>,
  );
}

let authRole = "parent";
vi.mock("../../src/auth/AuthContext", () => ({
  useAuth: () => ({ user: { role: authRole }, isAuthenticated: true, login: vi.fn(), logout: vi.fn() }),
}));

let childrenData: { children: { id: string; first_name: string; last_name: string }[] } = {
  children: [{ id: "student-1", first_name: "John", last_name: "Smith" }],
};
vi.mock("../../src/features/users", () => ({
  useMyChildren: () => ({ data: childrenData, isLoading: false, isError: false }),
}));

vi.mock("../../src/features/schedule", () => ({
  useMySchedule: () => ({ data: { entries: [] } }),
}));

const examsData = {
  items: [
    { id: "exam-1", title: "Midterm", course_name: "Intro to CS", exam_type: "mcq", time_limit_minutes: 30, status: "published", scheduled_at: "2026-08-01T09:00:00Z" },
  ],
  total: 1,
  page: 1,
  page_size: 20,
};
const useExamsMock = vi.fn(() => ({ data: examsData, isLoading: false }));
vi.mock("../../src/features/exams", () => ({
  useExams: (...args: unknown[]) => useExamsMock(...args),
}));

describe("ExamListPage — Parent", () => {
  beforeEach(() => {
    authRole = "parent";
    useExamsMock.mockClear();
    useExamsMock.mockReturnValue({ data: examsData, isLoading: false });
    childrenData = { children: [{ id: "student-1", first_name: "John", last_name: "Smith" }] };
  });

  it("with one linked child: auto-selects it and scopes GET /exams by studentId", () => {
    renderPage();
    expect(screen.getByText(/Linked Child/i)).toBeInTheDocument();
    expect(useExamsMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ studentId: "student-1" }),
    );
    expect(screen.getByText("Midterm")).toBeInTheDocument();
  });

  it("with multiple linked children: auto-selects the first, and switching re-scopes the query", async () => {
    childrenData = {
      children: [
        { id: "student-1", first_name: "John", last_name: "Smith" },
        { id: "student-2", first_name: "Amy", last_name: "Smith" },
      ],
    };
    const user = userEvent.setup();
    renderPage();

    expect(useExamsMock).toHaveBeenLastCalledWith(expect.objectContaining({ studentId: "student-1" }));

    const select = screen.getByDisplayValue("John Smith");
    await user.selectOptions(select, "student-2");

    expect(useExamsMock).toHaveBeenLastCalledWith(expect.objectContaining({ studentId: "student-2" }));
  });

  it("with no linked children: shows the EmptyState and never calls GET /exams with a student id", () => {
    childrenData = { children: [] };
    renderPage();

    expect(screen.getByText("No children linked yet")).toBeInTheDocument();
    expect(screen.queryByText("Midterm")).not.toBeInTheDocument();
    // useExams is never reached at all for this branch — no ExamListContent
    // is rendered until a child is selected, so it must not have been
    // called with a defined studentId.
    for (const call of useExamsMock.mock.calls) {
      expect((call[0] as { studentId?: string } | undefined)?.studentId).toBeUndefined();
    }
  });
});

describe("ExamListPage — Student (unchanged)", () => {
  beforeEach(() => {
    authRole = "student";
    useExamsMock.mockClear();
    useExamsMock.mockReturnValue({ data: examsData, isLoading: false });
  });

  it("renders the exam list directly, with no Linked Child selector, and no studentId passed", () => {
    renderPage();
    expect(screen.queryByText(/Linked Child/i)).not.toBeInTheDocument();
    expect(screen.getByText("Midterm")).toBeInTheDocument();
    expect(useExamsMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ studentId: undefined }),
    );
  });
});

describe("ExamListPage — Teacher (unchanged)", () => {
  beforeEach(() => {
    authRole = "teacher";
    useExamsMock.mockClear();
    useExamsMock.mockReturnValue({ data: examsData, isLoading: false });
  });

  it("renders the exam list directly, with no Linked Child selector, and the New Exam button", () => {
    renderPage();
    expect(screen.queryByText(/Linked Child/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new exam/i })).toBeInTheDocument();
    expect(useExamsMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ studentId: undefined }),
    );
  });
});
