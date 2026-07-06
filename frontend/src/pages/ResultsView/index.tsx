// Results View page (FR-033, FR-036). Layout matches docs/UI_Wireframes.md
// Section 6: semester selector, GPA summary line, a per-course results
// table, and a Download Transcript button.
//
// Production-readiness audit gap closure: a dedicated Parent-facing view
// was previously unbuilt (Parent only had a 5-row widget on
// ParentDashboard). This page now branches by role — same pattern already
// established by Timetable/index.tsx — reusing this exact layout/GET
// /results/me/GET /{studentId}/transcript (already Parent-accessible) with
// a linked-child selector, rather than forking a second page/route.
//
// CGPA (overall, across all semesters): GET /results/me only returns
// per-semester GPA, never a cross-semester aggregate, and the per-course
// entries it returns don't include credit_hours — so an accurate
// credit-weighted CGPA can't be computed client-side (only the backend,
// which already computes per-semester GPA the same way, has that data).
// Per the brief's own instruction, this renders a graceful "Not available"
// placeholder rather than a client-side approximation that could be
// materially wrong. The Student view below has the same limitation — this
// isn't a Parent-specific gap.
//
// Teacher Remarks: the `result` table has no remarks/comments column
// (Database_Design.md §6.21 — only grade_letter/grade_point). The only
// existing "teacher remarks" data anywhere is `question_grade.feedback`,
// per-question feedback tied to one specific exam submission — a
// different granularity than a per-course/semester Result row, and
// already surfaced separately in the exam-taking view (GET /exams/{id})
// once published. Folding it into this aggregated view would require new
// join/aggregation logic, not just exposing an existing field, so it's
// left out here per the brief's "if an existing model already supports
// it" condition not being met at this level.

import { useEffect, useMemo, useState } from "react";
import { Award, Download, Users } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { useMyResults, useDownloadTranscript } from "../../features/results";
import { useMyChildren } from "../../features/users";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";
import { inputClass } from "../../components/ui/classNames";

export default function ResultsViewPage() {
  const { user } = useAuth();
  if (user?.role === "parent") {
    return <ParentResultsView />;
  }
  return <StudentResultsView />;
}

function passFail(gradePoint: number): "Pass" | "Fail" {
  // Derived label, not a stored field — Requirement_Analysis.md's A-004
  // conventional 4.0-scale assumption treats a 0.0 grade point as failing.
  return gradePoint > 0 ? "Pass" : "Fail";
}

function ResultsPanel({
  studentId,
  semesterId,
  onSemesterChange,
  semesters,
}: {
  studentId: string;
  semesterId: string;
  onSemesterChange: (id: string) => void;
  semesters: { semester_id: string; semester_name: string; gpa: number; courses: { course_id: string; course_name: string; grade_letter: string; grade_point: number }[] }[];
}) {
  const downloadTranscript = useDownloadTranscript();
  const selected = semesterId ? semesters.find((s) => s.semester_id === semesterId) : semesters[0];
  const hasAnyPublishedResults = semesters.length > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <select value={semesterId} onChange={(e) => onSemesterChange(e.target.value)} className={`w-auto ${inputClass}`}>
          <option value="">Most recent</option>
          {semesters.map((s) => (
            <option key={s.semester_id} value={s.semester_id}>
              {s.semester_name}
            </option>
          ))}
        </select>
      </div>

      {!hasAnyPublishedResults ? (
        <EmptyState icon={Award} title="No published results yet" description="Results will appear here once a teacher submits and an admin publishes them." />
      ) : selected ? (
        <>
          <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1">
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              GPA this semester: {selected.gpa.toFixed(2)}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">Overall CGPA: Not available</p>
          </div>
          <Card className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-4 py-2.5">Course</th>
                  <th className="px-4 py-2.5">Grade</th>
                  <th className="px-4 py-2.5">GPA Points</th>
                  <th className="px-4 py-2.5">Pass/Fail</th>
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
                    <td className="px-4 py-2.5">{passFail(course.grade_point)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      ) : null}

      <div className="flex justify-center pt-2">
        <Button
          onClick={() => downloadTranscript.mutate(studentId)}
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

function StudentResultsView() {
  const [semesterId, setSemesterId] = useState("");
  const { data, isLoading } = useMyResults({ semesterId: semesterId || undefined });

  if (isLoading || !data) {
    return <PageLoader label="Loading results..." />;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Results</h1>
      <ResultsPanel
        studentId={data.student_id}
        semesterId={semesterId}
        onSemesterChange={setSemesterId}
        semesters={data.semesters}
      />
    </div>
  );
}

function ParentResultsView() {
  const { data: childrenData, isLoading: childrenLoading, isError: childrenError } = useMyChildren();
  const children = useMemo(() => childrenData?.children ?? [], [childrenData]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [semesterId, setSemesterId] = useState("");

  useEffect(() => {
    if (!selectedStudentId && children.length > 0) {
      setSelectedStudentId(children[0].id);
    }
  }, [children, selectedStudentId]);

  const { data, isLoading } = useMyResults({
    studentId: selectedStudentId || undefined,
    semesterId: semesterId || undefined,
  });

  const selectedChild = children.find((c) => c.id === selectedStudentId);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Results</h1>

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

      {selectedStudentId && selectedChild && (
        <>
          {/* Every table below belongs to this one selected child — the
              heading makes that unambiguous even after scrolling past the
              child-selector card above. */}
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Viewing results for: <span className="font-medium text-slate-900 dark:text-slate-100">{selectedChild.first_name} {selectedChild.last_name}</span>
          </p>
          {isLoading || !data ? (
            <PageLoader label="Loading results..." />
          ) : (
            <ResultsPanel
              studentId={data.student_id}
              semesterId={semesterId}
              onSemesterChange={setSemesterId}
              semesters={data.semesters}
            />
          )}
        </>
      )}
    </div>
  );
}
