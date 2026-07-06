// Notifications page (FR-052, FR-053). Layout matches
// docs/UI_Wireframes.md Section 16: chronological feed (newest first),
// unread items visually distinguished, "Mark all as read" bulk action,
// pagination, and per-item click marks read + deep-links based on type.

import { useNavigate } from "react-router-dom";
import { Bell, CheckCheck } from "lucide-react";
import { useMarkNotificationRead, useNotifications } from "../../features/notifications";
import type { NotificationEntry, NotificationType } from "../../features/notifications";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";

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
    return <PageLoader label="Loading notifications..." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
          Notifications {data.unread_count > 0 && `(${data.unread_count} unread)`}
        </h1>
        <Button
          variant="secondary"
          size="sm"
          icon={<CheckCheck className="h-3.5 w-3.5" aria-hidden="true" />}
          onClick={handleMarkAllAsRead}
          disabled={data.unread_count === 0}
          isLoading={markRead.isPending}
        >
          Mark all as read
        </Button>
      </div>

      {data.items.length === 0 ? (
        <EmptyState icon={Bell} title="No notifications yet" description="Result publishing, schedule changes, attendance warnings, and fee due dates will show up here." />
      ) : (
        <Card className="divide-y divide-slate-100 p-0 dark:divide-slate-800">
          {data.items.map((notification) => (
            <button
              key={notification.id}
              type="button"
              onClick={() => handleClick(notification)}
              className="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50"
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
          ))}
        </Card>
      )}
    </div>
  );
}
