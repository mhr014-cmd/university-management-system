// Component test: Parent-facing Results view (production-readiness audit
// gap closure). ResultsView/index.tsx now branches by role — this covers
// the Parent branch specifically: child selector, per-semester GPA, the
// explicit "Not available" CGPA placeholder (no backend aggregate
// exists), the derived Pass/Fail column, and transcript download scoped
// to the selected child.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, beforeEach, expect, it, vi } from "vitest";
import ResultsViewPage from "../../src/pages/ResultsView";

vi.mock("../../src/auth/AuthContext", () => ({
  useAuth: () => ({ user: { role: "parent" }, isAuthenticated: true, login: vi.fn(), logout: vi.fn() }),
}));

const childrenData = {
  children: [
    { id: "student-1", first_name: "John", last_name: "Smith" },
    { id: "student-2", first_name: "Amy", last_name: "Smith" },
  ],
};
vi.mock("../../src/features/users", () => ({
  useMyChildren: () => ({ data: childrenData, isLoading: false, isError: false }),
}));

const resultsData = {
  student_id: "student-1",
  semesters: [
    {
      semester_id: "sem-1",
      semester_name: "Fall 2025",
      gpa: 3.5,
      courses: [
        { course_id: "course-1", course_name: "Intro to CS", grade_letter: "A", grade_point: 4.0 },
        { course_id: "course-2", course_name: "Calculus", grade_letter: "F", grade_point: 0.0 },
      ],
    },
  ],
};
const mutateDownloadTranscript = vi.fn();
vi.mock("../../src/features/results", () => ({
  useMyResults: () => ({ data: resultsData, isLoading: false }),
  useDownloadTranscript: () => ({ mutate: mutateDownloadTranscript, isPending: false }),
}));

describe("ResultsViewPage — Parent", () => {
  beforeEach(() => {
    mutateDownloadTranscript.mockReset();
  });

  it("auto-selects the first linked child and shows their results", () => {
    render(<ResultsViewPage />);

    expect(screen.getByText("Intro to CS")).toBeInTheDocument();
    expect(screen.getByText("GPA this semester: 3.50")).toBeInTheDocument();
  });

  it("shows an honest 'Not available' placeholder for overall CGPA", () => {
    render(<ResultsViewPage />);
    expect(screen.getByText(/Overall CGPA: Not available/i)).toBeInTheDocument();
  });

  it("derives Pass/Fail per course from grade_point", () => {
    render(<ResultsViewPage />);
    const passRow = screen.getByText("Intro to CS").closest("tr") as HTMLElement;
    const failRow = screen.getByText("Calculus").closest("tr") as HTMLElement;
    expect(passRow).toHaveTextContent("Pass");
    expect(failRow).toHaveTextContent("Fail");
  });

  it("lets the parent switch children via the Linked Child selector", async () => {
    const user = userEvent.setup();
    render(<ResultsViewPage />);

    const select = screen.getByDisplayValue("John Smith");
    await user.selectOptions(select, "student-2");

    expect(screen.getByText(/Viewing results for:/)).toHaveTextContent("Amy Smith");
  });

  it("downloads the transcript for the selected child", async () => {
    const user = userEvent.setup();
    render(<ResultsViewPage />);

    await user.click(screen.getByRole("button", { name: /download transcript/i }));

    expect(mutateDownloadTranscript).toHaveBeenCalledWith("student-1");
  });
});
