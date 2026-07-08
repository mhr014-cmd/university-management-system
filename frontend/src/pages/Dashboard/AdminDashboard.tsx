// Admin Dashboard widgets (Milestone 10) — docs/UI_Wireframes.md Section 2
// Role Visibility: Pending Result Approvals count, Overdue Fees count,
// Recent User Signups.
//
// Recent User Signups is backed by the additive `created_at` field added
// to GET /users/students and GET /users/teachers (approved Finding D) —
// no new endpoint or schema change was needed.

import { AlertTriangle, ClipboardCheck, FileBarChart, Users as UsersIcon } from "lucide-react";
import { usePendingResults } from "../../features/results";
import { useOverdueAccounts } from "../../features/fees";
import { useStudents, useTeachers } from "../../features/users";
import { RecentNotificationsCard } from "../../components/RecentNotificationsCard";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
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
        <DashboardCard title="Pending Result Approvals" icon={ClipboardCheck} to="/admin/result-approval">
          <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{pendingApprovalsCount}</p>
          <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">Review</span>
        </DashboardCard>

        <DashboardCard title="Overdue Fees" icon={AlertTriangle} to="/admin/fee-dashboard">
          <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
            {overdue?.overdue_accounts.length ?? 0}
          </p>
          <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">
            View Fee Dashboard
          </span>
        </DashboardCard>

        <DashboardCard title="Reports" icon={FileBarChart} to="/admin/reports">
          <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">
            Generate reports
          </span>
        </DashboardCard>
      </div>

      <Card to="/admin/users" hoverable>
        <div className="mb-2 flex items-center gap-2">
          <UsersIcon className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Recent User Signups</p>
        </div>
        {recentSignups.length === 0 ? (
          <EmptyState icon={UsersIcon} title="No users yet" description="New student and teacher signups will appear here." />
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
                <tr
                  key={u.id}
                  className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
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
        <span className="mt-2 inline-block text-sm font-medium text-slate-600 dark:text-slate-400">Manage users</span>
      </Card>

      <RecentNotificationsCard />
    </div>
  );
}
