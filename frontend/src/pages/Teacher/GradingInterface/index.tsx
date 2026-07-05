// Teacher: Grading Interface page (FR-023, FR-024). Layout matches
// docs/UI_Wireframes.md Section 14: a submission selector, per-question
// marks/feedback inputs, and "Save Grades".
//
// Per-answer detail is fetched via GET /exams/{id}/submissions/{submission_id}
// — a Derived Engineering Addition added specifically to make this page
// buildable (POST /exams/{id}/grade needs answer_id values, but no existing
// endpoint returned a submission's actual answer content alongside them).
// See docs/Proposal_vs_Engineering_Additions.md.
//
// "Submit Results for Approval" (wireframe §14) is explicitly Milestone 7
// scope (it calls M7's POST /results/{examId}/submit) and is not
// implemented here. "Publish Exam" (making exam.status = "published",
// which reveals correct answers/marks to students per BR-001) is offered
// here instead, once every submission for the exam has status "graded" —
// the natural point in this workflow for that transition, per the
// status-transition mapping recorded in Teacher/ExamBuilder.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { isAxiosError } from "axios";
import {
  useExam,
  useExamResults,
  useGradeExam,
  useSubmissionDetail,
  useUpdateExam,
} from "../../../features/exams";

type GradeDraft = Record<string, { awardedMarks: string; feedback: string }>;

export default function GradingInterfacePage() {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const { data: exam } = useExam(examId);
  const { data: results } = useExamResults(examId);
  const [submissionId, setSubmissionId] = useState<string>("");
  const { data: detail, isLoading: isDetailLoading } = useSubmissionDetail(examId, submissionId || undefined);
  const gradeExam = useGradeExam();
  const updateExam = useUpdateExam();
  const [draft, setDraft] = useState<GradeDraft>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!results || results.submissions.length === 0) return;
    if (!submissionId) setSubmissionId(results.submissions[0].submission_id);
  }, [results, submissionId]);

  useEffect(() => {
    if (!detail) return;
    const next: GradeDraft = {};
    for (const question of detail.questions) {
      next[question.question_id] = {
        awardedMarks: question.awarded_marks !== null ? String(question.awarded_marks) : "",
        feedback: question.feedback ?? "",
      };
    }
    setDraft(next);
  }, [detail]);

  const allGraded = (results?.submissions.length ?? 0) > 0 && results!.submissions.every((s) => s.status === "graded");

  const handleSave = async () => {
    if (!examId || !detail) return;
    setMessage(null);
    setError(null);
    const grades = detail.questions
      .filter((q) => q.answer_id !== null)
      .map((q) => ({
        answer_id: q.answer_id as string,
        awarded_marks: Number(draft[q.question_id]?.awardedMarks ?? 0),
        feedback: draft[q.question_id]?.feedback || undefined,
      }));
    try {
      await gradeExam.mutateAsync({ examId, submissionId: detail.submission_id, grades });
      setMessage("Grades saved.");
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 422) {
        setError("A grade exceeds a question's maximum marks.");
      } else {
        setError("Could not save grades. Please try again.");
      }
    }
  };

  const handlePublish = async () => {
    if (!examId) return;
    setMessage(null);
    setError(null);
    try {
      await updateExam.mutateAsync({ id: examId, payload: { status: "published" } });
      setMessage("Exam published. Students can now see their results.");
      navigate("/exams");
    } catch {
      setError("Could not publish the exam. Please try again.");
    }
  };

  if (!exam || !results) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading...</p>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Grading: {exam.title}</h1>

      {message && (
        <div className="rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
          {message}
        </div>
      )}
      {error && (
        <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {results.submissions.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No submissions yet.</p>
      ) : (
        <div className="flex items-center gap-4 text-sm">
          <select
            value={submissionId}
            onChange={(e) => setSubmissionId(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
          >
            {results.submissions.map((submission) => (
              <option key={submission.submission_id} value={submission.submission_id}>
                {submission.student_name} — {submission.status} ({submission.total_awarded_marks} marks)
              </option>
            ))}
          </select>
          {allGraded && (
            <button
              type="button"
              onClick={handlePublish}
              disabled={updateExam.isPending}
              className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
            >
              Publish Exam
            </button>
          )}
        </div>
      )}

      {isDetailLoading || !detail ? (
        submissionId && <p className="text-sm text-slate-500 dark:text-slate-400">Loading submission...</p>
      ) : (
        <div className="space-y-4">
          {detail.questions.map((question, index) => (
            <div key={question.question_id} className="space-y-2 rounded border border-slate-200 p-3 dark:border-slate-700">
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                {index + 1}. {question.question_text}{" "}
                <span className="text-xs font-normal text-slate-500 dark:text-slate-400">
                  (max {question.marks} marks)
                </span>
              </p>

              {question.answer_id === null ? (
                <p className="text-sm italic text-slate-500 dark:text-slate-400">Not answered.</p>
              ) : (
                <>
                  <p className="rounded bg-slate-50 px-2 py-1 text-sm dark:bg-slate-800">
                    {question.answer_text ?? question.selected_option_id ?? "—"}
                  </p>
                  <div className="flex items-center gap-4 text-sm">
                    <input
                      type="number"
                      min={0}
                      max={question.marks}
                      step={0.01}
                      value={draft[question.question_id]?.awardedMarks ?? ""}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          [question.question_id]: {
                            awardedMarks: e.target.value,
                            feedback: prev[question.question_id]?.feedback ?? "",
                          },
                        }))
                      }
                      className="w-24 rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
                      placeholder="Marks"
                    />
                    <input
                      type="text"
                      value={draft[question.question_id]?.feedback ?? ""}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          [question.question_id]: {
                            awardedMarks: prev[question.question_id]?.awardedMarks ?? "",
                            feedback: e.target.value,
                          },
                        }))
                      }
                      placeholder="Feedback (optional)"
                      className="flex-1 rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
                    />
                  </div>
                </>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={handleSave}
            disabled={gradeExam.isPending}
            className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
          >
            Save Grades
          </button>
        </div>
      )}
    </div>
  );
}
