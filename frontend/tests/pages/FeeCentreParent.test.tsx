// Component test: Parent-facing Fee Centre view (production-readiness
// audit gap closure). FeeCentre/index.tsx now branches by role — this
// covers the Parent branch: child selector, outstanding balance/invoices/
// payments scoped to the selected child, and the Invoice/Receipt download
// label switching based on invoice status.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, beforeEach, expect, it, vi } from "vitest";
import FeeCentrePage from "../../src/pages/FeeCentre";

vi.mock("../../src/auth/AuthContext", () => ({
  useAuth: () => ({ user: { role: "parent" }, isAuthenticated: true, login: vi.fn(), logout: vi.fn() }),
}));

const childrenData = {
  children: [
    { id: "student-1", first_name: "John", last_name: "Smith" },
    { id: "student-2", first_name: "Amy", last_name: "Smith" },
  ],
};
vi.mock("../../src/features/users", () => ({
  useMyChildren: () => ({ data: childrenData, isLoading: false, isError: false }),
}));

const feesData = {
  student_id: "student-1",
  outstanding_balance: 250,
  invoices: [
    { invoice_id: "inv-1", amount: 250, status: "unpaid", due_date: "2026-08-01" },
    { invoice_id: "inv-2", amount: 500, status: "paid", due_date: "2026-01-01" },
  ],
  payments: [{ payment_id: "pay-1", amount: 500, payment_date: "2026-01-02" }],
};
const mutateDownloadInvoice = vi.fn();
vi.mock("../../src/features/fees", () => ({
  useMyFees: () => ({ data: feesData, isLoading: false }),
  useDownloadInvoice: () => ({ mutate: mutateDownloadInvoice, isPending: false }),
}));

describe("FeeCentrePage — Parent", () => {
  beforeEach(() => {
    mutateDownloadInvoice.mockReset();
  });

  it("auto-selects the first linked child and shows their fee status", () => {
    render(<FeeCentrePage />);
    expect(screen.getAllByText("250.00").length).toBeGreaterThan(0);
    expect(screen.getByText(/Viewing fees for:/)).toHaveTextContent("John Smith");
  });

  it("labels an unpaid invoice's download button 'Download Invoice'", () => {
    render(<FeeCentrePage />);
    const row = screen.getByText("2026-08-01").closest("tr") as HTMLElement;
    expect(row.querySelector("button")).toHaveTextContent("Download Invoice");
  });

  it("labels a paid invoice's download button 'Download Receipt'", () => {
    render(<FeeCentrePage />);
    const row = screen.getByText("2026-01-01").closest("tr") as HTMLElement;
    expect(row.querySelector("button")).toHaveTextContent("Download Receipt");
  });

  it("downloads the invoice/receipt for the clicked row", async () => {
    const user = userEvent.setup();
    render(<FeeCentrePage />);

    const row = screen.getByText("2026-01-01").closest("tr") as HTMLElement;
    await user.click(row.querySelector("button") as HTMLElement);

    expect(mutateDownloadInvoice).toHaveBeenCalledWith("inv-2");
  });

  it("lets the parent switch children via the Linked Child selector", async () => {
    const user = userEvent.setup();
    render(<FeeCentrePage />);

    const select = screen.getByDisplayValue("John Smith");
    await user.selectOptions(select, "student-2");

    expect(screen.getByText(/Viewing fees for:/)).toHaveTextContent("Amy Smith");
  });
});
