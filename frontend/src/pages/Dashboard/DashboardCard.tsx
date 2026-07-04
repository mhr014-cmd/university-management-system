// Shared widget-card shell for all role Dashboard variants (Milestone 10).
// Matches docs/UI_Wireframes.md Section 2's widget-card visual pattern —
// factored out once four role variants needed the identical card chrome.

import type { ReactNode } from "react";

export function DashboardCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
      <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">{title}</p>
      {children}
    </div>
  );
}

export function NotAvailableCard({ title }: { title: string }) {
  return (
    <DashboardCard title={title}>
      <p className="text-sm text-slate-400 dark:text-slate-500">Not available</p>
    </DashboardCard>
  );
}
