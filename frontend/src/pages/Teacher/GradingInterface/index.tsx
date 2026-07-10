// Teacher: Grading Interface page (FR-023, FR-024, FR-034). Layout
// matches docs/UI_Wireframes.md Section 14: a submission selector,
// per-question marks/feedback inputs, "Save Grades", "Publish Exam",
// and — once published and fully graded — "Submit Results for
// Approval".
//
// Per-answer detail is fetched via GET /exams/{id}/submissions/{submission_id}
// — a Derived Engineering Addition added specifically to make this page
// buildable (POST /exams/{id}/grade needs answer_id values, but no existing
// endpoint returned a submission's actual answer content alongside them).
// See docs/Proposal_vs_Engineering_Additions.md.
//
// "Publish Exam" (making exam.status = "published", which reveals correct
// answers/marks to students per BR-001) is offered once every submission
// has status "graded". POST /results/{examId}/submit (FR-034) requires
// exam.status = "published" as a precondition (API_Contract.md §5.2), so
// the "Submit Results for Approval" section below only appears after
// that transition — grade_letter/grade_point are Teacher-supplied per
// student, not computed from marks (no letter-grade-boundary scheme is
// hard-coded anywhere, per Requirement_Analysis.md's A-004 resolution);
// each awarded-marks total is shown alongside the inputs as context.

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { isAxiosError } from "axios";
import { AlertCircle, CheckCircle2, FileText } from "lucide-react";
import {
  useExam,
  useExamResults,
  useGradeExam,
  useSubmissionDetail,
  useUpdateExam,
} from "../../../features/exams";
import { useSubmitResults } from "../../../features/results";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { PageLoader } from "../../../components/ui/PageLoader";
import { inputClass } from "../../../components/ui/classNames";

type ResultDraft = Record<string, { gradeLetter: string; gradePoint: string }>;

type GradeDraft = Record<string, { awardedMarks: string; feedback: string }>;

