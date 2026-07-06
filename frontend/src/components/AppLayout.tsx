// Global app layout — shared header/nav shell used by all authenticated
// pages (per docs/UI_Wireframes.md "Cross-Page Conventions": top nav bar
// present on all pages except Login).
//
// Known simplification (Milestone 9): the notification bell links
// directly to the full Notifications page with an unread-count badge,
// rather than also offering the wireframe's optional desktop dropdown
// panel — same class of documented simplification as Milestone 5's
// Attendance Calendar view. See PROJECT_PROGRESS.md's Milestone 9 entry.
//
// Production-polish pass: visual redesign only (icons, active-link
// styling, sticky header, collapsible mobile nav) — every route,
// role-scoped link condition, and RBAC-hiding note below is unchanged.
// The nav link list is built once (navItems) and rendered twice — inline
// on desktop, in a dropdown panel on mobile — rather than duplicated, so
// the two can never drift out of sync.

import { useState } from "react";
import { Bell, GraduationCap, LogOut, Menu, Moon, Sun, X } from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../app/ThemeProvider";
import { useNotifications } from "../features/notifications";

interface NavItem {
  to: string;
  label: string;
}

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
    isActive
      ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white"
      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-100"
  }`;
}

function mobileNavLinkClass({ isActive }: { isActive: boolean }): string {
  return `block rounded-md px-3 py-2 text-sm font-medium ${
    isActive
      ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white"
      : "text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800/60"
  }`;
}

export function AppLayout() {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { data: notifications } = useNotifications({ isRead: false, pageSize: 1 });
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  // Role-scoped nav links, per docs/UI_Wireframes.md Sections 7, 10, 15
  // Role Visibility notes — server-side RBAC is the actual enforcement;
  // this list is UX only, per CLAUDE.md Section 7.
  const navItems: NavItem[] = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/profile", label: "Profile" },
    { to: "/timetable", label: "Timetable" },
    ...(user?.role === "admin" ? [{ to: "/admin/users", label: "User Management" }] : []),
    ...(user?.role === "student" || user?.role === "parent" ? [{ to: "/attendance", label: "Attendance" }] : []),
    ...(user?.role === "teacher" ? [{ to: "/teacher/attendance-marker", label: "Mark Attendance" }] : []),
    ...(user?.role === "student" || user?.role === "teacher" || user?.role === "admin"
      ? [{ to: "/exams", label: "Exams" }]
      : []),
    ...(user?.role === "student" || user?.role === "parent" ? [{ to: "/results", label: "Results" }] : []),
    ...(user?.role === "admin" ? [{ to: "/admin/result-approval", label: "Result Approval" }] : []),
    ...(user?.role === "student" || user?.role === "parent" ? [{ to: "/fees", label: "Fee Centre" }] : []),
    ...(user?.role === "admin" ? [{ to: "/admin/fee-dashboard", label: "Fee Dashboard" }] : []),
    ...(user?.role === "admin" ? [{ to: "/admin/reports", label: "Reports" }] : []),
    ...(user?.role === "admin"
      ? [{ to: "/admin/academic-setup/departments", label: "Academic Setup" }]
      : []),
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90">
        <div className="flex items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link to="/dashboard" className="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
            <GraduationCap className="h-5 w-5" aria-hidden="true" />
            ICT Education
          </Link>

          <nav className="hidden flex-1 flex-wrap items-center gap-1 text-sm lg:flex">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={navLinkClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-1 sm:gap-2">
            <NavLink
              to="/notifications"
              aria-label="Notifications"
              className="relative rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            >
              <Bell className="h-4 w-4" aria-hidden="true" />
              {(notifications?.unread_count ?? 0) > 0 && (
                <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold leading-none text-white">
                  {notifications!.unread_count}
                </span>
              )}
            </NavLink>
            {user && (
              <span className="hidden text-sm text-slate-500 dark:text-slate-400 xl:inline">{user.email}</span>
            )}
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
              aria-label="Toggle theme"
              title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
            >
              {theme === "light" ? <Moon className="h-4 w-4" aria-hidden="true" /> : <Sun className="h-4 w-4" aria-hidden="true" />}
            </button>
            <button
              type="button"
              onClick={handleLogout}
              aria-label="Log out"
              className="hidden items-center gap-1.5 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 sm:flex"
            >
              <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
              Log out
            </button>
            <button
              type="button"
              onClick={() => setMobileNavOpen((v) => !v)}
              aria-label={mobileNavOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileNavOpen}
              className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100 lg:hidden"
            >
              {mobileNavOpen ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
            </button>
          </div>
        </div>

        {mobileNavOpen && (
          <nav className="border-t border-slate-200 px-4 py-3 dark:border-slate-800 lg:hidden">
            <div className="flex flex-col gap-1">
              {navItems.map((item) => (
                <NavLink key={item.to} to={item.to} className={mobileNavLinkClass} onClick={() => setMobileNavOpen(false)}>
                  {item.label}
                </NavLink>
              ))}
              <button
                type="button"
                onClick={handleLogout}
                className="mt-2 flex items-center gap-1.5 rounded-md border border-slate-300 px-3 py-2 text-left text-sm font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300 sm:hidden"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                Log out
              </button>
            </div>
          </nav>
        )}
      </header>
      <main className="mx-auto max-w-7xl p-4 sm:p-6">
        <Outlet />
      </main>
    </div>
  );
}
