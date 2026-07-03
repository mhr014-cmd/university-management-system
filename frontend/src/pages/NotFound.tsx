// 404 fallback page — not one of the 18 pages in docs/Requirement_Analysis.md
// §7 (proposal doesn't specify one); a routing necessity, kept minimal.

import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <Link to="/dashboard" className="text-blue-600 underline dark:text-blue-400">
        Back to Dashboard
      </Link>
    </div>
  );
}
