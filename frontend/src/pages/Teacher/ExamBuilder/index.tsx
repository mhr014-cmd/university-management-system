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

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { isAxiosError } from "axios";
import { useMySchedule } from "../../../features/schedule";
import { useCreateExam, useExam, useUpdateExam } from "../../../features/exams";
import type { ExamType, QuestionInput, QuestionType } from "../../../features/exams";

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
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading exam...</p>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
        {isEditMode ? "Edit Exam" : "New Exam"}
      </h1>

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
      {isPublished && (
        <div className="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-700 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300">
          This exam is published and read-only.
        </div>
      )}

      <fieldset disabled={isPublished} className="space-y-3">
        <div className="flex items-center gap-4 text-sm">
          <select
            value={classSessionId}
            onChange={(e) => setClassSessionId(e.target.value)}
            disabled={isEditMode}
            className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
          >
            <option value="">Select Class</option>
            {uniqueClassSessions.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
          <select
            value={examType}
            onChange={(e) => setExamType(e.target.value as ExamType)}
            className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
          >
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
            className="w-28 rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
            placeholder="Minutes"
          />
        </div>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Exam title"
          className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
        />

        <div className="space-y-4">
          {questions.map((question, qIndex) => (
            <div key={qIndex} className="space-y-2 rounded border border-slate-200 p-3 dark:border-slate-700">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Question {qIndex + 1}</span>
                <button
                  type="button"
                  onClick={() => removeQuestion(qIndex)}
                  className="text-xs text-red-600 dark:text-red-400"
                >
                  Remove
                </button>
              </div>
              <textarea
                value={question.question_text}
                onChange={(e) => updateQuestion(qIndex, { question_text: e.target.value })}
                placeholder="Question text"
                rows={2}
                className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
              />
              <div className="flex items-center gap-4 text-sm">
                <select
                  value={question.question_type}
                  onChange={(e) => updateQuestion(qIndex, { question_type: e.target.value as QuestionType })}
                  className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
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
                  className="w-24 rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
                  placeholder="Marks"
                />
                <input
                  type="text"
                  value={question.hint ?? ""}
                  onChange={(e) => updateQuestion(qIndex, { hint: e.target.value })}
                  placeholder="Hint (optional)"
                  className="flex-1 rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
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
                        className="flex-1 rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
                      />
                      <button
                        type="button"
                        onClick={() => removeOption(qIndex, oIndex)}
                        className="text-xs text-red-600 dark:text-red-400"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addOption(qIndex)}
                    className="text-xs text-slate-600 dark:text-slate-400"
                  >
                    + Add option
                  </button>
                </div>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={addQuestion}
            className="rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600"
          >
            + Add question
          </button>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => save(undefined)}
            disabled={createExam.isPending || updateExam.isPending}
            className="rounded border border-slate-300 px-3 py-2 text-sm disabled:opacity-50 dark:border-slate-600"
          >
            Save Draft
          </button>
          <button
            type="button"
            onClick={() => save("open")}
            disabled={createExam.isPending || updateExam.isPending}
            className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
          >
            Publish Exam
          </button>
        </div>
      </fieldset>
    </div>
  );
}
