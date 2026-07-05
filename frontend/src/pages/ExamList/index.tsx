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

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { useMySchedule } from "../../features/schedule";
import { useExams } from "../../features/exams";
import type { ExamStatus } from "../../features/exams";

const STATUS_OPTIONS: ExamStatus[] = ["draft", "scheduled", "open", "closed", "published"];

const examStatusStyles: Record<ExamStatus, string> = {
  draft: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  scheduled: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  open: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300",
  closed: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  published: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
};

export default function ExamListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [classSessionId, setClassSessionId] = useState("");
  const [status, setStatus] = useState("");

  const { data: schedule } = useMySchedule();
  const { data, isLoading } = useExams({
    classSessionId: classSessionId || undefined,
    status: status || undefined,
  });

  const uniqueClassSessions = Array.from(
    new Map((schedule?.entries ?? []).map((entry) => [entry.class_session_id, entry.course_name])).entries(),
  );

  const handleRowClick = (examId: string, examStatus: ExamStatus) => {
    if (user?.role === "student") {
      if (examStatus === "open") navigate(`/exams/${examId}/room`);
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
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading exams...</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Exams</h1>
        {user?.role === "teacher" && (
          <button
            type="button"
            onClick={() => navigate("/teacher/exam-builder")}
            className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
          >
            New Exam
          </button>
        )}
      </div>

      <div className="flex items-center gap-4 text-sm">
        <select
          value={classSessionId}
          onChange={(e) => setClassSessionId(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
        >
          <option value="">All Classes</option>
          {uniqueClassSessions.map(([id, name]) => (
            <option key={id} value={id}>
              {name}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600 dark:bg-slate-800"
        >
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="py-2">Title</th>
            <th className="py-2">Class</th>
            <th className="py-2">Status</th>
            <th className="py-2">Date</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((exam) => (
            <tr
              key={exam.id}
              onClick={() => handleRowClick(exam.id, exam.status)}
              className="cursor-pointer border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
            >
              <td className="py-2">{exam.title}</td>
              <td className="py-2">{exam.course_name}</td>
              <td className="py-2">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${examStatusStyles[exam.status]}`}>
                  {exam.status}
                </span>
              </td>
              <td className="py-2">{exam.scheduled_at ? new Date(exam.scheduled_at).toLocaleString() : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.items.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">No exams found.</p>
      )}
    </div>
  );
}
