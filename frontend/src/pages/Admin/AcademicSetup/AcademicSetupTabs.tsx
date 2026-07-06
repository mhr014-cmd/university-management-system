// Shared sub-nav for the four Academic Setup pages (Version 2.3).
// Real routes, not local tab state — each of Departments/Courses/Rooms/
// Semesters is its own bookmarkable page (per the approved plan), so this
// renders NavLinks rather than switching a local `tab` variable the way
// Admin/Reports's internal tabs do.

import { NavLink } from "react-router-dom";

const TABS = [
  { to: "/admin/academic-setup/departments", label: "Departments" },
  { to: "/admin/academic-setup/courses", label: "Courses" },
  { to: "/admin/academic-setup/rooms", label: "Rooms" },
  { to: "/admin/academic-setup/semesters", label: "Semesters" },
];

function tabClass({ isActive }: { isActive: boolean }): string {
  return `rounded px-3 py-1 text-sm font-medium transition-colors ${
    isActive
      ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
  }`;
}

export function AcademicSetupTabs() {
  return (
    <div className="flex flex-wrap gap-1 rounded-md border border-slate-200 p-1 dark:border-slate-700 w-fit">
      {TABS.map((tab) => (
        <NavLink key={tab.to} to={tab.to} className={tabClass}>
          {tab.label}
        </NavLink>
      ))}
    </div>
  );
}
