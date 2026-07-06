// Shared report export client (Version 1.2 reporting infrastructure).
//
// Centralizes the "request a file from the backend, then trigger a
// browser download" behavior so future report modules (Results, Fees,
// Timetable, Users) reuse this instead of each re-implementing the same
// blob/Content-Disposition/anchor-click dance. Generalizes the pattern
// previously hand-rolled once-off in features/fees's useDownloadInvoice.

import { apiClient } from "./apiClient";

export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export function filenameFromContentDisposition(header: string | undefined | null): string | undefined {
  if (!header) return undefined;
  const match = /filename="?([^";]+)"?/.exec(header);
  return match?.[1];
}

// Requests `path` with `params` as a blob, then triggers a browser
// download using the server-supplied filename (Content-Disposition) when
// present, falling back to `fallbackFilename` otherwise.
export async function exportReport(
  path: string,
  params: Record<string, string | undefined>,
  fallbackFilename: string,
): Promise<void> {
  const response = await apiClient.get<Blob>(path, { params, responseType: "blob" });
  const filename = filenameFromContentDisposition(response.headers["content-disposition"]) ?? fallbackFilename;
  downloadBlob(response.data, filename);
}
