// Results View page (FR-033, FR-036). Layout matches docs/UI_Wireframes.md
// Section 6: semester selector, GPA summary line, a per-course results
// table, and a Download Transcript button.
//
// Known simplification: this milestone builds the Student-facing view
// only, matching Implementation_Roadmap.md's Milestone 7 frontend page
// list ("Results view (Student)"). The wireframe's Role Visibility note
// says Parent access reuses this same layout with a child selector — but
// no endpoint exists anywhere to list a Parent's linked children (only
// ownership *verification* via parent_student_link, not enumeration), so
// a child selector cannot be populated yet. Left as a known gap for
// whichever future milestone builds the full Parent Portal (Page 17,
// Parent: Child View), which will need the same "list my children"
// capability for attendance/fees/schedule too, not just results. See
// PROJECT_PROGRESS.md's Milestone 7 entry.

import { useState } from "react";
import { useMyResults, useDownloadTranscript } from "../../features/results";

export default function ResultsViewPage() {
  const [semesterId, setSemesterId] = useState("");
  const { data, isLoading } = useMyResults({ semesterId: semesterId || undefined });
  const downloadTranscript = useDownloadTranscript();

  if (isLoading || !data) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading results...</p>;
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
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Results</h1>
        <select
          value={semesterId}
          onChange={(e) => setSemesterId(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
        >
          <option value="">Most recent</option>
          {semesters.map((s) => (
            <option key={s.semester_id} value={s.semester_id}>
              {s.semester_name}
            </option>
          ))}
        </select>
      </div>

      {!hasAnyPublishedResults ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No published results yet.</p>
      ) : selected ? (
        <>
          <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            GPA this semester: {selected.gpa.toFixed(2)}
          </p>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="py-2">Course</th>
                <th className="py-2">Grade</th>
                <th className="py-2">GPA Points</th>
              </tr>
            </thead>
            <tbody>
              {selected.courses.map((course) => (
                <tr key={course.course_id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2">{course.course_name}</td>
                  <td className="py-2">{course.grade_letter}</td>
                  <td className="py-2">{course.grade_point.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : null}

      <div className="flex justify-center pt-2">
        <button
          type="button"
          onClick={handleDownload}
          disabled={!hasAnyPublishedResults || downloadTranscript.isPending}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          {downloadTranscript.isPending ? "Preparing..." : "Download Transcript (PDF)"}
        </button>
      </div>
    </div>
  );
}
