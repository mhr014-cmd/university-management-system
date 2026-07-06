// Results View page (FR-033, FR-036). Layout matches docs/UI_Wireframes.md
// Section 6: semester selector, GPA summary line, a per-course results
// table, and a Download Transcript button.
//
// Known simplification: this milestone builds the Student-facing view
// only, matching Implementation_Roadmap.md's Milestone 7 frontend page
// list ("Results view (Student)"). The wireframe's Role Visibility note
// says Parent access reuses this same layout with a child selector; the
// production-polish audit added GET /users/me/children (Parent linked-
// children enumeration) and wired a child selector into
// ParentDashboard.tsx's Recent Results widget rather than into this page
// directly. A dedicated Parent-facing Results View reusing this exact
// layout remains unbuilt — out of scope for that audit pass. See
// PROJECT_PROGRESS.md's Milestone 7 entry.

import { useState } from "react";
import { Award, Download } from "lucide-react";
import { useMyResults, useDownloadTranscript } from "../../features/results";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";
import { inputClass } from "../../components/ui/classNames";

export default function ResultsViewPage() {
  const [semesterId, setSemesterId] = useState("");
  const { data, isLoading } = useMyResults({ semesterId: semesterId || undefined });
  const downloadTranscript = useDownloadTranscript();

  if (isLoading || !data) {
    return <PageLoader label="Loading results..." />;
  }

  const semesters = data.semesters;
  const selected = semesterId ? semesters.find((s) => s.semester_id === semesterId) : semesters[0];
  const hasAnyPublishedResults = semesters.length > 0;

  const handleDownload = () => {
    downloadTranscript.mutate(data.student_id);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Results</h1>
        <select value={semesterId} onChange={(e) => setSemesterId(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">Most recent</option>
          {semesters.map((s) => (
            <option key={s.semester_id} value={s.semester_id}>
              {s.semester_name}
            </option>
          ))}
        </select>
      </div>

      {!hasAnyPublishedResults ? (
        <EmptyState icon={Award} title="No published results yet" description="Results will appear here once your teacher submits and an admin publishes them." />
      ) : selected ? (
        <>
          <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            GPA this semester: {selected.gpa.toFixed(2)}
          </p>
          <Card className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-4 py-2.5">Course</th>
                  <th className="px-4 py-2.5">Grade</th>
                  <th className="px-4 py-2.5">GPA Points</th>
                </tr>
              </thead>
              <tbody>
                {selected.courses.map((course) => (
                  <tr
                    key={course.course_id}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                  >
                    <td className="px-4 py-2.5">{course.course_name}</td>
                    <td className="px-4 py-2.5">{course.grade_letter}</td>
                    <td className="px-4 py-2.5">{course.grade_point.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      ) : null}

      <div className="flex justify-center pt-2">
        <Button
          onClick={handleDownload}
          disabled={!hasAnyPublishedResults}
          isLoading={downloadTranscript.isPending}
          icon={<Download className="h-4 w-4" aria-hidden="true" />}
        >
          Download Transcript (PDF)
        </Button>
      </div>
    </div>
  );
}
