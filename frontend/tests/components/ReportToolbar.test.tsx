// Component test: shared ReportToolbar (Version 1.2 reporting
// infrastructure). Verifies Print/PDF/Excel wiring — Print falls back to
// window.print() when no onPrint is supplied; PDF/Excel always call their
// required callback props; isExportingPdf/isExportingExcel drive the
// shared Button's loading state.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReportToolbar } from "../../src/components/ui/ReportToolbar";

describe("ReportToolbar", () => {
  let printSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    printSpy = vi.fn();
    window.print = printSpy;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("calls window.print() when Print is clicked and no onPrint is supplied", async () => {
    const user = userEvent.setup();
    render(<ReportToolbar onExportPdf={vi.fn()} onExportExcel={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /print/i }));

    expect(printSpy).toHaveBeenCalledOnce();
  });

  it("calls the supplied onPrint instead of window.print() when provided", async () => {
    const user = userEvent.setup();
    const onPrint = vi.fn();
    render(<ReportToolbar onPrint={onPrint} onExportPdf={vi.fn()} onExportExcel={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /print/i }));

    expect(onPrint).toHaveBeenCalledOnce();
    expect(printSpy).not.toHaveBeenCalled();
  });

  it("calls onExportPdf when PDF is clicked", async () => {
    const user = userEvent.setup();
    const onExportPdf = vi.fn();
    render(<ReportToolbar onExportPdf={onExportPdf} onExportExcel={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /pdf/i }));

    expect(onExportPdf).toHaveBeenCalledOnce();
  });

  it("calls onExportExcel when Excel is clicked", async () => {
    const user = userEvent.setup();
    const onExportExcel = vi.fn();
    render(<ReportToolbar onExportPdf={vi.fn()} onExportExcel={onExportExcel} />);

    await user.click(screen.getByRole("button", { name: /excel/i }));

    expect(onExportExcel).toHaveBeenCalledOnce();
  });

  it("disables the PDF button while isExportingPdf is true", () => {
    render(<ReportToolbar onExportPdf={vi.fn()} onExportExcel={vi.fn()} isExportingPdf />);

    expect(screen.getByRole("button", { name: /pdf/i })).toBeDisabled();
  });

  it("disables the Excel button while isExportingExcel is true", () => {
    render(<ReportToolbar onExportPdf={vi.fn()} onExportExcel={vi.fn()} isExportingExcel />);

    expect(screen.getByRole("button", { name: /excel/i })).toBeDisabled();
  });

  it("does not render a CSV button when onExportCsv is omitted", () => {
    render(<ReportToolbar onExportPdf={vi.fn()} onExportExcel={vi.fn()} />);
    expect(screen.queryByRole("button", { name: /csv/i })).not.toBeInTheDocument();
  });

  it("calls onExportCsv when CSV is clicked", async () => {
    const user = userEvent.setup();
    const onExportCsv = vi.fn();
    render(<ReportToolbar onExportPdf={vi.fn()} onExportExcel={vi.fn()} onExportCsv={onExportCsv} />);

    await user.click(screen.getByRole("button", { name: /csv/i }));

    expect(onExportCsv).toHaveBeenCalledOnce();
  });

  it("disables the CSV button while isExportingCsv is true", () => {
    render(<ReportToolbar onExportPdf={vi.fn()} onExportExcel={vi.fn()} onExportCsv={vi.fn()} isExportingCsv />);
    expect(screen.getByRole("button", { name: /csv/i })).toBeDisabled();
  });
});
