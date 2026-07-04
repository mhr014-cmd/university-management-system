// Admin: Fee Dashboard page (FR-039, FR-040, FR-043). Layout matches
// docs/UI_Wireframes.md Section 12: summary stat cards, New Fee
// Structure / Record Payment forms, overdue accounts table.
//
// Known simplification: the wireframe's "Notify"/"Send Bulk Overdue
// Notice" actions (FR-056, POST /fees/overdue/notify) are explicitly
// deferred to Milestone 9 per Implementation_Roadmap.md's own Milestone 8
// note — that endpoint writes to the `notification` table, which doesn't
// exist until Milestone 9. Not built here, same pattern as Milestone 6's
// Grading Interface deliberately omitting "Submit Results for Approval".

import { useState } from "react";
import { isAxiosError } from "axios";
import { useDepartments } from "../../../features/departments";
import { useSemesters } from "../../../features/semesters";
import { useStudents } from "../../../features/users";
import {
  useCreateFeeStructure,
  useOverdueAccounts,
  useRecordPayment,
} from "../../../features/fees";

export default function FeeDashboardPage() {
  const { data: departments } = useDepartments();
  const { data: semesters } = useSemesters();
  const { data: students } = useStudents(undefined, 1, 100);
  const { data: overdue, isLoading: isOverdueLoading } = useOverdueAccounts();
  const createFeeStructure = useCreateFeeStructure();
  const recordPayment = useRecordPayment();

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

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Fee Dashboard</h1>

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
        <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400">Outstanding (Overdue)</p>
          <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">{totalOutstanding.toFixed(2)}</p>
        </div>
        <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400">Overdue Accounts</p>
          <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            {overdue?.overdue_accounts.length ?? 0}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="space-y-2 rounded border border-slate-200 p-4 dark:border-slate-700">
          <h2 className="text-lg font-medium text-slate-900 dark:text-slate-100">New Fee Structure</h2>
          <select
            value={fsDepartmentId}
            onChange={(e) => setFsDepartmentId(e.target.value)}
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          >
            <option value="">University-wide (all departments)</option>
            {departments?.items.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <select
            value={fsSemesterId}
            onChange={(e) => setFsSemesterId(e.target.value)}
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          >
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
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <input
            type="number"
            min={0.01}
            step={0.01}
            value={fsAmount}
            onChange={(e) => setFsAmount(e.target.value)}
            placeholder="Amount"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <input
            type="date"
            value={fsDueDate}
            onChange={(e) => setFsDueDate(e.target.value)}
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <button
            type="button"
            onClick={handleCreateFeeStructure}
            disabled={!fsSemesterId || !fsName || !fsAmount || !fsDueDate || createFeeStructure.isPending}
            className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
          >
            Create Fee Structure
          </button>
        </div>

        <div className="space-y-2 rounded border border-slate-200 p-4 dark:border-slate-700">
          <h2 className="text-lg font-medium text-slate-900 dark:text-slate-100">Record Payment</h2>
          <select
            value={payStudentId}
            onChange={(e) => setPayStudentId(e.target.value)}
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          >
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
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <input
            type="number"
            min={0.01}
            step={0.01}
            value={payAmount}
            onChange={(e) => setPayAmount(e.target.value)}
            placeholder="Amount"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <input
            type="datetime-local"
            value={payDate}
            onChange={(e) => setPayDate(e.target.value)}
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <input
            type="text"
            value={payMethod}
            onChange={(e) => setPayMethod(e.target.value)}
            placeholder="Payment method (optional)"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <button
            type="button"
            onClick={handleRecordPayment}
            disabled={!payStudentId || !payFeeStructureId || !payAmount || !payDate || recordPayment.isPending}
            className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
          >
            Record Payment
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-medium text-slate-900 dark:text-slate-100">Overdue Accounts</h2>
        {isOverdueLoading || !overdue ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading...</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="py-2">Student ID</th>
                <th className="py-2">Amount Due</th>
                <th className="py-2">Days Overdue</th>
              </tr>
            </thead>
            <tbody>
              {overdue.overdue_accounts.map((account) => (
                <tr key={account.invoice_id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2">{account.student_id}</td>
                  <td className="py-2">{account.amount_due.toFixed(2)}</td>
                  <td className="py-2">{account.days_overdue}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {overdue && overdue.overdue_accounts.length === 0 && (
          <p className="text-sm text-slate-500 dark:text-slate-400">No overdue accounts.</p>
        )}
      </div>
    </div>
  );
}
