// Teacher: Exam Builder page (FR-018, FR-020). Layout matches
// docs/UI_Wireframes.md Section 13: Class selector, title/type/time-limit
// fields, a dynamic question editor (type selector, marks, hint, MCQ
// options with a correct-answer checkbox), "Save Draft", and
// "Publish Exam".
//
// Status-transition mapping (resolved during the Milestone 6
// pre-implementation review — see docs/Requirement_Traceability_Matrix.md):
// "Save Draft" calls POST/PUT without a `status` field, leaving the exam in
// its current status (draft by default on create). "Publish Exam" here
// specifically means making the exam available for students to start
// (`status: "open"`) — the exam-level `published` status, which reveals
// correct answers/marks to students per BR-001, is a separate later action
// taken from the Grading Interface once every submission has been graded.
//
// Editing is blocked once status === "published" (BR-003), matching
// ExamService.update_exam's server-side 409.
//
// Gap closure (GC-3): the proposal (§7) and UI_Wireframes.md both specify
// a Preview toggle ("renders the exam as a Student would see it,
// read-only"), absent until now. Preview renders the exact in-progress
// `questions`/`title`/`examType`/`timeLimitMinutes` state already held
// below — no second data model, no server round trip (the draft isn't
// saved yet, so there is nothing else to fetch) — visually mirroring
// ExamRoomPage's question-navigator/MCQ-radio-group/textarea layout
// without importing it directly, since ExamRoomPage consumes
// server-shaped `ExamRead` (real question/option ids), not this page's
// pre-save `QuestionInput[]` draft shape.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { isAxiosError } from "axios";
import { AlertCircle, AlertTriangle, CheckCircle2, Eye, Pencil, Plus, Trash2 } from "lucide-react";
import { useMySchedule } from "../../../features/schedule";
import { useCreateExam, useExam, useUpdateExam } from "../../../features/exams";
import type { ExamType, QuestionInput, QuestionType } from "../../../features/exams";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { PageLoader } from "../../../components/ui/PageLoader";
import { inputClass } from "../../../components/ui/classNames";

const EXAM_TYPE_OPTIONS: ExamType[] = ["mcq", "written", "practical_coding", "mixed"];
const QUESTION_TYPE_OPTIONS: QuestionType[] = ["mcq", "short_answer", "descriptive", "coding"];

function blankQuestion(orderIndex: number): QuestionInput {
  return {
    question_text: "",
    question_type: "mcq",
    marks: 1,
    hint: "",
    order_index: orderIndex,
    options: [
      { option_text: "", is_correct: true },
      { option_text: "", is_correct: false },
    ],
  };
}

