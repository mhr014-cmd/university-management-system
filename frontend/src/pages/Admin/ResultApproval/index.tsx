// Admin: Result Approval page (FR-035, BR-002). Layout matches
// docs/UI_Wireframes.md Section 11: a pending-results queue table
// (Exam/Class/Submitted By/Date) with a status filter, and an
// expandable per-exam review panel showing per-student grades with
// Approve/Reject actions.
//
// Backed by GET /results/pending, a Derived Engineering Addition added
// during Milestone 7 implementation because none of this milestone's
// other documented endpoints could list/retrieve pending results — see
// docs/Proposal_vs_Engineering_Additions.md.

import { Fragment, useState } from "react";
import { usePendingResults, useApproveOrRejectResult } from "../../../features/results";
import type { ResultStatus } from "../../../features/results";

const STATUS_OPTIONS: ResultStatus[] = ["submitted", "published", "rejected"];

export default function ResultApprovalPage() {
  const [status, setStatus] = useState<ResultStatus>("submitted");
  const { data, isLoading } = usePendingResults(status);
  const approveOrReject = useApproveOrRejectResult();
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleApprove = async (resultId: string) => {
    setError(null);
    try {
      await approveOrReject.mutateAsync({ resultId, decision: "approve" });
    } catch {
      setError("Could not approve this result. Please try again.");
    }
  };

  const handleReject = async (resultId: string) => {
    if (!comment.trim()) {
      setError("A comment is required when rejecting a result.");
      return;
    }
    setError(null);
    try {
      await approveOrReject.mutateAsync({ resultId, decision: "reject", comment });
      setComment("");
    } catch {
      setError("Could not reject this result. Please try again.");
    }
  };

  if (isLoading || !data) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading pending results...</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Result Approval</h1>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as ResultStatus)}
          className="rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="py-2">Exam</th>
            <th className="py-2">Class</th>
            <th className="py-2">Submitted By</th>
            <th className="py-2">Date</th>
            <th className="py-2"></th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((item) => {
            const key = `${item.exam_id}-${item.course_id}-${item.submitted_by_teacher_id}-${item.submitted_at}`;
            const isExpanded = expandedKey === key;
            return (
              <Fragment key={key}>
                <tr className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50">
                  <td className="py-2">{item.exam_title ?? "—"}</td>
                  <td className="py-2">{item.course_name}</td>
                  <td className="py-2">{item.submitted_by_teacher_name}</td>
                  <td className="py-2">{new Date(item.submitted_at).toLocaleDateString()}</td>
                  <td className="py-2">
                    <button
                      type="button"
                      onClick={() => setExpandedKey(isExpanded ? null : key)}
                      className="rounded border border-slate-300 px-2 py-1 text-xs dark:border-slate-600"
                    >
                      {isExpanded ? "Close" : "Review"}
                    </button>
                  </td>
                </tr>
                {isExpanded && (
                  <tr>
                    <td colSpan={5} className="border-b border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800">
                      <table className="w-full text-left text-sm">
                        <thead>
                          <tr>
                            <th className="py-1">Student</th>
                            <th className="py-1">Grade</th>
                            <th className="py-1">Points</th>
                            {item.status === "submitted" && <th className="py-1">Action</th>}
                          </tr>
                        </thead>
                        <tbody>
                          {item.results.map((r) => (
                            <tr key={r.result_id}>
                              <td className="py-1">{r.student_name}</td>
                              <td className="py-1">{r.grade_letter ?? "—"}</td>
                              <td className="py-1">{r.grade_point?.toFixed(1) ?? "—"}</td>
                              {item.status === "submitted" && (
                                <td className="py-1">
                                  <button
                                    type="button"
                                    onClick={() => handleApprove(r.result_id)}
                                    disabled={approveOrReject.isPending}
                                    className="mr-2 rounded bg-green-600 px-2 py-1 text-xs text-white disabled:opacity-50"
                                  >
                                    Approve
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleReject(r.result_id)}
                                    disabled={approveOrReject.isPending}
                                    className="rounded bg-red-600 px-2 py-1 text-xs text-white disabled:opacity-50"
                                  >
                                    Reject
                                  </button>
                                </td>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {item.status === "submitted" && (
                        <input
                          type="text"
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                          placeholder="Comment (required if reject)"
                          className="mt-2 w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-900"
                        />
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      {data.items.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">No results in this status.</p>
      )}
    </div>
  );
}
