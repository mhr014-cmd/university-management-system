// Shared loading-skeleton primitive (enterprise-polish pass). Replaces bare
// "Loading..." text in a handful of dashboard stat slots with a pulsing
// placeholder block — purely presentational, no behavior change.

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-md bg-slate-200 dark:bg-slate-700 ${className ?? "h-4 w-full"}`}
    />
  );
}
