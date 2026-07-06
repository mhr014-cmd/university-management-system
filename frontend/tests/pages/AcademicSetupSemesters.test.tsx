// Component test: Admin Academic Setup — Semesters page (Version 2.3).
// Verifies: create submits name/start_date/end_date; the backend's
// start_date < end_date 422 is surfaced as a specific message rather than
// a generic error.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, AxiosHeaders } from "axios";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AcademicSetupSemestersPage from "../../src/pages/Admin/AcademicSetup/Semesters";
import { ToastProvider } from "../../src/components/ui/Toast";

const mutateAsyncCreate = vi.fn();

const semestersData = {
  items: [{ id: "sem-1", name: "Fall 2025", start_date: "2025-09-01", end_date: "2025-12-20" }],
  total: 1,
  page: 1,
  page_size: 100,
};

vi.mock("../../src/features/semesters", () => ({
  useSemesters: () => ({ data: semestersData, isLoading: false }),
  useCreateSemester: () => ({ mutateAsync: mutateAsyncCreate, isPending: false }),
  useUpdateSemester: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteSemester: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <AcademicSetupSemestersPage />
      </ToastProvider>
    </MemoryRouter>,
  );
}

describe("AcademicSetupSemestersPage", () => {
  beforeEach(() => {
    mutateAsyncCreate.mockReset();
  });

  it("submits name/start_date/end_date when creating a semester", async () => {
    mutateAsyncCreate.mockResolvedValue({ id: "sem-2" });
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /new semester/i }));
    await user.type(screen.getByLabelText(/^name/i), "Spring 2026");
    await user.type(screen.getByLabelText(/start date/i), "2026-01-15");
    await user.type(screen.getByLabelText(/end date/i), "2026-05-01");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    expect(mutateAsyncCreate).toHaveBeenCalledWith({
      name: "Spring 2026",
      start_date: "2026-01-15",
      end_date: "2026-05-01",
    });
  });

  it("shows a specific message when start_date is after end_date (422)", async () => {
    mutateAsyncCreate.mockRejectedValue(
      new AxiosError("Unprocessable", "422", undefined, undefined, {
        status: 422,
        statusText: "Unprocessable",
        headers: new AxiosHeaders(),
        config: { headers: new AxiosHeaders() },
        data: { error: { message: "start_date must be before end_date" } },
      }),
    );
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /new semester/i }));
    await user.type(screen.getByLabelText(/^name/i), "Bad Semester");
    await user.type(screen.getByLabelText(/start date/i), "2026-06-01");
    await user.type(screen.getByLabelText(/end date/i), "2026-01-01");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    expect(await screen.findByText(/start_date must be before end_date/i)).toBeInTheDocument();
  });
});
