// Page-level loading indicator (final UI polish pass). Replaces bare
// "Loading..." text — present on nearly every page's initial-fetch
// branch — with a small spinner so the loading state reads as active
// rather than a static, possibly-stuck label.

import { Loader2 } from "lucide-react";

export function PageLoader({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
