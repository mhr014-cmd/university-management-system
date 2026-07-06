// Shared print trigger (Version 1.2 reporting infrastructure). Wraps
// window.print() so ReportToolbar has a sensible default `onPrint`
// without every report page needing to know this is just a native
// browser call — printing itself needs no backend request, unlike the
// PDF/Excel exports (see lib/exportClient.ts).
export function usePrint(): () => void {
  return () => window.print();
}
