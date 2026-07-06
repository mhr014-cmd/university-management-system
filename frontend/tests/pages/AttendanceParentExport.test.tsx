// Component test: Parent Attendance export toolbar (production-readiness
// audit gap closure). The pre-existing Parent attendance view (child
// selector, table/calendar) is unchanged; this covers only the newly
// added PDF/Excel/CSV export buttons and their scoping to the selected
// child.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, beforeEach, expect, it, vi } from "vitest";
import AttendancePage from "../../src/pages/Attendance";

vi.mock("../../src/auth/AuthContext", () => ({
  useAuth: () => ({ user: { role: "parent" }, isAuthenticated: true, login: vi.fn(), logout: vi.fn() }),
}));

const childrenData = { children: [{ id: "student-1", first_name: "John", last_name: "Smith" }] };
vi.mock("../../src/features/users", () => ({
  useMyChildren: () => ({ data: childrenData, isLoading: false, isError: false }),
}));

const attendanceData = {
  overall_percentage: 92,
  low_attendance_warning: false,
  by_class_session: [],
};
const mutateExportPdf = vi.fn();
const mutateExportExcel = vi.fn();
const mutateExportCsv = vi.fn();
vi.mock("../../src/features/attendance", () => ({
  useMyAttendance: () => ({ data: attendanceData, isLoading: false }),
  useExportAttendanceReportPdf: () => ({ mutate: mutateExportPdf, isPending: false }),
  useExportAttendanceReportExcel: () => ({ mutate: mutateExportExcel, isPending: false }),
  useExportAttendanceReportCsv: () => ({ mutate: mutateExportCsv, isPending: false }),
}));

describe("AttendancePage — Parent export toolbar", () => {
  beforeEach(() => {
    mutateExportPdf.mockReset();
    mutateExportExcel.mockReset();
    mutateExportCsv.mockReset();
  });

  it("exports the selected child's attendance as PDF/Excel/CSV", async () => {
    const user = userEvent.setup();
    render(<AttendancePage />);

    await user.click(screen.getByRole("button", { name: /pdf/i }));
    await user.click(screen.getByRole("button", { name: /excel/i }));
    await user.click(screen.getByRole("button", { name: /csv/i }));

    expect(mutateExportPdf).toHaveBeenCalledWith({ studentId: "student-1" });
    expect(mutateExportExcel).toHaveBeenCalledWith({ studentId: "student-1" });
    expect(mutateExportCsv).toHaveBeenCalledWith({ studentId: "student-1" });
  });
});
