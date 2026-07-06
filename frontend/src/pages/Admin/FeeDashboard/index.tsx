// Admin: Fee Dashboard page (FR-039, FR-040, FR-043, FR-056). Layout
// matches docs/UI_Wireframes.md Section 12: summary stat cards, New Fee
// Structure / Record Payment forms, overdue accounts table with per-row
// Notify and a Send Bulk Overdue Notice action.
//
// The "Notify"/"Send Bulk Overdue Notice" actions (FR-056,
// POST /fees/overdue/notify) were deferred past Milestone 8 since that
// endpoint writes to the `notification` table, which didn't exist until
// Milestone 9 — implemented now in Milestone 10 alongside the rest of the
// Reporting module. Reuses the existing Notification Dispatcher; no
// second notification system.

import { useState } from "react";
import { isAxiosError } from "axios";
import { AlertTriangle, CheckCircle2, Download, Send, Wallet } from "lucide-react";
import { useDepartments } from "../../../features/departments";
import { useSemesters } from "../../../features/semesters";
import { useStudents } from "../../../features/users";
import {
  useCreateFeeStructure,
  useDownloadInvoice,
  useNotifyOverdueAccounts,
  useOverdueAccounts,
  useRecordPayment,
} from "../../../features/fees";
import { Button } from "../../../components/ui/Button";
import { Card, CardTitle } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { PageLoader } from "../../../components/ui/PageLoader";
import { inputClass } from "../../../components/ui/classNames";

