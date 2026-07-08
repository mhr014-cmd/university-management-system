// Shared progress-bar primitive (enterprise-polish pass). Color-coded by
// value so a glance at the bar communicates status without reading the
// number — used first by Attendance (green/amber/red vs. the 80% BR-008
// threshold), reusable anywhere else a 0-100 percentage is shown.

interface ProgressBarProps {
  value: number;
  className?: string;
  trackClassName?: string;
  /** Optional explicit tier thresholds; defaults suit attendance-style metrics. */
  thresholds?: { amber: number; green: number };
}

export function progressBarTone(value: number, thresholds: { amber: number; green: number } = { amber: 60, green: 80 }) {
  if (value >= thresholds.green) return "green";
  if (value >= thresholds.amber) return "amber";
  return "red";
}

const barColorClass: Record<"green" | "amber" | "red", string> = {
  green: "bg-green-500 dark:bg-green-500",
  amber: "bg-amber-500 dark:bg-amber-500",
  red: "bg-red-500 dark:bg-red-500",
};

export function ProgressBar({ value, className, trackClassName, thresholds }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(value, 100));
  const tone = progressBarTone(clamped, thresholds);

  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      className={`h-2 w-40 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700 ${trackClassName ?? ""} ${className ?? ""}`}
    >
      <div
        className={`h-2 rounded-full transition-[width] duration-500 ease-out ${barColorClass[tone]}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
