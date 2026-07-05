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

import { InvoiceStatus, useMyFees, useDownloadInvoice } from "../../features/fees";

const invoiceStatusStyles: Record<InvoiceStatus, string> = {
  paid: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300",
  partially_paid: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  unpaid: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  overdue: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
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
      <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Fee Centre</h1>

      <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
        <p className="text-sm text-slate-500 dark:text-slate-400">Outstanding Balance</p>
        <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          {data.outstanding_balance.toFixed(2)}
        </p>
        {nextDue && <p className="text-sm text-slate-500 dark:text-slate-400">Due: {nextDue.due_date}</p>}
      </div>

      <h2 className="text-lg font-medium text-slate-900 dark:text-slate-100">Payment History</h2>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="py-2">Date</th>
            <th className="py-2">Amount</th>
          </tr>
        </thead>
        <tbody>
          {data.payments.map((payment) => (
            <tr
              key={payment.payment_id}
              className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
            >
              <td className="py-2">{new Date(payment.payment_date).toLocaleDateString()}</td>
              <td className="py-2">{payment.amount.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.payments.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">No payments recorded yet.</p>
      )}

      <h2 className="text-lg font-medium text-slate-900 dark:text-slate-100">Invoices</h2>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="py-2">Amount</th>
            <th className="py-2">Status</th>
            <th className="py-2">Due Date</th>
            <th className="py-2"></th>
          </tr>
        </thead>
        <tbody>
          {data.invoices.map((invoice) => (
            <tr
              key={invoice.invoice_id}
              className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
            >
              <td className="py-2">{invoice.amount.toFixed(2)}</td>
              <td className="py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${invoiceStatusStyles[invoice.status]}`}
                >
                  {invoice.status.replace("_", " ")}
                </span>
              </td>
              <td className="py-2">{invoice.due_date}</td>
              <td className="py-2">
                <button
                  type="button"
                  onClick={() => downloadInvoice.mutate(invoice.invoice_id)}
                  disabled={downloadInvoice.isPending}
                  className="rounded border border-slate-300 px-2 py-1 text-xs disabled:opacity-50 dark:border-slate-600"
                >
                  Download
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.invoices.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">No invoices yet.</p>
      )}
    </div>
  );
}
