// React Query hooks: fees (status, structures, payments, invoices)
// See docs/API_Contract.md Section 6.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export type InvoiceStatus = "unpaid" | "partially_paid" | "paid" | "overdue";

export interface InvoiceEntry {
  invoice_id: string;
  amount: number;
  status: InvoiceStatus;
  due_date: string;
}

export interface PaymentEntry {
  payment_id: string;
  amount: number;
  payment_date: string;
}

export interface FeesMeResponse {
  student_id: string;
  outstanding_balance: number;
  invoices: InvoiceEntry[];
  payments: PaymentEntry[];
}

export interface FeeStructureCreateInput {
  department_id?: string;
  semester_id: string;
  name: string;
  amount: number;
  due_date: string;
}

export interface FeeStructureRead {
  id: string;
  department_id: string | null;
  semester_id: string;
  name: string;
  amount: number;
  due_date: string;
  created_at: string;
  invoices_created: number;
}

export interface PaymentCreateInput {
  student_id: string;
  fee_structure_id: string;
  amount: number;
  payment_date: string;
  payment_method?: string;
}

export interface PaymentRead {
  payment_id: string;
  amount: number;
  payment_date: string;
  fee_structure_id: string;
}

export interface PaymentHistoryResponse {
  student_id: string;
  payments: PaymentRead[];
}

export interface OverdueAccountEntry {
  student_id: string;
  invoice_id: string;
  amount_due: number;
  due_date: string;
  days_overdue: number;
}

export interface OverdueResponse {
  overdue_accounts: OverdueAccountEntry[];
}

export function useMyFees(params?: { semesterId?: string; studentId?: string }) {
  return useQuery({
    queryKey: ["fees", "me", params],
    queryFn: async () =>
      (
        await apiClient.get<FeesMeResponse>("/fees/me", {
          params: { semester_id: params?.semesterId, student_id: params?.studentId },
        })
      ).data,
  });
}

export function useCreateFeeStructure() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: FeeStructureCreateInput) =>
      (await apiClient.post<FeeStructureRead>("/fees", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fees"] });
    },
  });
}

export function useRecordPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PaymentCreateInput) =>
      (await apiClient.post<PaymentRead>("/fees/payments", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fees"] });
    },
  });
}

export function usePaymentHistory(studentId?: string) {
  return useQuery({
    queryKey: ["fees", "payments", studentId],
    queryFn: async () => (await apiClient.get<PaymentHistoryResponse>(`/fees/payments/${studentId}`)).data,
    enabled: Boolean(studentId),
  });
}

export function useOverdueAccounts(params?: { departmentId?: string; semesterId?: string }) {
  return useQuery({
    queryKey: ["fees", "overdue", params],
    queryFn: async () =>
      (
        await apiClient.get<OverdueResponse>("/fees/overdue", {
          params: { department_id: params?.departmentId, semester_id: params?.semesterId },
        })
      ).data,
  });
}

export function useDownloadInvoice() {
  return useMutation({
    mutationFn: async (invoiceId: string) => {
      const response = await apiClient.get(`/fees/invoices/${invoiceId}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "invoice.pdf";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
  });
}
