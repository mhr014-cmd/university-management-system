// Application router.
// Every route under AppLayout is wrapped in RouteGuard (Milestone 2):
// unauthenticated users are redirected to /login. Server-side RBAC
// (app/middleware/rbac.py) is the actual enforcement — this is UX only,
// per CLAUDE.md Section 7.

import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "../components/AppLayout";
import { RouteGuard } from "../auth/RouteGuard";
import LoginPage from "../pages/Login";
import DashboardPage from "../pages/Dashboard";
import ProfilePage from "../pages/Profile";
import UserManagementPage from "../pages/Admin/UserManagement";
import TimetablePage from "../pages/Timetable";
import AttendancePage from "../pages/Attendance";
import AttendanceMarkerPage from "../pages/Teacher/AttendanceMarker";
import NotFoundPage from "../pages/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/login" replace />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    element: <RouteGuard />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            path: "/dashboard",
            element: <DashboardPage />,
          },
          {
            path: "/profile",
            element: <ProfilePage />,
          },
          {
            path: "/admin/users",
            element: <UserManagementPage />,
          },
          {
            path: "/timetable",
            element: <TimetablePage />,
          },
          {
            path: "/attendance",
            element: <AttendancePage />,
          },
          {
            path: "/teacher/attendance-marker",
            element: <AttendanceMarkerPage />,
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
