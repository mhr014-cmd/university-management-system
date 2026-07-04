// React Query hooks: notifications (feed, read state)
// See docs/API_Contract.md Section 8.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export type NotificationType = "result_published" | "schedule_change" | "attendance_warning" | "fee_due" | "other";

export interface NotificationEntry {
  id: string;
  type: NotificationType;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationEntry[];
  unread_count: number;
  total: number;
}

export function useNotifications(params?: { isRead?: boolean; page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: ["notifications", params],
    queryFn: async () =>
      (
        await apiClient.get<NotificationListResponse>("/notifications", {
          params: { is_read: params?.isRead, page: params?.page ?? 1, page_size: params?.pageSize ?? 20 },
        })
      ).data,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (notificationId: string) =>
      (await apiClient.put<{ id: string; is_read: boolean }>(`/notifications/${notificationId}/read`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}
