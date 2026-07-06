// Component test: shared ReportLayout (Version 1.2 reporting
// infrastructure). Verifies the title/subtitle/toolbar render, and that
// the printable content is wrapped in the [data-print-region] marker
// styles/print.css relies on for print isolation.

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReportLayout } from "../../src/components/ui/ReportLayout";

describe("ReportLayout", () => {
  it("renders the title, subtitle, toolbar, and children", () => {
    render(
      <ReportLayout title="Attendance Report" subtitle="All Departments" toolbar={<button>Export</button>}>
        <p>Report body</p>
      </ReportLayout>,
    );

    expect(screen.getAllByText("Attendance Report").length).toBeGreaterThan(0);
    expect(screen.getAllByText("All Departments").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Export" })).toBeInTheDocument();
    expect(screen.getByText("Report body")).toBeInTheDocument();
  });

  it("wraps children in a [data-print-region] element", () => {
    const { container } = render(
      <ReportLayout title="Attendance Report">
        <p>Report body</p>
      </ReportLayout>,
    );

    const printRegion = container.querySelector("[data-print-region]");
    expect(printRegion).not.toBeNull();
    expect(printRegion?.textContent).toContain("Report body");
  });

  it("renders without a toolbar or subtitle when omitted", () => {
    render(
      <ReportLayout title="Attendance Report">
        <p>Report body</p>
      </ReportLayout>,
    );

    expect(screen.getAllByText("Attendance Report").length).toBeGreaterThan(0);
    expect(screen.getByText("Report body")).toBeInTheDocument();
  });
});
