// Component test: Admin Academic Setup — Rooms page (Version 2.3).
// Verifies: create submits name/building/capacity (nulling optional
// fields left blank, matching the backend's RoomCreate schema).

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AcademicSetupRoomsPage from "../../src/pages/Admin/AcademicSetup/Rooms";
import { ToastProvider } from "../../src/components/ui/Toast";

const mutateAsyncCreate = vi.fn();

const roomsData = {
  items: [{ id: "room-1", name: "Room 101", building: "Main", capacity: 30 }],
  total: 1,
  page: 1,
  page_size: 100,
};

vi.mock("../../src/features/rooms", () => ({
  useRooms: () => ({ data: roomsData, isLoading: false }),
  useCreateRoom: () => ({ mutateAsync: mutateAsyncCreate, isPending: false }),
  useUpdateRoom: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteRoom: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <AcademicSetupRoomsPage />
      </ToastProvider>
    </MemoryRouter>,
  );
}

describe("AcademicSetupRoomsPage", () => {
  beforeEach(() => {
    mutateAsyncCreate.mockReset();
  });

  it("submits name/building/capacity when creating a room", async () => {
    mutateAsyncCreate.mockResolvedValue({ id: "room-2" });
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /new room/i }));
    await user.type(screen.getByLabelText(/^name/i), "Room 202");
    await user.type(screen.getByLabelText(/building/i), "Annex");
    await user.type(screen.getByLabelText(/capacity/i), "25");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    expect(mutateAsyncCreate).toHaveBeenCalledWith({ name: "Room 202", building: "Annex", capacity: 25 });
  });

  it("submits null building/capacity when left blank", async () => {
    mutateAsyncCreate.mockResolvedValue({ id: "room-2" });
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /new room/i }));
    await user.type(screen.getByLabelText(/^name/i), "Room 303");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    expect(mutateAsyncCreate).toHaveBeenCalledWith({ name: "Room 303", building: null, capacity: null });
  });
});
