// Component test: Teacher Grading Interface (Milestone 11 — CLAUDE.md §10
// names the grading form explicitly as critical interaction logic
// requiring coverage).
//
// Verifies: entering a mark and clicking "Save Grades" submits exactly the
// entered value via POST /exams/{id}/grade (features/exams' useGradeExam),
// and that a 422 (a grade exceeding a question's max marks, VR-006) shows
// the specific inline error rather than a generic failure message.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError } from "axios";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import GradingInterfacePage from "../../src/pages/Teacher/GradingInterface";

const mutateAsyncGrade = vi.fn();
const mutateAsyncUpdateExam = vi.fn();

// Hoisted, stable object identities: the mocked hooks below must return the
// *same* reference on every render, not a fresh object literal per call —
// otherwise GradingInterfacePage's `useEffect(..., [detail])` (which syncs
// `draft` from `detail`) sees a "changed" dependency every render, calls
// setDraft again, re-renders, and never stabilizes (an infinite loop that
// exhausted the test worker's memory the first time this was written).
// Same reason `examData`/`examResultsData` are mutated in place by each
// test (via `Object.assign`/array splicing) rather than reassigned, and
// why the FR-034 describe block below does the same instead of using
// `vi.doMock` — the top-level `vi.mock` factory below is hoisted and
// resolved once for the whole file, so a per-test `vi.doMock` never
// actually overrides it once `GradingInterfacePage` has been imported.
const examData: { id: string; title: string; status: string } = {
  id: "exam-1",
  title: "Midterm",
  status: "open",
};

const examResultsData = {
  exam_id: "exam-1",
  submissions: [
    {
      student_id: "student-1",
      student_name: "Sam Student",
      submission_id: "sub-1",
      total_awarded_marks: 0,
      status: "submitted",
    },
  ],
};

const submissionDetailData = {
  submission_id: "sub-1",
  exam_id: "exam-1",
  student_id: "student-1",
  status: "submitted",
  questions: [
    {
      question_id: "q1",
      question_text: "2 + 2 = ?",
      question_type: "short_answer",
      marks: 5,
      order_index: 0,
      answer_id: "answer-1",
      answer_text: "4",
      selected_option_id: null,
      awarded_marks: null,
      feedback: null,
    },
  ],
};

vi.mock("../../src/features/exams", () => ({
  useExam: () => ({ data: examData }),
  useExamResults: () => ({ data: examResultsData }),
  useSubmissionDetail: () => ({ data: submissionDetailData, isLoading: false }),
  useGradeExam: () => ({ mutateAsync: mutateAsyncGrade, isPending: false }),
  useUpdateExam: () => ({ mutateAsync: mutateAsyncUpdateExam, isPending: false }),
}));

const mutateAsyncSubmitResults = vi.fn();
vi.mock("../../src/features/results", () => ({
  useSubmitResults: () => ({ mutateAsync: mutateAsyncSubmitResults, isPending: false }),
}));

function renderGradingInterface() {
  return render(
    <MemoryRouter initialEntries={["/teacher/grading/exam-1"]}>
      <Routes>
        <Route path="/teacher/grading/:examId" element={<GradingInterfacePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("GradingInterfacePage grading form", () => {
  it("submits the entered mark for the answered question via POST /exams/{id}/grade", async () => {
    const user = userEvent.setup();
    mutateAsyncGrade.mockResolvedValue({ submission_id: "sub-1", status: "graded", total_awarded_marks: 4 });

    renderGradingInterface();

    const marksInput = await screen.findByPlaceholderText("Marks");
    await user.type(marksInput, "4");
    await user.click(screen.getByRole("button", { name: /save grades/i }));

    expect(mutateAsyncGrade).toHaveBeenCalledWith({
      examId: "exam-1",
      submissionId: "sub-1",
      grades: [{ answer_id: "answer-1", awarded_marks: 4, feedback: undefined }],
    });
    expect(await screen.findByText("Grades saved.")).toBeInTheDocument();
  });

  it("shows the VR-006 max-marks message on a 422 response, not a generic error", async () => {
    const user = userEvent.setup();
    mutateAsyncGrade.mockRejectedValueOnce(
      new AxiosError("Request failed", "422", undefined, undefined, {
        status: 422,
        data: {},
        statusText: "Unprocessable Entity",
        headers: {},
        // @ts-expect-error - partial AxiosResponse is sufficient for isAxiosError's own duck-typing.
        config: {},
      }),
    );

    renderGradingInterface();

    const marksInput = await screen.findByPlaceholderText("Marks");
    await user.type(marksInput, "10");
    await user.click(screen.getByRole("button", { name: /save grades/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/exceeds a question's maximum marks/i);
  });
});

// FR-034: a Teacher submits a published, fully-graded exam's results for
// admin approval via POST /results/{examId}/submit (features/results'
// useSubmitResults) — previously built and tested at the API layer but
// never reachable from any page. Covers the gap found via live runtime
// debugging (see Grading Interface's own module docstring).
describe("GradingInterfacePage — Submit Results for Approval (FR-034)", () => {
  it("is hidden until the exam is published, even when fully graded", async () => {
    examData.status = "open";
    examResultsData.submissions[0].status = "graded";

    renderGradingInterface();

    await screen.findByPlaceholderText("Marks");
    expect(screen.queryByText("Submit Results for Admin Approval")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /publish exam/i })).toBeInTheDocument();
  });

  it("submits grade_letter/grade_point per student once published and fully graded", async () => {
    examData.status = "published";
    examResultsData.submissions[0].status = "graded";
    examResultsData.submissions[0].total_awarded_marks = 4;
    const user = userEvent.setup();
    mutateAsyncSubmitResults.mockResolvedValue({ exam_id: "exam-1", status: "submitted", submitted_at: "now" });

    renderGradingInterface();

    expect(screen.queryByRole("button", { name: /publish exam/i })).not.toBeInTheDocument();
    await screen.findByText("Submit Results for Admin Approval");

    await user.type(screen.getByPlaceholderText("Grade letter (e.g. A)"), "A");
    await user.type(screen.getByPlaceholderText("Grade point"), "4");
    await user.click(screen.getByRole("button", { name: /submit results for approval/i }));

    expect(mutateAsyncSubmitResults).toHaveBeenCalledWith({
      examId: "exam-1",
      results: [{ student_id: "student-1", grade_letter: "A", grade_point: 4 }],
    });
    expect(await screen.findByText("Results submitted for admin approval.")).toBeInTheDocument();
  });
});
