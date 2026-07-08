// Exam List page (FR-017, FR-019). Layout matches docs/UI_Wireframes.md
// Section 4: Class/Status filter dropdowns, a table of Title/Class/Status/
// Date, row-click navigation that depends on role and status.
//
// Known simplification: the wireframe's "Graded" derived display label
// (exam.status === "closed" AND every submission has question_grade
// entries) is not computed here — it would require an extra
// GET /exams/{id}/results round trip per row. The raw exam.status is
// shown instead; Teachers can see full grading progress by opening the
// Grading Interface. See PROJECT_PROGRESS.md's Milestone 6 entry.
//
// "Draft" exams are never shown to Students — enforced server-side in
// ExamService.list_exams, not re-implemented here (CLAUDE.md Section 7:
// client-side hiding is UX only).
//
// Audit fix (critical A1): GET /exams requires student_id for a Parent
// caller, but this page never offered a Parent a way to pick a linked
// child, so a Parent following the Dashboard's "Upcoming Exams" card hit
// a 403 that rendered as a permanent "Loading exams..." spinner. Reuses
// the exact "Linked Child" selector pattern already used by
// Attendance/FeeCentre/ResultsView/Timetable (useMyChildren, auto-select
// the first/only child) — no new component, no backend change.

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileQuestion, Plus, Users } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { useMySchedule } from "../../features/schedule";
import { useExams } from "../../features/exams";
import type { ExamStatus } from "../../features/exams";
import { useMyChildren } from "../../features/users";
import { Badge, type BadgeTone } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";
import { inputClass } from "../../components/ui/classNames";

const STATUS_OPTIONS: ExamStatus[] = ["draft", "scheduled", "open", "closed", "published"];

const examStatusTone: Record<ExamStatus, BadgeTone> = {
  draft: "neutral",
  scheduled: "blue",
  open: "green",
  closed: "amber",
  published: "neutral",
};

export default function ExamListPage() {
  const { user } = useAuth();
  if (user?.role === "parent") {
    return <ParentExamList />;
  }
  return <ExamListContent />;
}

// Same child-selector convention as FeeCentre's ParentFeeCentre /
// ResultsView's ParentResultsView / Attendance's ParentAttendanceView.
function ParentExamList() {
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
      <Card>
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

      {selectedStudentId && <ExamListContent studentId={selectedStudentId} />}
    </div>
  );
}

function ExamListContent({ studentId }: { studentId?: string }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [classSessionId, setClassSessionId] = useState("");
  const [status, setStatus] = useState("");

  const { data: schedule } = useMySchedule(studentId);
  const { data, isLoading } = useExams({
    classSessionId: classSessionId || undefined,
    status: status || undefined,
    studentId,
  });

  const uniqueClassSessions = Array.from(
    new Map((schedule?.entries ?? []).map((entry) => [entry.class_session_id, entry.course_name])).entries(),
  );

  const handleRowClick = (examId: string, examStatus: ExamStatus) => {
    if (user?.role === "student") {
      if (examStatus === "open") navigate(`/exams/${examId}/room`);
      // Feature 2 (final-verification-pass addition): once an exam is
      // published, its per-question feedback (already saved by the
      // Teacher via Grading) becomes visible — see ExamFeedback page.
      else if (examStatus === "published") navigate(`/exams/${examId}/feedback`);
      return;
    }
    if (user?.role === "teacher") {
      if (examStatus === "draft" || examStatus === "scheduled") {
        navigate(`/teacher/exam-builder/${examId}`);
      } else {
        navigate(`/teacher/grading/${examId}`);
      }
    }
  };

  if (isLoading || !data) {
    return <PageLoader label="Loading exams..." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Exams</h1>
        {user?.role === "teacher" && (
          <Button icon={<Plus className="h-4 w-4" aria-hidden="true" />} onClick={() => navigate("/teacher/exam-builder")}>
            New Exam
          </Button>
        )}
      </div>

      <div className="flex items-center gap-4 text-sm">
        <select value={classSessionId} onChange={(e) => setClassSessionId(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">All Classes</option>
          {uniqueClassSessions.map(([id, name]) => (
            <option key={id} value={id}>
              {name}
            </option>
          ))}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {data.items.length === 0 ? (
        <EmptyState icon={FileQuestion} title="No exams found" description="Try a different class or status filter." />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2.5">Title</th>
                <th className="px-4 py-2.5">Class</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((exam) => (
                <tr
                  key={exam.id}
                  onClick={() => handleRowClick(exam.id, exam.status)}
                  className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-2.5">{exam.title}</td>
                  <td className="px-4 py-2.5">{exam.course_name}</td>
                  <td className="px-4 py-2.5">
                    <Badge tone={examStatusTone[exam.status]}>{exam.status}</Badge>
                  </td>
                  <td className="px-4 py-2.5">{exam.scheduled_at ? new Date(exam.scheduled_at).toLocaleString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
