// Admin: User Management page (FR-009-FR-016). Layout matches
// docs/UI_Wireframes.md Section 10: Students/Teachers tab toggle, table
// with inline actions, "+ New" opening an in-page create form (no
// separate route, per the wireframe's Navigation note).

import { useState, type FormEvent } from "react";
import { isAxiosError } from "axios";
import { AlertCircle, Plus, Users } from "lucide-react";
import { useDepartments } from "../../../features/departments";
import {
  useCreateStudent,
  useCreateTeacher,
  useDeactivateStudent,
  useStudents,
  useTeachers,
  useUpdateStudent,
  useUpdateTeacher,
  type StudentOrTeacher,
} from "../../../features/users";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { ConfirmDialog } from "../../../components/ui/ConfirmDialog";
import { EmptyState } from "../../../components/ui/EmptyState";
import { Pagination } from "../../../components/ui/Pagination";
import { PasswordInput } from "../../../components/ui/PasswordInput";
import { useToast } from "../../../components/ui/Toast";
import { errorTextClass, inputClass, labelClass } from "../../../components/ui/classNames";

const PAGE_SIZE = 20;

type Tab = "students" | "teachers";

export default function UserManagementPage() {
  const { showSuccess, showError } = useToast();
  const [tab, setTab] = useState<Tab>("students");
  const [departmentFilter, setDepartmentFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editing, setEditing] = useState<StudentOrTeacher | null>(null);
  const [togglingRow, setTogglingRow] = useState<StudentOrTeacher | null>(null);

  const { data: departments } = useDepartments();
  const studentsQuery = useStudents(departmentFilter || undefined, page, PAGE_SIZE);
  const teachersQuery = useTeachers(departmentFilter || undefined, page, PAGE_SIZE);
  const activeQuery = tab === "students" ? studentsQuery : teachersQuery;

  const deactivateStudent = useDeactivateStudent();
  const updateStudent = useUpdateStudent();
  const updateTeacher = useUpdateTeacher();

  const switchTab = (next: Tab) => {
    setTab(next);
    setPage(1);
  };

  const handleToggleActive = async (row: StudentOrTeacher) => {
    try {
      if (tab === "students") {
        if (row.is_active) {
          await deactivateStudent.mutateAsync(row.id);
        } else {
          await updateStudent.mutateAsync({ id: row.id, payload: { is_active: true } });
        }
      } else {
        await updateTeacher.mutateAsync({ id: row.id, payload: { is_active: !row.is_active } });
      }
      showSuccess(`Account ${row.is_active ? "deactivated" : "reactivated"}.`);
    } catch {
      showError("Could not update this account's status. Please try again.");
    } finally {
      setTogglingRow(null);
    }
  };

  const isToggling = deactivateStudent.isPending || updateStudent.isPending || updateTeacher.isPending;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">User Management</h1>
        <Button icon={<Plus className="h-4 w-4" aria-hidden="true" />} onClick={() => setShowCreateForm(true)}>
          New
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <div className="flex gap-1 rounded-md border border-slate-200 p-1 dark:border-slate-700">
          <button
            type="button"
            onClick={() => switchTab("students")}
            className={`rounded px-3 py-1 text-sm font-medium transition-colors ${tab === "students" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"}`}
          >
            Students
          </button>
          <button
            type="button"
            onClick={() => switchTab("teachers")}
            className={`rounded px-3 py-1 text-sm font-medium transition-colors ${tab === "teachers" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"}`}
          >
            Teachers
          </button>
        </div>

        <select
          value={departmentFilter}
          onChange={(e) => {
            setDepartmentFilter(e.target.value);
            setPage(1);
          }}
          className={`w-auto ${inputClass}`}
        >
          <option value="">All Departments</option>
          {departments?.items.map((department) => (
            <option key={department.id} value={department.id}>
              {department.name}
            </option>
          ))}
        </select>
      </div>

      {activeQuery.data && activeQuery.data.items.length === 0 ? (
        <EmptyState icon={Users} title={`No ${tab} found`} description="Try a different department filter, or create a new account." />
      ) : (
        <>
          <Card className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-4 py-2.5">Name</th>
                  <th className="px-4 py-2.5">Email</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Actions</th>
                </tr>
              </thead>
              <tbody>
                {activeQuery.data?.items.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                  >
                    <td className="px-4 py-2.5">{row.first_name} {row.last_name}</td>
                    <td className="px-4 py-2.5">{row.email}</td>
                    <td className="px-4 py-2.5">
                      <Badge tone={row.is_active ? "green" : "neutral"}>{row.is_active ? "Active" : "Inactive"}</Badge>
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex gap-2">
                        <Button variant="secondary" size="sm" onClick={() => setEditing(row)}>
                          Edit
                        </Button>
                        <Button variant="secondary" size="sm" onClick={() => setTogglingRow(row)}>
                          {row.is_active ? "Deactivate" : "Reactivate"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          {activeQuery.data && (
            <Pagination page={page} pageSize={PAGE_SIZE} total={activeQuery.data.total} onPageChange={setPage} />
          )}
        </>
      )}

      {showCreateForm && (
        <CreateAccountModal tab={tab} onClose={() => setShowCreateForm(false)} onCreated={() => showSuccess(`${tab === "students" ? "Student" : "Teacher"} account created.`)} />
      )}
      {editing && (
        <EditAccountModal tab={tab} row={editing} onClose={() => setEditing(null)} onSaved={() => showSuccess("Changes saved.")} />
      )}
      {togglingRow && (
        <ConfirmDialog
          isOpen
          title={togglingRow.is_active ? "Deactivate account?" : "Reactivate account?"}
          description={`Are you sure you want to ${togglingRow.is_active ? "deactivate" : "reactivate"} this account? Historical records will be preserved.`}
          confirmLabel={togglingRow.is_active ? "Deactivate" : "Reactivate"}
          tone={togglingRow.is_active ? "danger" : "default"}
          isLoading={isToggling}
          onConfirm={() => void handleToggleActive(togglingRow)}
          onCancel={() => setTogglingRow(null)}
        />
      )}
    </div>
  );
}

function CreateAccountModal({ tab, onClose, onCreated }: { tab: Tab; onClose: () => void; onCreated: () => void }) {
  const { data: departments } = useDepartments();
  const createStudent = useCreateStudent();
  const createTeacher = useCreateTeacher();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      if (tab === "students") {
        await createStudent.mutateAsync({
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          department_id: departmentId,
          enrollment_date: new Date().toISOString().slice(0, 10),
        });
      } else {
        await createTeacher.mutateAsync({
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          department_id: departmentId,
        });
      }
      onCreated();
      onClose();
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setError("A user with this email already exists.");
      } else if (isAxiosError(err) && err.response?.status === 422) {
        setError("Please check the department and other fields.");
      } else {
        setError("Could not create account. Please try again.");
      }
    }
  };

  const isPending = tab === "students" ? createStudent.isPending : createTeacher.isPending;

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-900"
      >
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          New {tab === "students" ? "Student" : "Teacher"}
        </h2>
        {error && (
          <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}
        <div>
          <label htmlFor="new-email" className={labelClass}>
            Email <span className="text-red-500">*</span>
          </label>
          <input
            id="new-email"
            required
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <label htmlFor="new-password" className={labelClass}>
            Initial Password <span className="text-red-500">*</span>
          </label>
          <PasswordInput id="new-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" />
        </div>
        <div>
          <label htmlFor="new-first-name" className={labelClass}>
            First Name <span className="text-red-500">*</span>
          </label>
          <input id="new-first-name" required value={firstName} onChange={(e) => setFirstName(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="new-last-name" className={labelClass}>
            Last Name <span className="text-red-500">*</span>
          </label>
          <input id="new-last-name" required value={lastName} onChange={(e) => setLastName(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="new-department" className={labelClass}>
            Department <span className="text-red-500">*</span>
          </label>
          <select id="new-department" required value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className={inputClass}>
            <option value="">Select Department</option>
            {departments?.items.map((department) => (
              <option key={department.id} value={department.id}>{department.name}</option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" isLoading={isPending}>Create</Button>
        </div>
      </form>
    </div>
  );
}

function EditAccountModal({
  tab,
  row,
  onClose,
  onSaved,
}: {
  tab: Tab;
  row: StudentOrTeacher;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { data: departments } = useDepartments();
  const updateStudent = useUpdateStudent();
  const updateTeacher = useUpdateTeacher();

  const [firstName, setFirstName] = useState(row.first_name);
  const [lastName, setLastName] = useState(row.last_name);
  const [departmentId, setDepartmentId] = useState(row.department_id);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const payload = { first_name: firstName, last_name: lastName, department_id: departmentId };
    try {
      if (tab === "students") {
        await updateStudent.mutateAsync({ id: row.id, payload });
      } else {
        await updateTeacher.mutateAsync({ id: row.id, payload });
      }
      onSaved();
      onClose();
    } catch {
      setError("Could not save changes. Please try again.");
    }
  };

  const isPending = tab === "students" ? updateStudent.isPending : updateTeacher.isPending;

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-900"
      >
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          Edit {tab === "students" ? "Student" : "Teacher"}
        </h2>
        {error && (
          <div role="alert" className={errorTextClass}>
            {error}
          </div>
        )}
        <div>
          <label htmlFor="edit-first-name" className={labelClass}>
            First Name <span className="text-red-500">*</span>
          </label>
          <input id="edit-first-name" required value={firstName} onChange={(e) => setFirstName(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="edit-last-name" className={labelClass}>
            Last Name <span className="text-red-500">*</span>
          </label>
          <input id="edit-last-name" required value={lastName} onChange={(e) => setLastName(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="edit-department" className={labelClass}>
            Department <span className="text-red-500">*</span>
          </label>
          <select id="edit-department" required value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className={inputClass}>
            {departments?.items.map((department) => (
              <option key={department.id} value={department.id}>{department.name}</option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" isLoading={isPending}>Save</Button>
        </div>
      </form>
    </div>
  );
}
