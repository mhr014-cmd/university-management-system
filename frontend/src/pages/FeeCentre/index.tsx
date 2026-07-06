// Fee Centre page (FR-038, FR-042). Layout matches docs/UI_Wireframes.md
// Section 8: outstanding balance card with due date, payment history
// table with per-row invoice download.
//
// Production-readiness audit gap closure: a dedicated Parent-facing page
// was previously unbuilt (Parent only had the outstanding-balance widget
// on ParentDashboard). This page now branches by role — same pattern
// already established by Timetable/index.tsx and ResultsView/index.tsx —
// reusing this exact layout/GET /fees/me and GET /fees/invoices/{id}
// (both already Parent-accessible) with a linked-child selector.

import { useEffect, useMemo, useState } from "react";
import { Download, Printer, Receipt, Users, Wallet } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { InvoiceStatus, useMyFees, useDownloadInvoice } from "../../features/fees";
import { useMyChildren } from "../../features/users";
import { usePrint } from "../../lib/usePrint";
import { Badge, type BadgeTone } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";
import { inputClass } from "../../components/ui/classNames";

const invoiceStatusTone: Record<InvoiceStatus, BadgeTone> = {
  paid: "green",
  partially_paid: "amber",
  unpaid: "neutral",
  overdue: "red",
};

export default function FeeCentrePage() {
  const { user } = useAuth();
  if (user?.role === "parent") {
    return <ParentFeeCentre />;
  }
  return <StudentFeeCentre />;
}

function FeesPanel({ studentId }: { studentId?: string }) {
  const { data, isLoading } = useMyFees({ studentId });
  const downloadInvoice = useDownloadInvoice();
  const print = usePrint();

  if (isLoading || !data) {
    return <PageLoader label="Loading fee status..." />;
  }

  const nextDue = data.invoices
    .filter((i) => i.status !== "paid")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];

  return (
    <div data-print-region className="space-y-4">
      <div className="flex justify-end" data-print-hidden>
        <Button variant="secondary" size="sm" icon={<Printer className="h-3.5 w-3.5" aria-hidden="true" />} onClick={print}>
          Print
        </Button>
      </div>

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
                <th className="px-4 py-2.5" data-print-hidden></th>
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
                  <td className="px-4 py-2.5" data-print-hidden>
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Download className="h-3 w-3" aria-hidden="true" />}
                      onClick={() => downloadInvoice.mutate(invoice.invoice_id)}
                      isLoading={downloadInvoice.isPending}
                    >
                      {invoice.status === "paid" ? "Download Receipt" : "Download Invoice"}
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

function StudentFeeCentre() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Fee Centre</h1>
      <FeesPanel />
    </div>
  );
}

function ParentFeeCentre() {
  const { data: childrenData, isLoading: childrenLoading, isError: childrenError } = useMyChildren();
  const children = useMemo(() => childrenData?.children ?? [], [childrenData]);
  const [selectedStudentId, setSelectedStudentId] = useState("");

  useEffect(() => {
    if (!selectedStudentId && children.length > 0) {
      setSelectedStudentId(children[0].id);
    }
  }, [children, selectedStudentId]);

  const selectedChild = children.find((c) => c.id === selectedStudentId);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Fee Centre</h1>

      <Card data-print-hidden>
        <div className="mb-2 flex items-center gap-2">
          <Users className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Linked Child</p>
        </div>
        {childrenLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading your linked children...</p>
        ) : childrenError ? (
          <p className="text-sm text-red-600 dark:text-red-400">Unable to load linked children.</p>
        ) : children.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No children linked yet"
            description="Contact an administrator to link a child's record to your account."
          />
        ) : (
          <select
            value={selectedStudentId}
            onChange={(e) => setSelectedStudentId(e.target.value)}
            className={inputClass}
          >
            {children.map((child) => (
              <option key={child.id} value={child.id}>
                {child.first_name} {child.last_name}
              </option>
            ))}
          </select>
        )}
      </Card>

      {selectedStudentId && selectedChild && (
        <>
          <p className="text-sm text-slate-500 dark:text-slate-400" data-print-hidden>
            Viewing fees for:{" "}
            <span className="font-medium text-slate-900 dark:text-slate-100">
              {selectedChild.first_name} {selectedChild.last_name}
            </span>
          </p>
          <FeesPanel studentId={selectedStudentId} />
        </>
      )}
    </div>
  );
}
