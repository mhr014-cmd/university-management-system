// Global app layout — shared header/nav shell used by all authenticated
// pages (per docs/UI_Wireframes.md "Cross-Page Conventions": top nav bar
// present on all pages except Login). Role-composed nav links, the
// notification bell, and the avatar menu are added starting Milestone 2/3
// once auth and user profiles exist — this milestone only provides the
// static shell and basic navigation.

import { Link, Outlet } from "react-router-dom";
import { useTheme } from "../app/ThemeProvider";

export function AppLayout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
        <Link to="/dashboard" className="text-lg font-semibold">
          ICT Education
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/dashboard">Dashboard</Link>
          <button
            type="button"
            onClick={toggleTheme}
            className="rounded border border-slate-300 px-2 py-1 text-xs dark:border-slate-600"
            aria-label="Toggle theme"
          >
            {theme === "light" ? "Dark mode" : "Light mode"}
          </button>
        </nav>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  );
}
