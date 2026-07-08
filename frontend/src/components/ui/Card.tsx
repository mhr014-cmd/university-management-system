// Shared Card primitive (production-polish pass). Replaces the plain
// `border p-4` boxes used ad hoc across pages with a consistent
// shadow/radius/hover treatment. Purely presentational.
//
// Enterprise-polish pass: an optional `to` makes the whole card a single
// navigable target (react-router Link) instead of relying on a small text
// link buried in the card's content — existing callers that don't pass
// `to` are unaffected (still render a plain, non-interactive div).

import type { HTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hoverable?: boolean;
  to?: string;
}

const baseClass =
  "rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800/50";
const hoverClass =
  "transition-all duration-150 hover:-translate-y-0.5 hover:shadow-md focus-visible:-translate-y-0.5 focus-visible:shadow-md";

export function Card({ children, hoverable, to, className, ...props }: CardProps) {
  if (to) {
    return (
      <Link
        to={to}
        className={`block ${baseClass} ${hoverClass} ${className ?? ""}`}
        {...(props as unknown as Record<string, unknown>)}
      >
        {children}
      </Link>
    );
  }

  return (
    <div
      className={`${baseClass} ${hoverable ? hoverClass : ""} ${className ?? ""}`}
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
