// Component test: Student self-view Results page (Download Transcript
// hang/no-feedback bug fix). Previously untested: StudentResultsView had
// no coverage at all despite already gating the "Download Transcript"
// button on `hasAnyPublishedResults`. This covers both cases the bug
// report described:
//   - a student with no published results — button disabled, no request
//     ever fires even if a click is attempted, and no spinner gets stuck.
//   - a student with published results — existing behavior (mutate
//     called) is preserved, and a failed download now surfaces a toast
//     instead of silently doing nothing (the mutation previously had no
//     onError at all).

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, beforeEach, expect, it, vi } from "vitest";
import ResultsViewPage from "../../src/pages/ResultsView";
import { ToastProvider } from "../../src/components/ui/Toast";

vi.mock("../../src/auth/AuthContext", () => ({
  useAuth: () => ({ user: { role: "student" }, isAuthenticated: true, login: vi.fn(), logout: vi.fn() }),
}));

let resultsData: { student_id: string; semesters: unknown[] } = { student_id: "student-4", semesters: [] };
const mutateDownloadTranscript = vi.fn();
vi.mock("../../src/features/results", () => ({
  useMyResults: () => ({ data: resultsData, isLoading: false }),
  useDownloadTranscript: () => ({ mutate: mutateDownloadTranscript, isPending: false }),
}));

function renderPage() {
  return render(
    <ToastProvider>
      <ResultsViewPage />
    </ToastProvider>,
  );
}

describe("ResultsViewPage — Student, no published results", () => {
  beforeEach(() => {
    mutateDownloadTranscript.mockReset();
    resultsData = { student_id: "student-4", semesters: [] };
  });

  it("shows the empty state and never enables the transcript download", async () => {
    renderPage();

    expect(screen.getByText("No published results yet")).toBeInTheDocument();
    const button = screen.getByRole("button", { name: /download transcript/i });
    expect(button).toBeDisabled();

    // A disabled native <button> never dispatches click, matching real
    // browser behavior — this is the same guard the reported hang bypassed.
    const user = userEvent.setup();
    await user.click(button);
    expect(mutateDownloadTranscript).not.toHaveBeenCalled();
  });
});

describe("ResultsViewPage — Student, with published results", () => {
  beforeEach(() => {
    mutateDownloadTranscript.mockReset();
    resultsData = {
      student_id: "student-4",
      semesters: [
        {
          semester_id: "sem-1",
          semester_name: "Spring 2026",
          gpa: 4.0,
          courses: [{ course_id: "course-1", course_name: "Intro to Programming", grade_letter: "A", grade_point: 4.0 }],
        },
      ],
    };
  });

  it("keeps the transcript download button enabled and calls mutate on click", async () => {
    const user = userEvent.setup();
    renderPage();

    const button = screen.getByRole("button", { name: /download transcript/i });
    expect(button).toBeEnabled();

    await user.click(button);
    expect(mutateDownloadTranscript).toHaveBeenCalledWith("student-4", expect.anything());
  });

  it("shows a toast instead of hanging silently if the download fails", async () => {
    const user = userEvent.setup();
    mutateDownloadTranscript.mockImplementation((_studentId, options) => {
      options?.onError?.();
    });
    renderPage();

    await user.click(screen.getByRole("button", { name: /download transcript/i }));

    expect(await screen.findByText("Could not generate the transcript. Please try again.")).toBeInTheDocument();
  });
});
