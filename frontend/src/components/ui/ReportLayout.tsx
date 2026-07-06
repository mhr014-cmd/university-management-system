// Shared report page layout (Version 1.2 reporting infrastructure).
// Renders a title/subtitle header (hidden when printing, since it
// duplicates into the print region below) plus a [data-print-region]
// content wrapper — the only part of the page visible when printing or
// exporting via the browser's own print dialog (see styles/print.css).

import type { ReactNode } from "react";

interface ReportLayoutProps {
  title: string;
  subtitle?: string;
  toolbar?: ReactNode;
  children: ReactNode;
}

export function ReportLayout({ title, subtitle, toolbar, children }: ReportLayoutProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between" data-print-hidden>
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
          {subtitle && <p className="text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
        </div>
        {toolbar}
      </div>
      <div data-print-region className="space-y-4">
        <div className="hidden print:block">
          <h2 className="text-lg font-semibold">{title}</h2>
          {subtitle && <p className="text-sm text-slate-600">{subtitle}</p>}
        </div>
        {children}
      </div>
    </div>
  );
}
