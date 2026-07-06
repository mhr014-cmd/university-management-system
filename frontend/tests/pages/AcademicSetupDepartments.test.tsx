// Component test: Admin Academic Setup — Departments page (Version 2.3).
// Verifies: create submits name/code to the API; delete on a
// still-referenced row surfaces the 409 conflict message instead of a
// generic error, since that's the whole point of the hard-DELETE +
// ON DELETE RESTRICT design (see the implementation report).

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, AxiosHeaders } from "axios";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AcademicSetupDepartmentsPage from "../../src/pages/Admin/AcademicSetup/Departments";
import { ToastProvider } from "../../src/components/ui/Toast";

function renderPage() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <AcademicSetupDepartmentsPage />
      </ToastProvider>
    </MemoryRouter>,
  );
}

const mutateAsyncCreate = vi.fn();
const mutateAsyncDelete = vi.fn();

const departmentsData = {
  items: [{ id: "dept-1", name: "Computer Science", code: "CS" }],
  total: 1,
  page: 1,
  page_size: 100,
};

vi.mock("../../src/features/departments", () => ({
  useDepartments: () => ({ data: departmentsData, isLoading: false }),
  useCreateDepartment: () => ({ mutateAsync: mutateAsyncCreate, isPending: false }),
  useUpdateDepartment: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteDepartment: () => ({ mutateAsync: mutateAsyncDelete, isPending: false }),
}));

describe("AcademicSetupDepartmentsPage", () => {
  beforeEach(() => {
    mutateAsyncCreate.mockReset();
    mutateAsyncDelete.mockReset();
  });

  it("submits name and code when creating a department", async () => {
    mutateAsyncCreate.mockResolvedValue({ id: "dept-2", name: "Business Administration", code: "BA" });
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /new department/i }));
    await user.type(screen.getByLabelText(/name/i), "Business Administration");
    await user.type(screen.getByLabelText(/code/i), "BA");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    expect(mutateAsyncCreate).toHaveBeenCalledWith({ name: "Business Administration", code: "BA" });
  });

  it("shows the 409 conflict message when deleting a still-referenced department", async () => {
    mutateAsyncDelete.mockRejectedValue(
      new AxiosError("Conflict", "409", undefined, undefined, {
        status: 409,
        statusText: "Conflict",
        headers: new AxiosHeaders(),
        config: { headers: new AxiosHeaders() },
        data: { error: { message: "conflict" } },
      }),
    );
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /delete/i }));
    const dialog = await screen.findByRole("alertdialog");
    await user.click(within(dialog).getByRole("button", { name: /^delete$/i }));

    expect(await screen.findByText(/still referenced by existing courses/i)).toBeInTheDocument();
  });
});
