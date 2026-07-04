// Notifications page (FR-052, FR-053). Layout matches
// docs/UI_Wireframes.md Section 16: chronological feed (newest first),
// unread items visually distinguished, "Mark all as read" bulk action,
// pagination, and per-item click marks read + deep-links based on type.

import { useNavigate } from "react-router-dom";
import { useMarkNotificationRead, useNotifications } from "../../features/notifications";
import type { NotificationEntry, NotificationType } from "../../features/notifications";

const TYPE_ROUTES: Record<NotificationType, string | null> = {
  result_published: "/results",
  attendance_warning: "/attendance",
  schedule_change: "/timetable",
  fee_due: "/fees",
  other: null,
};

export default function NotificationsPage() {
  const { data, isLoading } = useNotifications();
  const markRead = useMarkNotificationRead();
  const navigate = useNavigate();

  const handleClick = async (notification: NotificationEntry) => {
    if (!notification.is_read) {
      await markRead.mutateAsync(notification.id);
    }
    const route = TYPE_ROUTES[notification.type];
    if (route) navigate(route);
  };

  const handleMarkAllAsRead = async () => {
    const unread = data?.items.filter((n) => !n.is_read) ?? [];
    for (const notification of unread) {
      await markRead.mutateAsync(notification.id);
    }
  };

  if (isLoading || !data) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading notifications...</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
          Notifications {data.unread_count > 0 && `(${data.unread_count} unread)`}
        </h1>
        <button
          type="button"
          onClick={handleMarkAllAsRead}
          disabled={data.unread_count === 0 || markRead.isPending}
          className="rounded border border-slate-300 px-3 py-2 text-sm disabled:opacity-50 dark:border-slate-600"
        >
          Mark all as read
        </button>
      </div>

      <ul className="divide-y divide-slate-200 dark:divide-slate-700">
        {data.items.map((notification) => (
          <li key={notification.id}>
            <button
              type="button"
              onClick={() => handleClick(notification)}
              className="flex w-full items-start gap-3 py-3 text-left"
            >
              <span
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                  notification.is_read ? "border border-slate-400" : "bg-slate-900 dark:bg-slate-100"
                }`}
              />
              <span className="flex-1">
                <span className={`block text-sm ${notification.is_read ? "text-slate-500 dark:text-slate-400" : "font-medium text-slate-900 dark:text-slate-100"}`}>
                  {notification.message}
                </span>
                <span className="text-xs text-slate-400 dark:text-slate-500">
                  {new Date(notification.created_at).toLocaleString()}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      {data.items.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">No notifications yet.</p>
      )}
    </div>
  );
}
