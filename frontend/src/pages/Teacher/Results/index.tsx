// Teacher: Results View page (final-verification-pass addition, Feature 1).
// Read-only. Lets a Teacher check the approval status (submitted/
// published/rejected) of the results they've submitted for their own
// exams — the one gap left after "create exam / grade exam / submit
// results": there was previously no way to see what happened *after*
// submission. Reuses the existing Result model/table and the existing
// GET /exams list (already scoped server-side to the caller's own exams
// for a Teacher — see exam_service.list_exams) — no new database table,
// no new column.

import { useState } from "react";
import { Award } from "lucide-react";
import { useExams } from "../../../features/exams";
import { useExamResultsForTeacher } from "../../../features/results";
import { Badge, type BadgeTone } from "../../../components/ui/Badge";
import { Card } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { PageLoader } from "../../../components/ui/PageLoader";
import { inputClass } from "../../../components/ui/classNames";

const statusTone: Record<string, BadgeTone> = {
  submitted: "amber",
  published: "green",
  rejected: "red",
};

export default function TeacherResultsPage() {
  const { data: exams, isLoading: examsLoading } = useExams({ pageSize: 100 });
  const [examId, setExamId] = useState("");

  const { data, isLoading: resultsLoading } = useExamResultsForTeacher(examId || undefined);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Results</h1>

      <Card>
        <div className="mb-2 flex items-center gap-2">
          <Award className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Select Exam</p>
        </div>
        {examsLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading your exams...</p>
        ) : (exams?.items ?? []).length === 0 ? (
          <EmptyState icon={Award} title="No exams yet" description="Exams you create will appear here." />
        ) : (
          <select value={examId} onChange={(e) => setExamId(e.target.value)} className={inputClass}>
            <option value="">Select an exam</option>
            {(exams?.items ?? []).map((exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.title} — {exam.course_name} ({exam.status})
              </option>
            ))}
          </select>
        )}
      </Card>

      {!examId ? null : resultsLoading || !data ? (
        <PageLoader label="Loading results..." />
      ) : data.results.length === 0 ? (
        <EmptyState
          icon={Award}
          title="No results submitted yet"
          description="Once you submit results for this exam, their approval status will appear here."
        />
      ) : (
        <Card className="overflow-x-auto p-0">
          <p className="px-4 pt-3 text-sm font-medium text-slate-700 dark:text-slate-300">
            {data.exam_title} — {data.course_name}
          </p>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2.5">Student</th>
                <th className="px-4 py-2.5">Grade</th>
                <th className="px-4 py-2.5">GPA Points</th>
                <th className="px-4 py-2.5">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((entry) => (
                <tr
                  key={entry.result_id}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-2.5">{entry.student_name}</td>
                  <td className="px-4 py-2.5">{entry.grade_letter ?? "—"}</td>
                  <td className="px-4 py-2.5">{entry.grade_point?.toFixed(1) ?? "—"}</td>
                  <td className="px-4 py-2.5">
                    <Badge tone={statusTone[entry.status] ?? "neutral"}>{entry.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
