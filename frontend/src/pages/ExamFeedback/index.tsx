// Student/Parent: Exam Feedback page (final-verification-pass addition,
// Feature 2). Read-only. Surfaces the per-question feedback and awarded
// marks a Teacher already saves via the Grading Interface
// (question_grade.feedback) — previously captured but never shown to the
// student who earned it anywhere in the frontend. Reached from ExamList
// by clicking a published exam (Student) or navigated to directly with a
// linked child selected (Parent, same ownership pattern as every other
// Parent-facing page in this app).
//
// No grading logic here at all — this only renders what
// GET /exams/{examId}/my-submission already returns.

import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, MessageSquare, Users } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { useMySubmissionDetail } from "../../features/exams";
import { useMyChildren } from "../../features/users";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";
import { inputClass } from "../../components/ui/classNames";

function FeedbackPanel({ examId, studentId }: { examId: string; studentId?: string }) {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useMySubmissionDetail(examId, { studentId });

  if (isLoading) {
    return <PageLoader label="Loading feedback..." />;
  }

  if (isError || !data) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="No feedback available"
        description="You haven't submitted this exam, or it hasn't been published yet."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Exam Feedback</h1>
        <Button
          variant="secondary"
          size="sm"
          icon={<ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />}
          onClick={() => navigate("/exams")}
        >
          Back to Exams
        </Button>
      </div>

      {data.questions.length === 0 ? (
        <EmptyState icon={MessageSquare} title="No questions on this exam" />
      ) : (
        <div className="space-y-3">
          {data.questions
            .slice()
            .sort((a, b) => a.order_index - b.order_index)
            .map((question) => (
              <Card key={question.question_id}>
                <div className="flex items-start justify-between gap-4">
                  <p className="font-medium text-slate-900 dark:text-slate-100">{question.question_text}</p>
                  <Badge tone={question.awarded_marks !== null ? "green" : "neutral"}>
                    {question.awarded_marks !== null ? `${question.awarded_marks} / ${question.marks}` : `— / ${question.marks}`}
                  </Badge>
                </div>
                {(question.answer_text ?? question.selected_option_text) && (
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                    Your answer:{" "}
                    <span className="text-slate-800 dark:text-slate-200">
                      {question.answer_text ?? question.selected_option_text}
                    </span>
                  </p>
                )}
                {question.feedback ? (
                  <div className="mt-3 flex items-start gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-800/50">
                    <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" aria-hidden="true" />
                    <p className="text-sm text-slate-700 dark:text-slate-300">{question.feedback}</p>
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-400 dark:text-slate-500">No feedback left for this question.</p>
                )}
              </Card>
            ))}
        </div>
      )}
    </div>
  );
}

export default function ExamFeedbackPage() {
  const { examId } = useParams<{ examId: string }>();
  const { user } = useAuth();

  if (!examId) return null;

  if (user?.role === "parent") {
    return <ParentExamFeedback examId={examId} />;
  }
  return <FeedbackPanel examId={examId} />;
}

function ParentExamFeedback({ examId }: { examId: string }) {
  const { data: childrenData, isLoading: childrenLoading, isError: childrenError } = useMyChildren();
  const children = useMemo(() => childrenData?.children ?? [], [childrenData]);
  const [selectedStudentId, setSelectedStudentId] = useState("");

  useEffect(() => {
    if (!selectedStudentId && children.length > 0) {
      setSelectedStudentId(children[0].id);
    }
  }, [children, selectedStudentId]);

  return (
    <div className="space-y-4">
      <Card data-print-hidden>
        <div className="mb-2 flex items-center gap-2">
          <Users className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Linked Child</p>
        </div>
        {childrenLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading your linked children...</p>
        ) : childrenError ? (
          <p className="text-sm text-red-600 dark:text-red-400">Unable to load linked children.</p>
        ) : children.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No children linked yet"
            description="Contact an administrator to link a child's record to your account."
          />
        ) : (
          <select
            value={selectedStudentId}
            onChange={(e) => setSelectedStudentId(e.target.value)}
            className={inputClass}
          >
            {children.map((child) => (
              <option key={child.id} value={child.id}>
                {child.first_name} {child.last_name}
              </option>
            ))}
          </select>
        )}
      </Card>

      {selectedStudentId && <FeedbackPanel examId={examId} studentId={selectedStudentId} />}
    </div>
  );
}
