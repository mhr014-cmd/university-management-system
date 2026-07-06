// Fee Centre page (FR-038, FR-042). Layout matches docs/UI_Wireframes.md
// Section 8: outstanding balance card with due date, payment history
// table with per-row invoice download.
//
// Known simplification: this milestone builds the Student-facing view
// only, matching Implementation_Roadmap.md's Milestone 8 frontend page
// list ("Fee centre"). Parent access is fully implemented and tested
// server-side (GET /fees/me accepts a student_id for Parent callers,
// verified against parent_student_link); the Parent-facing equivalent of
// this view is the Fee Status widget on ParentDashboard.tsx (which uses
// GET /users/me/children, added in the production-polish audit, for
// child selection) rather than a dedicated Parent Fee Centre page. See
// PROJECT_PROGRESS.md's Milestone 8 entry.

import { Download, Receipt, Wallet } from "lucide-react";
import { InvoiceStatus, useMyFees, useDownloadInvoice } from "../../features/fees";
import { Badge, type BadgeTone } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";

const invoiceStatusTone: Record<InvoiceStatus, BadgeTone> = {
  paid: "green",
  partially_paid: "amber",
  unpaid: "neutral",
  overdue: "red",
};

export default function FeeCentrePage() {
  const { data, isLoading } = useMyFees();
  const downloadInvoice = useDownloadInvoice();

  if (isLoading || !data) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading fee status...</p>;
  }

  const nextDue = data.invoices
    .filter((i) => i.status !== "paid")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Fee Centre</h1>

      <Card>
        <div className="mb-1 flex items-center gap-2">
          <Wallet className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Outstanding Balance</p>
        </div>
        <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          {data.outstanding_balance.toFixed(2)}
        </p>
        {nextDue && <p className="text-sm text-slate-500 dark:text-slate-400">Due: {nextDue.due_date}</p>}
      </Card>

      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Payment History</h2>
      {data.payments.length === 0 ? (
        <EmptyState icon={Receipt} title="No payments recorded yet" />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2.5">Date</th>
                <th className="px-4 py-2.5">Amount</th>
              </tr>
            </thead>
            <tbody>
              {data.payments.map((payment) => (
                <tr
                  key={payment.payment_id}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-2.5">{new Date(payment.payment_date).toLocaleDateString()}</td>
                  <td className="px-4 py-2.5">{payment.amount.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Invoices</h2>
      {data.invoices.length === 0 ? (
        <EmptyState icon={Receipt} title="No invoices yet" />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="px-4 py-2.5">Amount</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Due Date</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {data.invoices.map((invoice) => (
                <tr
                  key={invoice.invoice_id}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-2.5">{invoice.amount.toFixed(2)}</td>
                  <td className="px-4 py-2.5">
                    <Badge tone={invoiceStatusTone[invoice.status]}>{invoice.status.replace("_", " ")}</Badge>
                  </td>
                  <td className="px-4 py-2.5">{invoice.due_date}</td>
                  <td className="px-4 py-2.5">
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Download className="h-3 w-3" aria-hidden="true" />}
                      onClick={() => downloadInvoice.mutate(invoice.invoice_id)}
                      isLoading={downloadInvoice.isPending}
                    >
                      Download
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
