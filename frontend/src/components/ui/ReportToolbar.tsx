// Shared report export toolbar (Version 1.2 reporting infrastructure).
// Print | PDF | Excel actions for any report page — Attendance Reports is
// the reference implementation; Results/Fees/Timetable/Users report
// pages should reuse this component rather than hand-rolling their own
// export buttons.

import { FileSpreadsheet, FileText, Printer } from "lucide-react";
import { usePrint } from "../../lib/usePrint";
import { Button } from "./Button";

interface ReportToolbarProps {
  onPrint?: () => void;
  onExportPdf: () => void;
  onExportExcel: () => void;
  isExportingPdf?: boolean;
  isExportingExcel?: boolean;
  // Optional — added for the Parent Attendance export (production-
  // readiness audit gap closure). Omitted by every pre-existing caller
  // (Admin Reports), so this stays backward compatible.
  onExportCsv?: () => void;
  isExportingCsv?: boolean;
}

export function ReportToolbar({
  onPrint,
  onExportPdf,
  onExportExcel,
  isExportingPdf,
  isExportingExcel,
  onExportCsv,
  isExportingCsv,
}: ReportToolbarProps) {
  const defaultPrint = usePrint();

  return (
    <div className="flex items-center gap-2" data-print-hidden>
      <Button
        variant="secondary"
        size="sm"
        icon={<Printer className="h-3.5 w-3.5" aria-hidden="true" />}
        onClick={onPrint ?? defaultPrint}
      >
        Print
      </Button>
      <Button
        variant="secondary"
        size="sm"
        icon={<FileText className="h-3.5 w-3.5" aria-hidden="true" />}
        onClick={onExportPdf}
        isLoading={isExportingPdf}
      >
        PDF
      </Button>
      <Button
        variant="secondary"
        size="sm"
        icon={<FileSpreadsheet className="h-3.5 w-3.5" aria-hidden="true" />}
        onClick={onExportExcel}
        isLoading={isExportingExcel}
      >
        Excel
      </Button>
      {onExportCsv && (
        <Button
          variant="secondary"
          size="sm"
          icon={<FileSpreadsheet className="h-3.5 w-3.5" aria-hidden="true" />}
          onClick={onExportCsv}
          isLoading={isExportingCsv}
        >
          CSV
        </Button>
      )}
    </div>
  );
}
