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
import ExamListPage from "../pages/ExamList";
import ExamRoomPage from "../pages/ExamRoom";
import ExamBuilderPage from "../pages/Teacher/ExamBuilder";
import GradingInterfacePage from "../pages/Teacher/GradingInterface";
import ResultsViewPage from "../pages/ResultsView";
import ResultApprovalPage from "../pages/Admin/ResultApproval";
import FeeCentrePage from "../pages/FeeCentre";
import FeeDashboardPage from "../pages/Admin/FeeDashboard";
import AdminReportsPage from "../pages/Admin/Reports";
import NotificationsPage from "../pages/Notifications";
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
          {
            path: "/exams",
            element: <ExamListPage />,
          },
          {
            path: "/exams/:examId/room",
            element: <ExamRoomPage />,
          },
          {
            path: "/teacher/exam-builder",
            element: <ExamBuilderPage />,
          },
          {
            path: "/teacher/exam-builder/:examId",
            element: <ExamBuilderPage />,
          },
          {
            path: "/teacher/grading/:examId",
            element: <GradingInterfacePage />,
          },
          {
            path: "/results",
            element: <ResultsViewPage />,
          },
          {
            path: "/admin/result-approval",
            element: <ResultApprovalPage />,
          },
          {
            path: "/fees",
            element: <FeeCentrePage />,
          },
          {
            path: "/admin/fee-dashboard",
            element: <FeeDashboardPage />,
          },
          {
            path: "/admin/reports",
            element: <AdminReportsPage />,
          },
          {
            path: "/notifications",
            element: <NotificationsPage />,
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
