// Shared status-badge primitive (production-polish pass). Consolidates the
// rounded-full colored-pill pattern already used ad hoc for invoice/exam/
// account status into one component with a fixed color palette.

import type { ReactNode } from "react";

export type BadgeTone = "neutral" | "green" | "amber" | "red" | "blue";

const toneClasses: Record<BadgeTone, string> = {
  neutral: "bg-slate-100 text-slate-600 ring-slate-600/10 dark:bg-slate-800 dark:text-slate-400 dark:ring-slate-300/10",
  green: "bg-green-100 text-green-700 ring-green-600/15 dark:bg-green-950 dark:text-green-300 dark:ring-green-300/15",
  amber: "bg-amber-100 text-amber-700 ring-amber-600/15 dark:bg-amber-950 dark:text-amber-300 dark:ring-amber-300/15",
  red: "bg-red-100 text-red-700 ring-red-600/15 dark:bg-red-950 dark:text-red-300 dark:ring-red-300/15",
  blue: "bg-blue-100 text-blue-700 ring-blue-600/15 dark:bg-blue-950 dark:text-blue-300 dark:ring-blue-300/15",
};

export function Badge({ tone = "neutral", className, children }: { tone?: BadgeTone; className?: string; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ring-1 ring-inset ${toneClasses[tone]} ${className ?? ""}`}
    >
      {children}
    </span>
  );
}
