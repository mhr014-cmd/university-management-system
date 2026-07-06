// Component test: Admin Academic Setup — Courses page (Version 2.3).
// Verifies: create submits department_id/name/code/credit_hours (via the
// SearchableSelect department picker) to the API — this is the one
// Academic Setup page that exercises SearchableSelect inside a real form,
// not just the component test's own isolated cases.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AcademicSetupCoursesPage from "../../src/pages/Admin/AcademicSetup/Courses";
import { ToastProvider } from "../../src/components/ui/Toast";

const mutateAsyncCreate = vi.fn();

const departmentsData = {
  items: [{ id: "dept-1", name: "Computer Science", code: "CS" }],
  total: 1,
  page: 1,
  page_size: 100,
};

const coursesData = {
  items: [{ id: "course-1", department_id: "dept-1", name: "Intro to CS", code: "CS101", credit_hours: 3 }],
  total: 1,
  page: 1,
  page_size: 100,
};

vi.mock("../../src/features/departments", () => ({
  useDepartments: () => ({ data: departmentsData, isLoading: false }),
}));

vi.mock("../../src/features/courses", () => ({
  useCourses: () => ({ data: coursesData, isLoading: false }),
  useCreateCourse: () => ({ mutateAsync: mutateAsyncCreate, isPending: false }),
  useUpdateCourse: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteCourse: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <AcademicSetupCoursesPage />
      </ToastProvider>
    </MemoryRouter>,
  );
}

describe("AcademicSetupCoursesPage", () => {
  beforeEach(() => {
    mutateAsyncCreate.mockReset();
  });

  it("submits department_id/name/code/credit_hours when creating a course", async () => {
    mutateAsyncCreate.mockResolvedValue({ id: "course-2" });
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /new course/i }));
    await user.click(screen.getByRole("button", { name: /department/i }));
    const listbox = screen.getByRole("listbox");
    await user.click(within(listbox).getByRole("option", { name: "Computer Science" }));
    await user.type(screen.getByLabelText(/^name/i), "Data Structures");
    await user.type(screen.getByLabelText(/^code/i), "CS201");
    await user.type(screen.getByLabelText(/credit hours/i), "4");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    expect(mutateAsyncCreate).toHaveBeenCalledWith({
      department_id: "dept-1",
      name: "Data Structures",
      code: "CS201",
      credit_hours: 4,
    });
  });

  it("renders the existing course's department name in the table", () => {
    renderPage();
    const row = screen.getByText("Intro to CS").closest("tr");
    expect(row).not.toBeNull();
    expect(within(row as HTMLElement).getByText("Computer Science")).toBeInTheDocument();
  });
});
