// Application router — basic navigation shell (Milestone 0).
// Role-aware route guards (frontend/src/auth/RouteGuard.tsx) are wired in
// starting Milestone 2; every route below is currently public.

import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "../components/AppLayout";
import LoginPage from "../pages/Login";
import DashboardPage from "../pages/Dashboard";
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
    element: <AppLayout />,
    children: [
      {
        path: "/dashboard",
        element: <DashboardPage />,
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
