// Admin: Academic Setup — Departments (Version 2.3). Closes the gap the
// pre-V2.3 architecture review identified: Department had a working
// backend CRUD (list/create since Milestone 1, update/delete added for
// this version) but no frontend management screen at all — only a
// read-only dropdown consumed by other pages.

import { useState, type FormEvent } from "react";
import { isAxiosError } from "axios";
import { AlertCircle, Building2, Plus } from "lucide-react";
import {
  useCreateDepartment,
  useDeleteDepartment,
  useDepartments,
  useUpdateDepartment,
  type Department,
} from "../../../features/departments";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { ConfirmDialog } from "../../../components/ui/ConfirmDialog";
import { EmptyState } from "../../../components/ui/EmptyState";
import { PageLoader } from "../../../components/ui/PageLoader";
import { useToast } from "../../../components/ui/Toast";
import { inputClass, labelClass } from "../../../components/ui/classNames";
import { AcademicSetupTabs } from "./AcademicSetupTabs";

export default function AcademicSetupDepartmentsPage() {
  const { showSuccess, showError } = useToast();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editing, setEditing] = useState<Department | null>(null);
  const [deleting, setDeleting] = useState<Department | null>(null);

  const { data, isLoading } = useDepartments();
  const deleteDepartment = useDeleteDepartment();

  const handleDelete = async () => {
    if (!deleting) return;
    try {
      await deleteDepartment.mutateAsync(deleting.id);
      showSuccess("Department deleted.");
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        showError("This department is still referenced by existing courses/students/teachers and cannot be deleted.");
      } else {
        showError("Could not delete this department. Please try again.");
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
          New Department
        </Button>
      </div>

      <AcademicSetupTabs />

      {isLoading || !data ? (
        <PageLoader />
      ) : data.items.length === 0 ? (
        <EmptyState icon={Building2} title="No departments yet" description="Create the first department to get started." />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2.5">Name</th>
                <th className="px-4 py-2.5">Code</th>
                <th className="px-4 py-2.5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((department) => (
                <tr
                  key={department.id}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-2.5">{department.name}</td>
                  <td className="px-4 py-2.5">{department.code}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex gap-2">
                      <Button variant="secondary" size="sm" onClick={() => setEditing(department)}>
                        Edit
                      </Button>
                      <Button variant="danger" size="sm" onClick={() => setDeleting(department)}>
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
        <DepartmentFormModal
          title="New Department"
          onClose={() => setShowCreateForm(false)}
          onSaved={() => showSuccess("Department created.")}
        />
      )}
      {editing && (
        <DepartmentFormModal
          title="Edit Department"
          department={editing}
          onClose={() => setEditing(null)}
          onSaved={() => showSuccess("Changes saved.")}
        />
      )}
      {deleting && (
        <ConfirmDialog
          isOpen
          title="Delete department?"
          description={`Are you sure you want to delete "${deleting.name}"? This cannot be undone.`}
          confirmLabel="Delete"
          tone="danger"
          isLoading={deleteDepartment.isPending}
          onConfirm={() => void handleDelete()}
          onCancel={() => setDeleting(null)}
        />
      )}
    </div>
  );
}

function DepartmentFormModal({
  title,
  department,
  onClose,
  onSaved,
}: {
  title: string;
  department?: Department;
  onClose: () => void;
  onSaved: () => void;
}) {
  const createDepartment = useCreateDepartment();
  const updateDepartment = useUpdateDepartment();

  const [name, setName] = useState(department?.name ?? "");
  const [code, setCode] = useState(department?.code ?? "");
  const [error, setError] = useState<string | null>(null);

  const isPending = createDepartment.isPending || updateDepartment.isPending;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      if (department) {
        await updateDepartment.mutateAsync({ id: department.id, payload: { name, code } });
      } else {
        await createDepartment.mutateAsync({ name, code });
      }
      onSaved();
      onClose();
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setError("A department with this name or code already exists.");
      } else {
        setError("Could not save this department. Please try again.");
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
          <label htmlFor="department-name" className={labelClass}>
            Name <span className="text-red-500">*</span>
          </label>
          <input id="department-name" required value={name} onChange={(e) => setName(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="department-code" className={labelClass}>
            Code <span className="text-red-500">*</span>
          </label>
          <input id="department-code" required value={code} onChange={(e) => setCode(e.target.value)} className={inputClass} />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" isLoading={isPending}>Save</Button>
        </div>
      </form>
    </div>
  );
}
