// Shared empty-state primitive (production-polish pass). Replaces bare
// "No X yet." text with an icon + title + optional description, used
// consistently wherever a list/table has zero rows.

import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
}

export function EmptyState({ icon: Icon = Inbox, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-slate-200 px-4 py-10 text-center dark:border-slate-700">
      <Icon className="h-8 w-8 text-slate-300 dark:text-slate-600" aria-hidden="true" />
      <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{title}</p>
      {description && <p className="max-w-sm text-xs text-slate-400 dark:text-slate-500">{description}</p>}
    </div>
  );
}
