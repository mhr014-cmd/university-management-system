// Pagination control (final UI polish pass). Wraps the Prev/Next +
// "Page X of Y" pattern already implicit in every PaginatedResponse
// (frontend/src/features/users/index.ts and friends) but never
// surfaced in the UI — list pages fetched page 1 and had no way to
// reach page 2+.

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./Button";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-1 text-sm text-slate-500 dark:text-slate-400">
      <span>
        Page {page} of {totalPages} &middot; {total} total
      </span>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          icon={<ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
          className="flex-row-reverse"
          icon={<ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
