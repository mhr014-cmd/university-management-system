// Shared widget-card shell for all role Dashboard variants (Milestone 10).
// Matches docs/UI_Wireframes.md Section 2's widget-card visual pattern —
// factored out once four role variants needed the identical card chrome.
//
// Production-polish pass: adopts the shared Card primitive (shadow/hover)
// and an optional leading icon — visual only, no change to what data each
// dashboard variant passes in.

import type { LucideIcon } from "lucide-react";
import { CircleSlash } from "lucide-react";
import type { ReactNode } from "react";
import { Card } from "../../components/ui/Card";

export function DashboardCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon?: LucideIcon;
  children: ReactNode;
}) {
  return (
    <Card hoverable>
      <div className="mb-2 flex items-center gap-2">
        {Icon && <Icon className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />}
        <p className="text-sm text-slate-500 dark:text-slate-400">{title}</p>
      </div>
      {children}
    </Card>
  );
}

export function NotAvailableCard({ title, icon }: { title: string; icon?: LucideIcon }) {
  return (
    <DashboardCard title={title} icon={icon}>
      <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500">
        <CircleSlash className="h-3.5 w-3.5" aria-hidden="true" />
        <p className="text-sm">Not available</p>
      </div>
    </DashboardCard>
  );
}
