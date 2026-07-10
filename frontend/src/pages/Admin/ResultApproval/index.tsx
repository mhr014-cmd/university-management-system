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
import { AlertCircle, ClipboardCheck } from "lucide-react";
import { usePendingResults, useApproveOrRejectResult } from "../../../features/results";
import type { ResultStatus } from "../../../features/results";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { inputClass } from "../../../components/ui/classNames";

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
        <h1 className="shrink-0 text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Result Approval</h1>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as ResultStatus)}
          className={`!w-40 shrink-0 ${inputClass}`}
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {data.items.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title={`No results with status "${status}"`} />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2.5">Exam</th>
                <th className="px-4 py-2.5">Class</th>
                <th className="px-4 py-2.5">Submitted By</th>
                <th className="px-4 py-2.5">Date</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => {
                const key = `${item.exam_id}-${item.course_id}-${item.submitted_by_teacher_id}-${item.submitted_at}`;
                const isExpanded = expandedKey === key;
                return (
                  <Fragment key={key}>
                    <tr className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-2.5">{item.exam_title ?? "—"}</td>
                      <td className="px-4 py-2.5">{item.course_name}</td>
                      <td className="px-4 py-2.5">{item.submitted_by_teacher_name}</td>
                      <td className="px-4 py-2.5">{new Date(item.submitted_at).toLocaleDateString()}</td>
                      <td className="px-4 py-2.5">
                        <Button variant="secondary" size="sm" onClick={() => setExpandedKey(isExpanded ? null : key)}>
                          {isExpanded ? "Close" : "Review"}
                        </Button>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr>
                        <td colSpan={5} className="border-b border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/50">
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
                                      <div className="flex gap-2">
                                        <Button
                                          size="sm"
                                          variant="success"
                                          onClick={() => handleApprove(r.result_id)}
                                          isLoading={approveOrReject.isPending}
                                        >
                                          Approve
                                        </Button>
                                        <Button
                                          size="sm"
                                          variant="danger"
                                          onClick={() => handleReject(r.result_id)}
                                          isLoading={approveOrReject.isPending}
                                        >
                                          Reject
                                        </Button>
                                      </div>
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
                              className={`mt-2 ${inputClass}`}
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
        </Card>
      )}
    </div>
  );
}
