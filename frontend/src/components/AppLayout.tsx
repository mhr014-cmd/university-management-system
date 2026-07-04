// Global app layout — shared header/nav shell used by all authenticated
// pages (per docs/UI_Wireframes.md "Cross-Page Conventions": top nav bar
// present on all pages except Login). The notification bell and full
// role-composed nav (beyond the single Dashboard link) are added starting
// Milestone 9/10 once those domains exist — this milestone adds the
// logged-in user's email and a logout action.

import { useNavigate } from "react-router-dom";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../app/ThemeProvider";

export function AppLayout() {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
        <Link to="/dashboard" className="text-lg font-semibold">
          ICT Education
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/profile">Profile</Link>
          <Link to="/timetable">Timetable</Link>
          {/* Role-scoped nav links, per docs/UI_Wireframes.md Sections 7,
              10, 15 Role Visibility notes — server-side RBAC is the
              actual enforcement; this is UX only, per CLAUDE.md
              Section 7. */}
          {user?.role === "admin" && <Link to="/admin/users">User Management</Link>}
          {(user?.role === "student" || user?.role === "parent") && (
            <Link to="/attendance">Attendance</Link>
          )}
          {user?.role === "teacher" && <Link to="/teacher/attendance-marker">Mark Attendance</Link>}
          {(user?.role === "student" || user?.role === "teacher" || user?.role === "admin") && (
            <Link to="/exams">Exams</Link>
          )}
          {user?.role === "student" && <Link to="/results">Results</Link>}
          {user?.role === "admin" && <Link to="/admin/result-approval">Result Approval</Link>}
          {user?.role === "student" && <Link to="/fees">Fee Centre</Link>}
          {user?.role === "admin" && <Link to="/admin/fee-dashboard">Fee Dashboard</Link>}
          {user && <span className="text-slate-500 dark:text-slate-400">{user.email}</span>}
          <button
            type="button"
            onClick={toggleTheme}
            className="rounded border border-slate-300 px-2 py-1 text-xs dark:border-slate-600"
            aria-label="Toggle theme"
          >
            {theme === "light" ? "Dark mode" : "Light mode"}
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded border border-slate-300 px-2 py-1 text-xs dark:border-slate-600"
          >
            Log out
          </button>
        </nav>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  );
}
