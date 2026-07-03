// Dashboard page — presentational shell only.
// Role-specific summary widgets land starting Milestone 10 (see
// docs/Implementation_Roadmap.md). This milestone only verifies the routed
// shell renders and can reach the backend (health check).

import { useHealthCheck } from "../../lib/useHealthCheck";

export default function DashboardPage() {
  const { data, isLoading, isError } = useHealthCheck();

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold">Dashboard</h1>
      <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">
        Role-specific widgets are implemented starting Milestone 10.
      </p>

      <div className="rounded border border-slate-200 p-4 text-sm dark:border-slate-700">
        <h2 className="mb-2 font-medium">Backend connectivity</h2>
        {isLoading && <p>Checking...</p>}
        {isError && <p className="text-red-600 dark:text-red-400">Cannot reach backend API.</p>}
        {data && (
          <ul className="space-y-1">
            <li>Status: {data.status}</li>
            <li>Environment: {data.environment}</li>
            <li>Database: {data.database}</li>
          </ul>
        )}
      </div>
    </div>
  );
}
