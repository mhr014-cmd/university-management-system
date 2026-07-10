// Shared report export client (Version 1.2 reporting infrastructure).
//
// Centralizes the "request a file from the backend, then trigger a
// browser download" behavior so future report modules (Results, Fees,
// Timetable, Users) reuse this instead of each re-implementing the same
// blob/anchor-click dance. Generalizes the pattern previously
// hand-rolled once-off in features/fees's useDownloadInvoice.
//
// Every generated-file endpoint returns a base64 JSON envelope
// (`{filename, content_type, data_base64}`), not a raw
// application/pdf/.xlsx/.csv response — see backend/app/core/
// file_response.py's docstring. Live runtime debugging traced a real
// bug: a raw binary response, even fetched via an authenticated
// XHR-blob request, was still intercepted at the network layer by
// third-party download managers (e.g. IDM's "Advanced Browser
// Integration"), which re-request the URL themselves without the
// JS-held bearer token — producing a spurious 401 and the download
// manager's own credential prompt, regardless of Content-Disposition.
// Wrapping the bytes in `application/json` removes the signal those
// tools key off entirely.

import { apiClient } from "./apiClient";

interface FileEnvelope {
  filename: string;
  content_type: string;
  data_base64: string;
}

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

export function blobFromEnvelope(envelope: FileEnvelope): Blob {
  const binary = window.atob(envelope.data_base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: envelope.content_type });
}

// Requests `path` with `params`, decodes the base64 JSON envelope, then
// triggers a browser download using the server-supplied filename,
// falling back to `fallbackFilename` if it's ever missing.
export async function exportReport(
  path: string,
  params: Record<string, string | undefined>,
  fallbackFilename: string,
): Promise<void> {
  const response = await apiClient.get<FileEnvelope>(path, { params });
  downloadBlob(blobFromEnvelope(response.data), response.data.filename ?? fallbackFilename);
}