export default function ExamBuilderPage() {
  const { examId } = useParams<{ examId?: string }>();
  const navigate = useNavigate();
  const isEditMode = Boolean(examId);

  const { data: schedule } = useMySchedule();
  const { data: existingExam } = useExam(examId);
  const createExam = useCreateExam();
  const updateExam = useUpdateExam();

  const [classSessionId, setClassSessionId] = useState("");
  const [title, setTitle] = useState("");
  const [examType, setExamType] = useState<ExamType>("mcq");
  const [timeLimitMinutes, setTimeLimitMinutes] = useState(30);
  const [questions, setQuestions] = useState<QuestionInput[]>([blankQuestion(0)]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Preview mode (GC-3): read-only render of the state above, exactly as
  // a Student would see it — no separate copy of the exam data.
  const [isPreview, setIsPreview] = useState(false);
  const [previewIndex, setPreviewIndex] = useState(0);

  useEffect(() => {
    if (!existingExam) return;
    setClassSessionId(existingExam.class_session_id);
    setTitle(existingExam.title);
    setExamType(existingExam.exam_type);
    setTimeLimitMinutes(existingExam.time_limit_minutes);
    setQuestions(
      existingExam.questions.map((q) => ({
        question_text: q.question_text,
        question_type: q.question_type,
        marks: q.marks,
        hint: q.hint ?? "",
        order_index: q.order_index,
        options: (q.options ?? []).map((o) => ({ option_text: o.option_text, is_correct: o.is_correct ?? false })),
      })),
    );
  }, [existingExam]);

  const isPublished = existingExam?.status === "published";

  const uniqueClassSessions = Array.from(
    new Map((schedule?.entries ?? []).map((entry) => [entry.class_session_id, entry.course_name])).entries(),
  );

  const updateQuestion = (index: number, patch: Partial<QuestionInput>) => {
    setQuestions((prev) => prev.map((q, i) => (i === index ? { ...q, ...patch } : q)));
  };

  const addQuestion = () => {
    setQuestions((prev) => [...prev, blankQuestion(prev.length)]);
  };

  const removeQuestion = (index: number) => {
    setQuestions((prev) => prev.filter((_, i) => i !== index).map((q, i) => ({ ...q, order_index: i })));
  };

  const addOption = (questionIndex: number) => {
    setQuestions((prev) =>
      prev.map((q, i) => (i === questionIndex ? { ...q, options: [...q.options, { option_text: "", is_correct: false }] } : q)),
    );
  };

  const removeOption = (questionIndex: number, optionIndex: number) => {
    setQuestions((prev) =>
      prev.map((q, i) =>
        i === questionIndex ? { ...q, options: q.options.filter((_, oi) => oi !== optionIndex) } : q,
      ),
    );
  };

  const save = async (status?: "open") => {
    setMessage(null);
    setError(null);
    const payload = {
      class_session_id: classSessionId,
      title,
      exam_type: examType,
      time_limit_minutes: timeLimitMinutes,
      questions,
    };
    try {
      if (isEditMode && examId) {
        await updateExam.mutateAsync({ id: examId, payload: { ...payload, status } });
      } else {
        await createExam.mutateAsync(payload);
      }
      setMessage(status === "open" ? "Exam published and open for students." : "Draft saved.");
      if (status === "open") navigate("/exams");
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 422) {
        setError("Every MCQ question needs at least one correct option, and all required fields must be filled in.");
      } else if (isAxiosError(err) && err.response?.status === 409) {
        setError("This exam has already been published and can no longer be edited.");
      } else {
        setError("Could not save the exam. Please try again.");
      }
    }
  };

  if (isEditMode && !existingExam) {
    return <PageLoader label="Loading exam..." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
          {isEditMode ? "Edit Exam" : "New Exam"}
        </h1>
        <Button
          variant="secondary"
          size="sm"
          icon={isPreview ? <Pencil className="h-3.5 w-3.5" aria-hidden="true" /> : <Eye className="h-3.5 w-3.5" aria-hidden="true" />}
          onClick={() => {
            setPreviewIndex(0);
            setIsPreview((prev) => !prev);
          }}
        >
          {isPreview ? "Back to Edit" : "Preview"}
        </Button>
      </div>

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
      {isPublished && (
        <div className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-700 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>This exam is published and read-only.</span>
        </div>
      )}

      {isPreview ? (
        <div className="flex gap-4">
          <aside className="w-40 shrink-0 space-y-1">
            {questions.map((_, qIndex) => (
              <button
                key={qIndex}
                type="button"
                onClick={() => setPreviewIndex(qIndex)}
                className={`w-full rounded-md border px-2 py-1.5 text-left text-sm ${
                  qIndex === previewIndex
                    ? "border-indigo-300 bg-indigo-50 text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950/50 dark:text-indigo-300"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800/50"
                }`}
              >
                Question {qIndex + 1}
              </button>
            ))}
          </aside>
          <Card className="flex-1 space-y-3">
            <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">
              {title || "Untitled exam"} · {examType} · {timeLimitMinutes} min
            </p>
            {questions[previewIndex] && (
              <>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {previewIndex + 1}. {questions[previewIndex].question_text || "(no question text yet)"}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{questions[previewIndex].marks} marks</p>
                {questions[previewIndex].question_type === "mcq" ? (
                  <div className="space-y-2">
                    {questions[previewIndex].options.map((option, oIndex) => (
                      <label key={oIndex} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <input type="radio" disabled name={`preview-question-${previewIndex}`} />
                        {option.option_text || "(empty option)"}
                      </label>
                    ))}
                  </div>
                ) : (
                  <textarea disabled rows={4} placeholder="Student's answer" className={inputClass} />
                )}
              </>
            )}
          </Card>
        </div>
      ) : (
      <fieldset disabled={isPublished} className="space-y-4">
        <div className="flex items-center gap-4 text-sm">
          <select
            value={classSessionId}
            onChange={(e) => setClassSessionId(e.target.value)}
            disabled={isEditMode}
            className={`w-auto ${inputClass}`}
          >
            <option value="">Select Class</option>
            {uniqueClassSessions.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
          <select value={examType} onChange={(e) => setExamType(e.target.value as ExamType)} className={`w-auto ${inputClass}`}>
            {EXAM_TYPE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <input
            type="number"
            min={1}
            value={timeLimitMinutes}
            onChange={(e) => setTimeLimitMinutes(Number(e.target.value))}
            className={`w-28 ${inputClass}`}
            placeholder="Minutes"
          />
        </div>
        <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Exam title" className={inputClass} />

        <div className="space-y-4">
          {questions.map((question, qIndex) => (
            <Card key={qIndex} className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">Question {qIndex + 1}</span>
                <Button variant="ghost" size="sm" icon={<Trash2 className="h-3.5 w-3.5" aria-hidden="true" />} onClick={() => removeQuestion(qIndex)}>
                  Remove
                </Button>
              </div>
              <textarea
                value={question.question_text}
                onChange={(e) => updateQuestion(qIndex, { question_text: e.target.value })}
                placeholder="Question text"
                rows={2}
                className={inputClass}
              />
              <div className="flex items-center gap-4 text-sm">
                <select
                  value={question.question_type}
                  onChange={(e) => updateQuestion(qIndex, { question_type: e.target.value as QuestionType })}
                  className={`w-auto ${inputClass}`}
                >
                  {QUESTION_TYPE_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min={0.01}
                  step={0.01}
                  value={question.marks}
                  onChange={(e) => updateQuestion(qIndex, { marks: Number(e.target.value) })}
                  className={`w-24 ${inputClass}`}
                  placeholder="Marks"
                />
                <input
                  type="text"
                  value={question.hint ?? ""}
                  onChange={(e) => updateQuestion(qIndex, { hint: e.target.value })}
                  placeholder="Hint (optional)"
                  className={`flex-1 ${inputClass}`}
                />
              </div>

              {question.question_type === "mcq" && (
                <div className="space-y-2 pl-4">
                  {question.options.map((option, oIndex) => (
                    <div key={oIndex} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={option.is_correct}
                        onChange={(e) => {
                          const nextOptions = question.options.map((o, i) => ({
                            ...o,
                            is_correct: i === oIndex ? e.target.checked : o.is_correct,
                          }));
                          updateQuestion(qIndex, { options: nextOptions });
                        }}
                      />
                      <input
                        type="text"
                        value={option.option_text}
                        onChange={(e) => {
                          const nextOptions = question.options.map((o, i) =>
                            i === oIndex ? { ...o, option_text: e.target.value } : o,
                          );
                          updateQuestion(qIndex, { options: nextOptions });
                        }}
                        placeholder="Option text"
                        className={`flex-1 ${inputClass}`}
                      />
                      <Button variant="ghost" size="sm" onClick={() => removeOption(qIndex, oIndex)}>
                        Remove
                      </Button>
                    </div>
                  ))}
                  <Button variant="ghost" size="sm" icon={<Plus className="h-3.5 w-3.5" aria-hidden="true" />} onClick={() => addOption(qIndex)}>
                    Add option
                  </Button>
                </div>
              )}
            </Card>
          ))}
          <Button variant="secondary" icon={<Plus className="h-4 w-4" aria-hidden="true" />} onClick={addQuestion}>
            Add question
          </Button>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <Button variant="secondary" onClick={() => save(undefined)} isLoading={createExam.isPending || updateExam.isPending}>
            Save Draft
          </Button>
          <Button onClick={() => save("open")} isLoading={createExam.isPending || updateExam.isPending}>
            Publish Exam
          </Button>
        </div>
      </fieldset>
      )}
    </div>
  );
}