export default function GradingInterfacePage() {
  const { examId } = useParams<{ examId: string }>();
  const { data: exam } = useExam(examId);
  const { data: results } = useExamResults(examId);
  const [submissionId, setSubmissionId] = useState<string>("");
  const { data: detail, isLoading: isDetailLoading } = useSubmissionDetail(examId, submissionId || undefined);
  const gradeExam = useGradeExam();
  const updateExam = useUpdateExam();
  const submitResults = useSubmitResults();
  const [draft, setDraft] = useState<GradeDraft>({});
  const [resultDraft, setResultDraft] = useState<ResultDraft>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);

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
      setMessage("Exam published. Students can now see their results — submit results below for admin approval.");
    } catch {
      setError("Could not publish the exam. Please try again.");
    }
  };

  const handleSubmitResults = async () => {
    if (!examId || !results) return;
    setSubmitMessage(null);
    setSubmitError(null);
    const entries = results.submissions
      .filter((s) => s.status === "graded")
      .map((s) => ({
        student_id: s.student_id,
        grade_letter: resultDraft[s.student_id]?.gradeLetter ?? "",
        grade_point: Number(resultDraft[s.student_id]?.gradePoint ?? ""),
      }));
    if (entries.some((e) => !e.grade_letter || Number.isNaN(e.grade_point))) {
      setSubmitError("Enter a grade letter and grade point (0-4) for every student before submitting.");
      return;
    }
    try {
      await submitResults.mutateAsync({ examId, results: entries });
      setSubmitMessage("Results submitted for admin approval.");
    } catch (err) {
      // Surface the backend's own validation message (Domain Rules 1-7 for
      // this endpoint each produce a distinct reason — enrollment, grading
      // completeness, duplicate submission, etc.) rather than guessing
      // from the status code alone, same pattern as Admin/FeeDashboard.
      if (isAxiosError(err) && err.response?.data?.error?.message) {
        setSubmitError(err.response.data.error.message);
      } else {
        setSubmitError("Could not submit results. Please try again.");
      }
    }
  };

  if (!exam || !results) {
    return <PageLoader />;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Grading: {exam.title}</h1>

      {message && (
        <div className="flex items-start gap-2 rounded-md border border-green-200 bg-green-50 px-3 py-2.5 text-sm text-green-700 dark:border-green-900 dark:bg-green-950/50 dark:text-green-300">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{message}</span>
        </div>
      )}
      {error && (
        <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {results.submissions.length === 0 ? (
        <EmptyState icon={FileText} title="No submissions yet" />
      ) : (
        <div className="flex items-center gap-4 text-sm">
          <select value={submissionId} onChange={(e) => setSubmissionId(e.target.value)} className={`w-auto ${inputClass}`}>
            {results.submissions.map((submission) => (
              <option key={submission.submission_id} value={submission.submission_id}>
                {submission.student_name} — {submission.status} ({submission.total_awarded_marks} marks)
              </option>
            ))}
          </select>
          {allGraded && exam.status !== "published" && (
            <Button onClick={handlePublish} isLoading={updateExam.isPending}>
              Publish Exam
            </Button>
          )}
        </div>
      )}

      {allGraded && exam.status === "published" && (
        <Card className="space-y-3">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Submit Results for Admin Approval
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Enter a grade letter and grade point (0-4) for each student, then submit for admin review. Results are
            not visible to students or parents until an Admin approves them.
          </p>

          {submitMessage && (
            <div className="flex items-start gap-2 rounded-md border border-green-200 bg-green-50 px-3 py-2.5 text-sm text-green-700 dark:border-green-900 dark:bg-green-950/50 dark:text-green-300">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{submitMessage}</span>
            </div>
          )}
          {submitError && (
            <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{submitError}</span>
            </div>
          )}

          <div className="space-y-2">
            {results.submissions
              .filter((s) => s.status === "graded")
              .map((submission) => (
                <div key={submission.student_id} className="flex items-center gap-4 text-sm">
                  <span className="w-40 shrink-0 text-slate-700 dark:text-slate-300">{submission.student_name}</span>
                  <span className="w-28 shrink-0 text-xs text-slate-500 dark:text-slate-400">
                    {submission.total_awarded_marks} marks awarded
                  </span>
                  <input
                    type="text"
                    value={resultDraft[submission.student_id]?.gradeLetter ?? ""}
                    onChange={(e) =>
                      setResultDraft((prev) => ({
                        ...prev,
                        [submission.student_id]: {
                          gradeLetter: e.target.value,
                          gradePoint: prev[submission.student_id]?.gradePoint ?? "",
                        },
                      }))
                    }
                    placeholder="Grade letter (e.g. A)"
                    className={`!w-40 shrink-0 ${inputClass}`}
                  />
                  <input
                    type="number"
                    min={0}
                    max={4}
                    step={0.01}
                    value={resultDraft[submission.student_id]?.gradePoint ?? ""}
                    onChange={(e) =>
                      setResultDraft((prev) => ({
                        ...prev,
                        [submission.student_id]: {
                          gradeLetter: prev[submission.student_id]?.gradeLetter ?? "",
                          gradePoint: e.target.value,
                        },
                      }))
                    }
                    placeholder="Grade point"
                    className={`!w-32 shrink-0 ${inputClass}`}
                  />
                </div>
              ))}
          </div>

          <Button onClick={handleSubmitResults} isLoading={submitResults.isPending}>
            Submit Results for Approval
          </Button>
        </Card>
      )}

      {isDetailLoading || !detail ? (
        submissionId && <PageLoader label="Loading submission..." />
      ) : (
        <div className="space-y-4">
          {detail.questions.map((question, index) => (
            <Card key={question.question_id} className="space-y-2">
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
                  <p className="rounded-md bg-slate-50 px-3 py-1.5 text-sm dark:bg-slate-800">
                    {question.answer_text ?? question.selected_option_text ?? "—"}
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
                      className={`!w-24 shrink-0 ${inputClass}`}
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
                      className={`min-w-0 flex-1 ${inputClass}`}
                    />
                  </div>
                </>
              )}
            </Card>
          ))}

          <Button onClick={handleSave} isLoading={gradeExam.isPending}>
            Save Grades
          </Button>
        </div>
      )}
    </div>
  );
}
