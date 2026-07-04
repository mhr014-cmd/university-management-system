// Exam Room page (FR-022). Layout matches docs/UI_Wireframes.md Section 5:
// persistent countdown timer, question navigator sidebar, MCQ radio group /
// textarea per question, a confirmation-gated Submit, and timer-expiry
// auto-submit.
//
// Per the wireframe, answers are autosaved client-side only — there is no
// server round trip until the final submit. The one exception (the reason
// POST /exams/{id}/start exists as a Derived Engineering Addition, see
// docs/Proposal_vs_Engineering_Additions.md) is starting the attempt: the
// countdown is always computed from the server-recorded `started_at`
// returned by /start, never a client-side clock, so a page refresh cannot
// extend a student's time limit.

import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useExam, useStartExam, useSubmitExam } from "../../features/exams";
import type { AnswerInput } from "../../features/exams";

type AnswerState = Record<string, { answer_text?: string; selected_option_id?: string }>;

export default function ExamRoomPage() {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const { data: exam, isLoading: isExamLoading } = useExam(examId);
  const startExam = useStartExam();
  const submitExam = useSubmitExam();

  const [startedAt, setStartedAt] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerState>({});
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const hasStarted = useRef(false);
  const hasAutoSubmitted = useRef(false);

  useEffect(() => {
    if (!examId || hasStarted.current) return;
    hasStarted.current = true;
    startExam
      .mutateAsync(examId)
      .then((response) => setStartedAt(response.started_at))
      .catch(() => setError("Could not start this exam. It may not be open, or you may not be enrolled."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [examId]);

  const deadline = useMemo(() => {
    if (!startedAt || !exam) return null;
    return new Date(startedAt).getTime() + exam.time_limit_minutes * 60 * 1000;
  }, [startedAt, exam]);

  const doSubmit = async () => {
    if (!examId || submitted) return;
    const payload: AnswerInput[] = Object.entries(answers).map(([question_id, value]) => ({
      question_id,
      answer_text: value.answer_text,
      selected_option_id: value.selected_option_id,
    }));
    try {
      await submitExam.mutateAsync({ examId, answers: payload });
      setSubmitted(true);
    } catch {
      setError("Could not submit the exam. Please try again.");
    }
  };

  useEffect(() => {
    if (!deadline) return;
    const interval = setInterval(() => {
      const secondsLeft = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
      setRemainingSeconds(secondsLeft);
      if (secondsLeft <= 0 && !hasAutoSubmitted.current && !submitted) {
        hasAutoSubmitted.current = true;
        void doSubmit();
      }
    }, 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deadline, submitted]);

  if (isExamLoading || !exam) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading exam...</p>;
  }

  if (submitted) {
    return (
      <div className="space-y-4">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Exam submitted</h1>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Your answers for &ldquo;{exam.title}&rdquo; have been submitted.
        </p>
        <button
          type="button"
          onClick={() => navigate("/exams")}
          className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          Back to Exams
        </button>
      </div>
    );
  }

  const minutes = remainingSeconds !== null ? Math.floor(remainingSeconds / 60) : null;
  const seconds = remainingSeconds !== null ? remainingSeconds % 60 : null;
  const currentQuestion = exam.questions[currentIndex];

  const handleSubmitClick = () => {
    if (window.confirm("Submit this exam? You will not be able to change your answers afterwards.")) {
      void doSubmit();
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">{exam.title}</h1>
        <div className="rounded border border-slate-300 px-3 py-1 text-sm font-mono dark:border-slate-600">
          {minutes !== null && seconds !== null
            ? `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
            : "--:--"}
        </div>
      </div>

      {error && (
        <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="flex gap-6">
        <aside className="w-40 shrink-0 space-y-1">
          {exam.questions.map((question, index) => (
            <button
              key={question.id}
              type="button"
              onClick={() => setCurrentIndex(index)}
              className={`block w-full rounded px-2 py-1 text-left text-sm ${
                index === currentIndex
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                  : answers[question.id]
                    ? "border border-green-300 dark:border-green-800"
                    : "border border-slate-300 dark:border-slate-600"
              }`}
            >
              Q{index + 1}
            </button>
          ))}
        </aside>

        {currentQuestion && (
          <div className="flex-1 space-y-3">
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
              {currentIndex + 1}. {currentQuestion.question_text}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">{currentQuestion.marks} marks</p>

            {currentQuestion.question_type === "mcq" ? (
              <div className="space-y-2">
                {(currentQuestion.options ?? []).map((option) => (
                  <label key={option.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="radio"
                      name={`question-${currentQuestion.id}`}
                      checked={answers[currentQuestion.id]?.selected_option_id === option.id}
                      onChange={() =>
                        setAnswers((prev) => ({
                          ...prev,
                          [currentQuestion.id]: { selected_option_id: option.id },
                        }))
                      }
                    />
                    {option.option_text}
                  </label>
                ))}
              </div>
            ) : (
              <textarea
                value={answers[currentQuestion.id]?.answer_text ?? ""}
                onChange={(e) =>
                  setAnswers((prev) => ({
                    ...prev,
                    [currentQuestion.id]: { answer_text: e.target.value },
                  }))
                }
                rows={8}
                className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
              />
            )}

            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                disabled={currentIndex === 0}
                onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
                className="rounded border border-slate-300 px-3 py-2 text-sm disabled:opacity-50 dark:border-slate-600"
              >
                Previous
              </button>
              {currentIndex < exam.questions.length - 1 ? (
                <button
                  type="button"
                  onClick={() => setCurrentIndex((i) => Math.min(exam.questions.length - 1, i + 1))}
                  className="rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600"
                >
                  Next
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSubmitClick}
                  disabled={submitExam.isPending}
                  className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
                >
                  Submit Exam
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
