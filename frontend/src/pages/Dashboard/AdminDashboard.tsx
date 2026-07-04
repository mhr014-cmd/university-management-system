// Admin Dashboard widgets (Milestone 10) — docs/UI_Wireframes.md Section 2
// Role Visibility: Pending Result Approvals count, Overdue Fees count,
// Recent User Signups.
//
// Recent User Signups is backed by the additive `created_at` field added
// to GET /users/students and GET /users/teachers (approved Finding D) —
// no new endpoint or schema change was needed.

import { Link } from "react-router-dom";
import { usePendingResults } from "../../features/results";
import { useOverdueAccounts } from "../../features/fees";
import { useStudents, useTeachers } from "../../features/users";
import { DashboardCard } from "./DashboardCard";

export function AdminDashboard() {
  const { data: pendingResults } = usePendingResults();
  const { data: overdue } = useOverdueAccounts();
  const { data: students } = useStudents(undefined, 1, 20);
  const { data: teachers } = useTeachers(undefined, 1, 20);

  const pendingApprovalsCount = (pendingResults?.items ?? []).reduce(
    (sum, item) => sum + item.results.length,
    0,
  );

  const recentSignups = [
    ...(students?.items ?? []).map((s) => ({ ...s, role: "Student" as const })),
    ...(teachers?.items ?? []).map((t) => ({ ...t, role: "Teacher" as const })),
  ]
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, 5);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <DashboardCard title="Pending Result Approvals">
          <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{pendingApprovalsCount}</p>
          <Link
            to="/admin/result-approval"
            className="mt-2 inline-block text-sm text-slate-900 underline dark:text-slate-100"
          >
            Review
          </Link>
        </DashboardCard>

        <DashboardCard title="Overdue Fees">
          <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
            {overdue?.overdue_accounts.length ?? 0}
          </p>
          <Link
            to="/admin/fee-dashboard"
            className="mt-2 inline-block text-sm text-slate-900 underline dark:text-slate-100"
          >
            View Fee Dashboard
          </Link>
        </DashboardCard>

        <DashboardCard title="Reports">
          <Link
            to="/admin/reports"
            className="mt-2 inline-block text-sm text-slate-900 underline dark:text-slate-100"
          >
            Generate reports
          </Link>
        </DashboardCard>
      </div>

      <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
        <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">Recent User Signups</p>
        {recentSignups.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No users yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="py-2">Name</th>
                <th className="py-2">Role</th>
                <th className="py-2">Signed up</th>
              </tr>
            </thead>
            <tbody>
              {recentSignups.map((u) => (
                <tr key={u.id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2">
                    {u.first_name} {u.last_name}
                  </td>
                  <td className="py-2">{u.role}</td>
                  <td className="py-2">{new Date(u.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Link to="/admin/users" className="mt-2 inline-block text-sm text-slate-900 underline dark:text-slate-100">
          Manage users
        </Link>
      </div>
    </div>
  );
}
