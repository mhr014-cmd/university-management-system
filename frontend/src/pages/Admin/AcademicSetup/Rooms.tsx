// Admin: Academic Setup — Rooms (Version 2.3). Closes the gap the
// pre-V2.3 architecture review identified: Room had a working backend
// CRUD (list/create since Milestone 1, update/delete added for this
// version) but zero frontend presence at all — not even read-only.

import { useState, type FormEvent } from "react";
import { isAxiosError } from "axios";
import { AlertCircle, DoorOpen, Plus } from "lucide-react";
import { useCreateRoom, useDeleteRoom, useRooms, useUpdateRoom, type Room } from "../../../features/rooms";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { ConfirmDialog } from "../../../components/ui/ConfirmDialog";
import { EmptyState } from "../../../components/ui/EmptyState";
import { PageLoader } from "../../../components/ui/PageLoader";
import { useToast } from "../../../components/ui/Toast";
import { inputClass, labelClass } from "../../../components/ui/classNames";
import { AcademicSetupTabs } from "./AcademicSetupTabs";

export default function AcademicSetupRoomsPage() {
  const { showSuccess, showError } = useToast();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editing, setEditing] = useState<Room | null>(null);
  const [deleting, setDeleting] = useState<Room | null>(null);

  const { data, isLoading } = useRooms();
  const deleteRoom = useDeleteRoom();

  const handleDelete = async () => {
    if (!deleting) return;
    try {
      await deleteRoom.mutateAsync(deleting.id);
      showSuccess("Room deleted.");
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        showError("This room is still referenced by existing schedule entries and cannot be deleted.");
      } else {
        showError("Could not delete this room. Please try again.");
      }
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Academic Setup</h1>
        <Button icon={<Plus className="h-4 w-4" aria-hidden="true" />} onClick={() => setShowCreateForm(true)}>
          New Room
        </Button>
      </div>

      <AcademicSetupTabs />

      {isLoading || !data ? (
        <PageLoader />
      ) : data.items.length === 0 ? (
        <EmptyState icon={DoorOpen} title="No rooms yet" description="Create the first room to get started." />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2.5">Name</th>
                <th className="px-4 py-2.5">Building</th>
                <th className="px-4 py-2.5">Capacity</th>
                <th className="px-4 py-2.5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((room) => (
                <tr
                  key={room.id}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-2.5">{room.name}</td>
                  <td className="px-4 py-2.5">{room.building ?? "—"}</td>
                  <td className="px-4 py-2.5">{room.capacity ?? "—"}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex gap-2">
                      <Button variant="secondary" size="sm" onClick={() => setEditing(room)}>
                        Edit
                      </Button>
                      <Button variant="danger" size="sm" onClick={() => setDeleting(room)}>
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {showCreateForm && (
        <RoomFormModal title="New Room" onClose={() => setShowCreateForm(false)} onSaved={() => showSuccess("Room created.")} />
      )}
      {editing && (
        <RoomFormModal
          title="Edit Room"
          room={editing}
          onClose={() => setEditing(null)}
          onSaved={() => showSuccess("Changes saved.")}
        />
      )}
      {deleting && (
        <ConfirmDialog
          isOpen
          title="Delete room?"
          description={`Are you sure you want to delete "${deleting.name}"? This cannot be undone.`}
          confirmLabel="Delete"
          tone="danger"
          isLoading={deleteRoom.isPending}
          onConfirm={() => void handleDelete()}
          onCancel={() => setDeleting(null)}
        />
      )}
    </div>
  );
}

function RoomFormModal({
  title,
  room,
  onClose,
  onSaved,
}: {
  title: string;
  room?: Room;
  onClose: () => void;
  onSaved: () => void;
}) {
  const createRoom = useCreateRoom();
  const updateRoom = useUpdateRoom();

  const [name, setName] = useState(room?.name ?? "");
  const [building, setBuilding] = useState(room?.building ?? "");
  const [capacity, setCapacity] = useState(room?.capacity != null ? String(room.capacity) : "");
  const [error, setError] = useState<string | null>(null);

  const isPending = createRoom.isPending || updateRoom.isPending;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const payload = {
      name,
      building: building || null,
      capacity: capacity ? Number(capacity) : null,
    };
    try {
      if (room) {
        await updateRoom.mutateAsync({ id: room.id, payload });
      } else {
        await createRoom.mutateAsync(payload);
      }
      onSaved();
      onClose();
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setError("A room with this name already exists.");
      } else {
        setError("Could not save this room. Please try again.");
      }
    }
  };

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-900"
      >
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
        {error && (
          <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}
        <div>
          <label htmlFor="room-name" className={labelClass}>
            Name <span className="text-red-500">*</span>
          </label>
          <input id="room-name" required value={name} onChange={(e) => setName(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="room-building" className={labelClass}>Building</label>
          <input id="room-building" value={building} onChange={(e) => setBuilding(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="room-capacity" className={labelClass}>Capacity</label>
          <input
            id="room-capacity"
            type="number"
            min={1}
            value={capacity}
            onChange={(e) => setCapacity(e.target.value)}
            className={inputClass}
          />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" isLoading={isPending}>Save</Button>
        </div>
      </form>
    </div>
  );
}
