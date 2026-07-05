// Admin: User Management page (FR-009-FR-016). Layout matches
// docs/UI_Wireframes.md Section 10: Students/Teachers tab toggle, table
// with inline actions, "+ New" opening an in-page create form (no
// separate route, per the wireframe's Navigation note).

import { useState, type FormEvent } from "react";
import { isAxiosError } from "axios";
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

type Tab = "students" | "teachers";

export default function UserManagementPage() {
  const [tab, setTab] = useState<Tab>("students");
  const [departmentFilter, setDepartmentFilter] = useState<string>("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editing, setEditing] = useState<StudentOrTeacher | null>(null);

  const { data: departments } = useDepartments();
  const studentsQuery = useStudents(departmentFilter || undefined);
  const teachersQuery = useTeachers(departmentFilter || undefined);
  const activeQuery = tab === "students" ? studentsQuery : teachersQuery;

  const deactivateStudent = useDeactivateStudent();
  const updateStudent = useUpdateStudent();
  const updateTeacher = useUpdateTeacher();

  const handleToggleActive = async (row: StudentOrTeacher) => {
    if (tab === "students") {
      if (row.is_active) {
        await deactivateStudent.mutateAsync(row.id);
      } else {
        await updateStudent.mutateAsync({ id: row.id, payload: { is_active: true } });
      }
    } else {
      await updateTeacher.mutateAsync({ id: row.id, payload: { is_active: !row.is_active } });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">User Management</h1>
        <button
          type="button"
          onClick={() => setShowCreateForm(true)}
          className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
        >
          + New
        </button>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setTab("students")}
            className={`rounded px-3 py-1 text-sm ${tab === "students" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "border border-slate-300 dark:border-slate-600"}`}
          >
            Students
          </button>
          <button
            type="button"
            onClick={() => setTab("teachers")}
            className={`rounded px-3 py-1 text-sm ${tab === "teachers" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "border border-slate-300 dark:border-slate-600"}`}
          >
            Teachers
          </button>
        </div>

        <select
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
        >
          <option value="">All Departments</option>
          {departments?.items.map((department) => (
            <option key={department.id} value={department.id}>
              {department.name}
            </option>
          ))}
        </select>
      </div>

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="py-2">Name</th>
            <th className="py-2">Email</th>
            <th className="py-2">Status</th>
            <th className="py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {activeQuery.data?.items.map((row) => (
            <tr
              key={row.id}
              className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
            >
              <td className="py-2">{row.first_name} {row.last_name}</td>
              <td className="py-2">{row.email}</td>
              <td className="py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    row.is_active
                      ? "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300"
                      : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                  }`}
                >
                  {row.is_active ? "Active" : "Inactive"}
                </span>
              </td>
              <td className="py-2 space-x-2">
                <button
                  type="button"
                  onClick={() => setEditing(row)}
                  className="rounded border border-slate-300 px-2 py-1 text-xs dark:border-slate-600"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm(`Are you sure you want to ${row.is_active ? "deactivate" : "reactivate"} this account? Historical records will be preserved.`)) {
                      void handleToggleActive(row);
                    }
                  }}
                  className="rounded border border-slate-300 px-2 py-1 text-xs dark:border-slate-600"
                >
                  {row.is_active ? "Deactivate" : "Reactivate"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {activeQuery.data && activeQuery.data.items.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">No {tab} found for this filter.</p>
      )}

      {showCreateForm && (
        <CreateAccountModal tab={tab} onClose={() => setShowCreateForm(false)} />
      )}
      {editing && (
        <EditAccountModal tab={tab} row={editing} onClose={() => setEditing(null)} />
      )}
    </div>
  );
}

function CreateAccountModal({ tab, onClose }: { tab: Tab; onClose: () => void }) {
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
    <div className="fixed inset-0 flex items-center justify-center bg-black/40">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-3 rounded bg-white p-6 dark:bg-slate-900">
        <h2 className="text-sm font-semibold">New {tab === "students" ? "Student" : "Teacher"}</h2>
        {error && (
          <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        )}
        <input required type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input required type="password" placeholder="Initial Password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input required placeholder="First Name" value={firstName} onChange={(e) => setFirstName(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input required placeholder="Last Name" value={lastName} onChange={(e) => setLastName(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <select required value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800">
          <option value="">Select Department</option>
          {departments?.items.map((department) => (
            <option key={department.id} value={department.id}>{department.name}</option>
          ))}
        </select>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600">Cancel</button>
          <button type="submit" disabled={isPending} className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900">
            {isPending ? "Creating..." : "Create"}
          </button>
        </div>
      </form>
    </div>
  );
}

function EditAccountModal({ tab, row, onClose }: { tab: Tab; row: StudentOrTeacher; onClose: () => void }) {
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
      onClose();
    } catch {
      setError("Could not save changes. Please try again.");
    }
  };

  const isPending = tab === "students" ? updateStudent.isPending : updateTeacher.isPending;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/40">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-3 rounded bg-white p-6 dark:bg-slate-900">
        <h2 className="text-sm font-semibold">Edit {tab === "students" ? "Student" : "Teacher"}</h2>
        {error && (
          <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        )}
        <input required placeholder="First Name" value={firstName} onChange={(e) => setFirstName(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <input required placeholder="Last Name" value={lastName} onChange={(e) => setLastName(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
        <select required value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800">
          {departments?.items.map((department) => (
            <option key={department.id} value={department.id}>{department.name}</option>
          ))}
        </select>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600">Cancel</button>
          <button type="submit" disabled={isPending} className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900">
            {isPending ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
