// Component test: Admin Result Approval page (Milestone 11 — CLAUDE.md §10
// names the approval workflow explicitly as critical interaction logic
// requiring coverage).
//
// Verifies: Approve calls POST /results/{id}/approve with decision
// "approve"; Reject without a comment is blocked client-side (BR-002's
// own reject-requires-comment rule) without calling the API at all; Reject
// with a comment calls the same endpoint with decision "reject" and the
// comment text.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ResultApprovalPage from "../../src/pages/Admin/ResultApproval";

const mutateAsyncApprove = vi.fn();

const pendingResultsData = {
  items: [
    {
      exam_id: "exam-1",
      exam_title: "Midterm",
      course_id: "course-1",
      course_name: "DB Systems",
      submitted_by_teacher_id: "teacher-1",
      submitted_by_teacher_name: "Terry Teach",
      submitted_at: "2026-01-01T00:00:00Z",
      status: "submitted",
      results: [
        { result_id: "result-1", student_id: "student-1", student_name: "Sam Student", grade_letter: "A", grade_point: 4.0 },
      ],
    },
  ],
};

vi.mock("../../src/features/results", () => ({
  usePendingResults: () => ({ data: pendingResultsData, isLoading: false }),
  useApproveOrRejectResult: () => ({ mutateAsync: mutateAsyncApprove, isPending: false }),
}));

async function expandReviewPanel() {
  const user = userEvent.setup();
  render(<ResultApprovalPage />);
  await user.click(screen.getByRole("button", { name: /review/i }));
  return user;
}

describe("ResultApprovalPage approval workflow", () => {
  beforeEach(() => {
    mutateAsyncApprove.mockReset();
  });

  it("approve calls the API with decision 'approve'", async () => {
    mutateAsyncApprove.mockResolvedValue({ id: "result-1", status: "published", approved_at: "2026-01-02T00:00:00Z" });
    const user = await expandReviewPanel();

    await user.click(screen.getByRole("button", { name: /^approve$/i }));

    expect(mutateAsyncApprove).toHaveBeenCalledWith({ resultId: "result-1", decision: "approve" });
  });

  it("reject without a comment is blocked client-side and never calls the API", async () => {
    const user = await expandReviewPanel();

    await user.click(screen.getByRole("button", { name: /^reject$/i }));

    expect(mutateAsyncApprove).not.toHaveBeenCalled();
    expect(await screen.findByRole("alert")).toHaveTextContent(/comment is required/i);
  });

  it("reject with a comment calls the API with decision 'reject' and the comment text", async () => {
    mutateAsyncApprove.mockResolvedValue({ id: "result-1", status: "rejected", approved_at: "2026-01-02T00:00:00Z" });
    const user = await expandReviewPanel();

    await user.type(screen.getByPlaceholderText(/comment/i), "Needs correction");
    await user.click(screen.getByRole("button", { name: /^reject$/i }));

    expect(mutateAsyncApprove).toHaveBeenCalledWith({
      resultId: "result-1",
      decision: "reject",
      comment: "Needs correction",
    });
  });
});
