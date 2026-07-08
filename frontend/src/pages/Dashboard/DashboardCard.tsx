// Shared widget-card shell for all role Dashboard variants (Milestone 10).
// Matches docs/UI_Wireframes.md Section 2's widget-card visual pattern —
// factored out once four role variants needed the identical card chrome.
//
// Production-polish pass: adopts the shared Card primitive (shadow/hover)
// and an optional leading icon — visual only, no change to what data each
// dashboard variant passes in.
//
// Enterprise-polish pass: an optional `to` makes the entire card a single
// clickable/keyboard-focusable navigation target (previously only a small
// "View all"-style text link inside the card was clickable). A trailing
// chevron appears as a visual affordance whenever `to` is set.

import type { LucideIcon } from "lucide-react";
import { ChevronRight, CircleSlash } from "lucide-react";
import type { ReactNode } from "react";
import { Card } from "../../components/ui/Card";

export function DashboardCard({
  title,
  icon: Icon,
  to,
  children,
}: {
  title: string;
  icon?: LucideIcon;
  to?: string;
  children: ReactNode;
}) {
  return (
    <Card hoverable={!to} to={to} aria-label={to ? title : undefined}>
      <div className="mb-2 flex items-center gap-2">
        {Icon && <Icon className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />}
        <p className="text-sm text-slate-500 dark:text-slate-400">{title}</p>
        {to && (
          <ChevronRight
            className="ml-auto h-4 w-4 shrink-0 text-slate-300 transition-transform group-hover:translate-x-0.5 dark:text-slate-600"
            aria-hidden="true"
          />
        )}
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
