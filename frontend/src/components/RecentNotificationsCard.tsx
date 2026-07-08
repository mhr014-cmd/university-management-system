// Shared "Latest Notifications" dashboard widget (enterprise-polish pass).
// Extracted from Dashboard/ParentDashboard.tsx, where it was first added
// (production-readiness audit gap closure) as a Parent-only widget reusing
// the existing generic GET /notifications endpoint — no new API surface.
// Extracting it lets Admin/Teacher/Student dashboards surface unread
// notifications too, using the exact same hook/endpoint.

import { Bell } from "lucide-react";
import { Link } from "react-router-dom";
import { useNotifications } from "../features/notifications";
import { Card } from "./ui/Card";
import { EmptyState } from "./ui/EmptyState";
import { Skeleton } from "./ui/Skeleton";

export function RecentNotificationsCard() {
  const { data, isLoading } = useNotifications({ pageSize: 5 });
  const unreadCount = (data?.items ?? []).filter((n) => !n.is_read).length;

  return (
    <Card>
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Latest Notifications</p>
          {unreadCount > 0 && (
            <span className="rounded-full bg-slate-900 px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white dark:bg-slate-100 dark:text-slate-900">
              {unreadCount} new
            </span>
          )}
        </div>
        <Link to="/notifications" className="text-xs font-medium text-slate-600 hover:underline dark:text-slate-300">
          View all
        </Link>
      </div>
      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <EmptyState icon={Bell} title="No notifications yet" />
      ) : (
        <ul className="space-y-2">
          {data.items.map((notification) => (
            <li key={notification.id} className="flex items-start gap-2 text-sm">
              <span
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                  notification.is_read ? "border border-slate-400" : "bg-slate-900 dark:bg-slate-100"
                }`}
              />
              <span className={notification.is_read ? "text-slate-500 dark:text-slate-400" : "font-medium text-slate-900 dark:text-slate-100"}>
                {notification.message}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
