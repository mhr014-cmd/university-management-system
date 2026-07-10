// Component test: Admin Reports — Results/Fees export consistency
// enhancement. The pre-existing Attendance tab (Print/PDF/Excel) is
// unchanged; this covers only the newly wired Results/Fees export
// buttons, reusing the same ReportToolbar/exportClient infrastructure.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, beforeEach, expect, it, vi } from "vitest";
import AdminReportsPage from "../../src/pages/Admin/Reports";
import { ToastProvider } from "../../src/components/ui/Toast";

vi.mock("../../src/features/departments", () => ({
  useDepartments: () => ({ data: { items: [] } }),
}));
vi.mock("../../src/features/semesters", () => ({
  useSemesters: () => ({ data: { items: [] } }),
}));
vi.mock("../../src/features/users", () => ({
  useStudents: () => ({ data: { items: [] } }),
}));

const attendanceData = { scope: {}, summary: [] };
const exportAttendancePdf = vi.fn();
const exportAttendanceExcel = vi.fn();
vi.mock("../../src/features/attendance", () => ({
  useAttendanceReports: () => ({ data: attendanceData, isLoading: false }),
  useExportAttendanceReportPdf: () => ({ mutate: exportAttendancePdf, isPending: false }),
  useExportAttendanceReportExcel: () => ({ mutate: exportAttendanceExcel, isPending: false }),
}));

const resultsData = {
  scope: {},
  grade_distribution: [{ grade_letter: "A", count: 2 }],
  pass_count: 2,
  fail_count: 0,
  average_gpa: 4.0,
  details: [
    { student_id: "s1", student_name: "Rafiq Chowdhury", course_name: "Data Structures", exam_title: "Midterm", grade_letter: "A", grade_point: 4.0 },
  ],
};
const exportResultsPdf = vi.fn();
const exportResultsExcel = vi.fn();
vi.mock("../../src/features/results", () => ({
  useResultsReport: () => ({ data: resultsData, isLoading: false }),
  useExportResultsReportPdf: () => ({ mutate: exportResultsPdf, isPending: false }),
  useExportResultsReportExcel: () => ({ mutate: exportResultsExcel, isPending: false }),
}));

const feesData = {
  scope: {},
  total_collected: 4000,
  total_outstanding: 6000,
  total_overdue: 2000,
  details: [
    { student_id: "s1", student_name: "Rafiq Chowdhury", fee_name: "Tuition", amount: 10000, paid: 4000, outstanding: 6000, due_date: "2026-01-01", status: "overdue" },
  ],
};
const exportFeesPdf = vi.fn();
const exportFeesExcel = vi.fn();
vi.mock("../../src/features/fees", () => ({
  useFeesReport: () => ({ data: feesData, isLoading: false }),
  useExportFeesReportPdf: () => ({ mutate: exportFeesPdf, isPending: false }),
  useExportFeesReportExcel: () => ({ mutate: exportFeesExcel, isPending: false }),
}));

function renderPage() {
  return render(
    <ToastProvider>
      <AdminReportsPage />
    </ToastProvider>,
  );
}

describe("AdminReportsPage — Results/Fees export consistency", () => {
  beforeEach(() => {
    exportAttendancePdf.mockReset();
    exportAttendanceExcel.mockReset();
    exportResultsPdf.mockReset();
    exportResultsExcel.mockReset();
    exportFeesPdf.mockReset();
    exportFeesExcel.mockReset();
  });

  it("Results tab shows Print/PDF/Excel and exports with the active filters", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /^results$/i }));

    // Detail-section gap closure: the summary alone never showed which
    // academic records produced it — verify the on-screen detail table
    // (which Print also renders, since Print is window.print() on this
    // same DOM) shows the underlying record.
    expect(screen.getByText("Rafiq Chowdhury")).toBeInTheDocument();
    expect(screen.getByText("Data Structures")).toBeInTheDocument();
    expect(screen.getByText("Midterm")).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /print/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /pdf/i }));
    await user.click(screen.getByRole("button", { name: /excel/i }));

    expect(exportResultsPdf).toHaveBeenCalledWith(
      { departmentId: undefined, semesterId: undefined, studentId: undefined },
      expect.anything(),
    );
    expect(exportResultsExcel).toHaveBeenCalledWith(
      { departmentId: undefined, semesterId: undefined, studentId: undefined },
      expect.anything(),
    );
  });

  it("Fees tab shows Print/PDF/Excel and exports with the active filters", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /^fees$/i }));

    // Detail-section gap closure: the summary totals alone never showed
    // what they represent — verify the itemized fee breakdown renders.
    expect(screen.getByText("Rafiq Chowdhury")).toBeInTheDocument();
    expect(screen.getByText("Tuition")).toBeInTheDocument();
    expect(screen.getByText("2026-01-01")).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /print/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /pdf/i }));
    await user.click(screen.getByRole("button", { name: /excel/i }));

    expect(exportFeesPdf).toHaveBeenCalledWith(
      { departmentId: undefined, semesterId: undefined, studentId: undefined },
      expect.anything(),
    );
    expect(exportFeesExcel).toHaveBeenCalledWith(
      { departmentId: undefined, semesterId: undefined, studentId: undefined },
      expect.anything(),
    );
  });

  it("does not affect the pre-existing Attendance tab's exports", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /pdf/i }));
    await user.click(screen.getByRole("button", { name: /excel/i }));

    expect(exportAttendancePdf).toHaveBeenCalledTimes(1);
    expect(exportAttendanceExcel).toHaveBeenCalledTimes(1);
  });
});
