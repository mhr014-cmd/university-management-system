// Login page — presentational shell only.
// No authentication logic in this milestone (login form submission, token
// handling, and role-based redirect land in Milestone 2 — FR-001, FR-005).
// Layout matches docs/UI_Wireframes.md Section 1.

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-white dark:bg-slate-900">
      <div className="w-full max-w-sm rounded border border-slate-200 p-8 dark:border-slate-700">
        <h1 className="mb-6 text-center text-xl font-semibold text-slate-900 dark:text-slate-100">
          Sign in
        </h1>
        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          Login form implemented in Milestone 2 (Authentication &amp; Authorization).
        </p>
      </div>
    </div>
  );
}
