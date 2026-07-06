// React Query hooks: rooms (see docs/API_Contract.md Section 10.7-10.9).
//
// Added for Version 2.3 (Academic Setup) — the backend GET/POST/PUT/DELETE
// /rooms endpoints existed since Milestone 1 (list/create) and Version 2.3
// (update/delete), but had no frontend feature-hook file at all until now
// (per the pre-V2.3 architecture review's finding: Room had zero frontend
// presence, not even read-only).

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export interface Room {
  id: string;
  name: string;
  building: string | null;
  capacity: number | null;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface RoomInput {
  name: string;
  building?: string | null;
  capacity?: number | null;
}

const roomsQueryKey = ["rooms"] as const;

export function useRooms(page = 1, pageSize = 100) {
  return useQuery({
    queryKey: [...roomsQueryKey, page, pageSize],
    queryFn: async () =>
      (await apiClient.get<PaginatedResponse<Room>>("/rooms", { params: { page, page_size: pageSize } })).data,
  });
}

export function useCreateRoom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: RoomInput) => (await apiClient.post<Room>("/rooms", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roomsQueryKey });
    },
  });
}

export function useUpdateRoom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<RoomInput> }) =>
      (await apiClient.put<Room>(`/rooms/${id}`, payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roomsQueryKey });
    },
  });
}

export function useDeleteRoom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/rooms/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roomsQueryKey });
    },
  });
}
