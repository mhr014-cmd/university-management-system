// Dashboard page — role-specific summary widgets (Milestone 10), per
// docs/UI_Wireframes.md Section 2. Each role variant is a separate
// component so per-role widget logic and data hooks stay isolated
// (shared shell composition per CLAUDE.md Section 7, not four separate
// app trees).

import { useAuth } from "../../auth/AuthContext";
import { useMe } from "../../features/users";
import { StudentDashboard } from "./StudentDashboard";
import { TeacherDashboard } from "./TeacherDashboard";
import { ParentDashboard } from "./ParentDashboard";
import { AdminDashboard } from "./AdminDashboard";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: me } = useMe();

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
        Welcome back{me ? `, ${me.profile.first_name}` : ""}
      </h1>
      <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">Here's what's happening with your account.</p>

      {user?.role === "student" && <StudentDashboard />}
      {user?.role === "teacher" && <TeacherDashboard />}
      {user?.role === "parent" && <ParentDashboard />}
      {user?.role === "admin" && <AdminDashboard />}
    </div>
  );
}
