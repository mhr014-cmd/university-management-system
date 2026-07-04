// Component test: ExamRoom page (Milestone 11 — CLAUDE.md §10 names the
// exam timer explicitly as critical interaction logic requiring coverage).
//
// Verifies: the countdown renders from the server-recorded start time, and
// that reaching zero triggers an automatic submit exactly once — the
// behavior `docs/UI_Wireframes.md` Section 5 and the page's own docstring
// describe as the reason /exams/{id}/start exists at all (never trusting
// a client-side clock).

import { act, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ExamRoomPage from "../../src/pages/ExamRoom";

const mutateAsyncStart = vi.fn();
const mutateAsyncSubmit = vi.fn();

vi.mock("../../src/features/exams", () => ({
  useExam: () => ({
    data: {
      id: "exam-1",
      class_session_id: "cs-1",
      created_by_teacher_id: "t-1",
      title: "Midterm",
      exam_type: "mcq",
      time_limit_minutes: 1,
      status: "open",
      scheduled_at: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      questions: [
        {
          id: "q1",
          question_text: "2 + 2 = ?",
          question_type: "mcq",
          marks: 5,
          hint: null,
          order_index: 0,
          options: [
            { id: "opt-a", option_text: "3", is_correct: null },
            { id: "opt-b", option_text: "4", is_correct: null },
          ],
          awarded_marks: null,
          feedback: null,
        },
      ],
    },
    isLoading: false,
  }),
  useStartExam: () => ({ mutateAsync: mutateAsyncStart }),
  useSubmitExam: () => ({ mutateAsync: mutateAsyncSubmit, isPending: false }),
}));

function renderExamRoom() {
  return render(
    <MemoryRouter initialEntries={["/exams/exam-1/room"]}>
      <Routes>
        <Route path="/exams/:examId/room" element={<ExamRoomPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ExamRoomPage timer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mutateAsyncStart.mockReset();
    mutateAsyncSubmit.mockReset();
    mutateAsyncSubmit.mockResolvedValue({});
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the countdown computed from the server-recorded start time, never a client clock", async () => {
    const startedAt = new Date().toISOString();
    mutateAsyncStart.mockResolvedValue({
      submission_id: "sub-1",
      exam_id: "exam-1",
      status: "in_progress",
      started_at: startedAt,
    });

    renderExamRoom();

    // Flush the mount-time useEffect's mutateAsyncStart().then(...) chain.
    await act(() => vi.advanceTimersByTimeAsync(0));
    expect(mutateAsyncStart).toHaveBeenCalledWith("exam-1");

    await act(() => vi.advanceTimersByTimeAsync(1000));
    expect(screen.getByText(/00:5\d/)).toBeInTheDocument();
  });

  it("auto-submits exactly once when the countdown reaches zero", async () => {
    const startedAt = new Date().toISOString();
    mutateAsyncStart.mockResolvedValue({
      submission_id: "sub-1",
      exam_id: "exam-1",
      status: "in_progress",
      started_at: startedAt,
    });

    renderExamRoom();
    await act(() => vi.advanceTimersByTimeAsync(0));
    expect(mutateAsyncStart).toHaveBeenCalled();

    // time_limit_minutes: 1 -> deadline is 60s after started_at.
    await act(() => vi.advanceTimersByTimeAsync(61_000));

    expect(mutateAsyncSubmit).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/exam submitted/i)).toBeInTheDocument();

    // Advancing further must not trigger a second auto-submit.
    await act(() => vi.advanceTimersByTimeAsync(5000));
    expect(mutateAsyncSubmit).toHaveBeenCalledTimes(1);
  });
});
