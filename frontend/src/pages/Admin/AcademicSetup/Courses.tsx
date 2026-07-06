// Admin: Academic Setup — Courses (Version 2.3). Closes the gap the
// pre-V2.3 architecture review identified: Course had a working backend
// CRUD (list/create since Milestone 1, update/delete added for this
// version) but zero frontend presence at all — not even read-only.

import { useState, type FormEvent } from "react";
import { isAxiosError } from "axios";
import { AlertCircle, BookOpen, Plus } from "lucide-react";
import { useDepartments } from "../../../features/departments";
import { useCourses, useCreateCourse, useDeleteCourse, useUpdateCourse, type Course } from "../../../features/courses";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { ConfirmDialog } from "../../../components/ui/ConfirmDialog";
import { EmptyState } from "../../../components/ui/EmptyState";
import { PageLoader } from "../../../components/ui/PageLoader";
import { SearchableSelect } from "../../../components/ui/SearchableSelect";
import { useToast } from "../../../components/ui/Toast";
import { inputClass, labelClass } from "../../../components/ui/classNames";
import { AcademicSetupTabs } from "./AcademicSetupTabs";

export default function AcademicSetupCoursesPage() {
  const { showSuccess, showError } = useToast();
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editing, setEditing] = useState<Course | null>(null);
  const [deleting, setDeleting] = useState<Course | null>(null);

  const { data: departments } = useDepartments();
  const { data, isLoading } = useCourses(departmentFilter || undefined);
  const deleteCourse = useDeleteCourse();

  const departmentName = (departmentId: string) =>
    departments?.items.find((d) => d.id === departmentId)?.name ?? "—";

  const handleDelete = async () => {
    if (!deleting) return;
    try {
      await deleteCourse.mutateAsync(deleting.id);
      showSuccess("Course deleted.");
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        showError("This course is still referenced by existing class sessions/enrollments and cannot be deleted.");
      } else {
        showError("Could not delete this course. Please try again.");
      }
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Academic Setup</h1>
        <Button icon={<Plus className="h-4 w-4" aria-hidden="true" />} onClick={() => setShowCreateForm(true)}>
          New Course
        </Button>
      </div>

      <AcademicSetupTabs />

      <select value={departmentFilter} onChange={(e) => setDepartmentFilter(e.target.value)} className={`w-auto ${inputClass}`}>
        <option value="">All Departments</option>
        {departments?.items.map((department) => (
          <option key={department.id} value={department.id}>{department.name}</option>
        ))}
      </select>

      {isLoading || !data ? (
        <PageLoader />
      ) : data.items.length === 0 ? (
        <EmptyState icon={BookOpen} title="No courses yet" description="Try a different department filter, or create a new course." />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2.5">Name</th>
                <th className="px-4 py-2.5">Code</th>
                <th className="px-4 py-2.5">Department</th>
                <th className="px-4 py-2.5">Credit Hours</th>
                <th className="px-4 py-2.5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((course) => (
                <tr
                  key={course.id}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-2.5">{course.name}</td>
                  <td className="px-4 py-2.5">{course.code}</td>
                  <td className="px-4 py-2.5">{departmentName(course.department_id)}</td>
                  <td className="px-4 py-2.5">{course.credit_hours}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex gap-2">
                      <Button variant="secondary" size="sm" onClick={() => setEditing(course)}>
                        Edit
                      </Button>
                      <Button variant="danger" size="sm" onClick={() => setDeleting(course)}>
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {showCreateForm && (
        <CourseFormModal title="New Course" onClose={() => setShowCreateForm(false)} onSaved={() => showSuccess("Course created.")} />
      )}
      {editing && (
        <CourseFormModal
          title="Edit Course"
          course={editing}
          onClose={() => setEditing(null)}
          onSaved={() => showSuccess("Changes saved.")}
        />
      )}
      {deleting && (
        <ConfirmDialog
          isOpen
          title="Delete course?"
          description={`Are you sure you want to delete "${deleting.name}"? This cannot be undone.`}
          confirmLabel="Delete"
          tone="danger"
          isLoading={deleteCourse.isPending}
          onConfirm={() => void handleDelete()}
          onCancel={() => setDeleting(null)}
        />
      )}
    </div>
  );
}

function CourseFormModal({
  title,
  course,
  onClose,
  onSaved,
}: {
  title: string;
  course?: Course;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { data: departments } = useDepartments();
  const createCourse = useCreateCourse();
  const updateCourse = useUpdateCourse();

  const [departmentId, setDepartmentId] = useState(course?.department_id ?? "");
  const [name, setName] = useState(course?.name ?? "");
  const [code, setCode] = useState(course?.code ?? "");
  const [creditHours, setCreditHours] = useState(course ? String(course.credit_hours) : "");
  const [error, setError] = useState<string | null>(null);

  const isPending = createCourse.isPending || updateCourse.isPending;

  const departmentOptions = (departments?.items ?? []).map((d) => ({ value: d.id, label: d.name }));

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const payload = { department_id: departmentId, name, code, credit_hours: Number(creditHours) };
    try {
      if (course) {
        await updateCourse.mutateAsync({ id: course.id, payload });
      } else {
        await createCourse.mutateAsync(payload);
      }
      onSaved();
      onClose();
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setError("A course with this code already exists.");
      } else if (isAxiosError(err) && err.response?.status === 422) {
        setError("Please check the department and other fields.");
      } else {
        setError("Could not save this course. Please try again.");
      }
    }
  };

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-900"
      >
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
        {error && (
          <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}
        <div>
          <label htmlFor="course-department" className={labelClass}>
            Department <span className="text-red-500">*</span>
          </label>
          <SearchableSelect
            id="course-department"
            options={departmentOptions}
            value={departmentId}
            onChange={setDepartmentId}
            placeholder="Select Department"
          />
        </div>
        <div>
          <label htmlFor="course-name" className={labelClass}>
            Name <span className="text-red-500">*</span>
          </label>
          <input id="course-name" required value={name} onChange={(e) => setName(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="course-code" className={labelClass}>
            Code <span className="text-red-500">*</span>
          </label>
          <input id="course-code" required value={code} onChange={(e) => setCode(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="course-credit-hours" className={labelClass}>
            Credit Hours <span className="text-red-500">*</span>
          </label>
          <input
            id="course-credit-hours"
            required
            type="number"
            min={1}
            value={creditHours}
            onChange={(e) => setCreditHours(e.target.value)}
            className={inputClass}
          />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" isLoading={isPending} disabled={!departmentId}>Save</Button>
        </div>
      </form>
    </div>
  );
}