export default function FeeDashboardPage() {
  const { data: departments } = useDepartments();
  const { data: semesters } = useSemesters();
  const { data: students } = useStudents(undefined, 1, 100);
  const { data: overdue, isLoading: isOverdueLoading } = useOverdueAccounts();
  const createFeeStructure = useCreateFeeStructure();
  const recordPayment = useRecordPayment();
  const notifyOverdue = useNotifyOverdueAccounts();
  const downloadInvoice = useDownloadInvoice();

  const [fsDepartmentId, setFsDepartmentId] = useState("");
  const [fsSemesterId, setFsSemesterId] = useState("");
  const [fsName, setFsName] = useState("");
  const [fsAmount, setFsAmount] = useState("");
  const [fsDueDate, setFsDueDate] = useState("");

  const [payStudentId, setPayStudentId] = useState("");
  const [payFeeStructureId, setPayFeeStructureId] = useState("");
  const [payAmount, setPayAmount] = useState("");
  const [payDate, setPayDate] = useState("");
  const [payMethod, setPayMethod] = useState("");

  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCreateFeeStructure = async () => {
    setMessage(null);
    setError(null);
    try {
      const result = await createFeeStructure.mutateAsync({
        department_id: fsDepartmentId || undefined,
        semester_id: fsSemesterId,
        name: fsName,
        amount: Number(fsAmount),
        due_date: fsDueDate,
      });
      setMessage(`Fee structure created — ${result.invoices_created} invoice(s) generated.`);
      setFsName("");
      setFsAmount("");
      setFsDueDate("");
    } catch {
      setError("Could not create fee structure. Please check the fields and try again.");
    }
  };

  const handleRecordPayment = async () => {
    setMessage(null);
    setError(null);
    try {
      await recordPayment.mutateAsync({
        student_id: payStudentId,
        fee_structure_id: payFeeStructureId,
        amount: Number(payAmount),
        payment_date: payDate,
        payment_method: payMethod || undefined,
      });
      setMessage("Payment recorded.");
      setPayAmount("");
      setPayDate("");
      setPayMethod("");
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setError(err.response.data?.error?.message ?? "Payment exceeds the outstanding balance or invoice is fully paid.");
      } else {
        setError("Could not record payment. Please check the fields and try again.");
      }
    }
  };

  const totalOutstanding = (overdue?.overdue_accounts ?? []).reduce((sum, a) => sum + a.amount_due, 0);

  const handleNotify = async (studentId: string) => {
    setMessage(null);
    setError(null);
    try {
      const result = await notifyOverdue.mutateAsync({ student_ids: [studentId], scope: "selected" });
      setMessage(`Notified ${result.notified_count} account(s).`);
    } catch {
      setError("Could not send the overdue notice. Please try again.");
    }
  };

  const handleBulkNotify = async () => {
    if (!window.confirm("Send an overdue notice to every currently overdue account?")) return;
    setMessage(null);
    setError(null);
    try {
      const result = await notifyOverdue.mutateAsync({ student_ids: [], scope: "all_overdue" });
      setMessage(`Notified ${result.notified_count} account(s).`);
    } catch {
      setError("Could not send bulk overdue notices. Please try again.");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Fee Dashboard</h1>

      {message && (
        <div className="rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
          {message}
        </div>
      )}
      {error && (
        <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <div className="mb-1 flex items-center gap-2">
            <Wallet className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
            <p className="text-sm text-slate-500 dark:text-slate-400">Outstanding (Overdue)</p>
          </div>
          <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">{totalOutstanding.toFixed(2)}</p>
        </Card>
        <Card>
          <div className="mb-1 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
            <p className="text-sm text-slate-500 dark:text-slate-400">Overdue Accounts</p>
          </div>
          <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            {overdue?.overdue_accounts.length ?? 0}
          </p>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card className="space-y-3">
          <CardTitle>New Fee Structure</CardTitle>
          <select
            value={fsDepartmentId}
            onChange={(e) => setFsDepartmentId(e.target.value)}
            className={inputClass}
          >
            <option value="">University-wide (all departments)</option>
            {departments?.items.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <select value={fsSemesterId} onChange={(e) => setFsSemesterId(e.target.value)} className={inputClass}>
            <option value="">Select Semester</option>
            {semesters?.items.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={fsName}
            onChange={(e) => setFsName(e.target.value)}
            placeholder="Fee name (e.g. Tuition Fee)"
            className={inputClass}
          />
          <input
            type="number"
            min={0.01}
            step={0.01}
            value={fsAmount}
            onChange={(e) => setFsAmount(e.target.value)}
            placeholder="Amount"
            className={inputClass}
          />
          <input type="date" value={fsDueDate} onChange={(e) => setFsDueDate(e.target.value)} className={inputClass} />
          <Button
            onClick={handleCreateFeeStructure}
            disabled={!fsSemesterId || !fsName || !fsAmount || !fsDueDate}
            isLoading={createFeeStructure.isPending}
          >
            Create Fee Structure
          </Button>
        </Card>

        <Card className="space-y-3">
          <CardTitle>Record Payment</CardTitle>
          <select value={payStudentId} onChange={(e) => setPayStudentId(e.target.value)} className={inputClass}>
            <option value="">Select Student</option>
            {students?.items.map((s) => (
              <option key={s.id} value={s.id}>
                {s.first_name} {s.last_name}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={payFeeStructureId}
            onChange={(e) => setPayFeeStructureId(e.target.value)}
            placeholder="Fee Structure ID"
            className={inputClass}
          />
          <input
            type="number"
            min={0.01}
            step={0.01}
            value={payAmount}
            onChange={(e) => setPayAmount(e.target.value)}
            placeholder="Amount"
            className={inputClass}
          />
          <input type="datetime-local" value={payDate} onChange={(e) => setPayDate(e.target.value)} className={inputClass} />
          <input
            type="text"
            value={payMethod}
            onChange={(e) => setPayMethod(e.target.value)}
            placeholder="Payment method (optional)"
            className={inputClass}
          />
          <Button
            onClick={handleRecordPayment}
            disabled={!payStudentId || !payFeeStructureId || !payAmount || !payDate}
            isLoading={recordPayment.isPending}
          >
            Record Payment
          </Button>
        </Card>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Overdue Accounts</h2>
          <Button
            variant="secondary"
            size="sm"
            icon={<Send className="h-3.5 w-3.5" aria-hidden="true" />}
            onClick={() => void handleBulkNotify()}
            disabled={!overdue?.overdue_accounts.length}
            isLoading={notifyOverdue.isPending}
          >
            Send Bulk Overdue Notice
          </Button>
        </div>
        {isOverdueLoading || !overdue ? (
          <PageLoader />
        ) : overdue.overdue_accounts.length === 0 ? (
          <EmptyState icon={CheckCircle2} title="No overdue accounts" description="Every student is current on their fees." />
        ) : (
          <Card className="overflow-x-auto p-0">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 z-[1] bg-white dark:bg-slate-800/50">
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-4 py-2.5">Student</th>
                  <th className="px-4 py-2.5">Amount Due</th>
                  <th className="px-4 py-2.5">Days Overdue</th>
                  <th className="px-4 py-2.5"></th>
                  <th className="px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                {overdue.overdue_accounts.map((account) => (
                  <tr
                    key={account.invoice_id}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                  >
                    <td className="px-4 py-2.5">{account.student_name}</td>
                    <td className="px-4 py-2.5">{account.amount_due.toFixed(2)}</td>
                    <td className="px-4 py-2.5">{account.days_overdue}</td>
                    <td className="px-4 py-2.5">
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={<Send className="h-3 w-3" aria-hidden="true" />}
                        onClick={() => handleNotify(account.student_id)}
                        isLoading={notifyOverdue.isPending}
                      >
                        Notify
                      </Button>
                    </td>
                    <td className="px-4 py-2.5">
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={<Download className="h-3 w-3" aria-hidden="true" />}
                        onClick={() => downloadInvoice.mutate(account.invoice_id)}
                        isLoading={downloadInvoice.isPending}
                      >
                        Invoice
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </div>
    </div>
  );
}
