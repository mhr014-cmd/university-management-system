// Shared Card primitive (production-polish pass). Replaces the plain
// `border p-4` boxes used ad hoc across pages with a consistent
// shadow/radius/hover treatment. Purely presentational.

import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hoverable?: boolean;
}

export function Card({ children, hoverable, className, ...props }: CardProps) {
  return (
    <div
      className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800/50 ${
        hoverable ? "transition-shadow duration-150 hover:shadow-md" : ""
      } ${className ?? ""}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={`mb-3 flex items-center justify-between ${className ?? ""}`}>{children}</div>;
}

export function CardTitle({ children }: { children: ReactNode }) {
  return <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{children}</h2>;
}
