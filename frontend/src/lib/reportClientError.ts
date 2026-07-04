// Client-side error reporting (Milestone 11 hardening — see
// docs/System_Architecture.md §10: "Client-side errors ... are captured
// via an error boundary and reported to a central location distinct from
// routine console output, so production issues are visible without
// depending on user bug reports.")
//
// This project has no backend endpoint to receive client error reports
// (adding one would be new business functionality, out of Milestone 11's
// scope), so "central location" here means a single, distinctly-tagged
// choke point — every uncaught render error funnels through this one
// function rather than being logged ad hoc wherever it's caught. A real
// deployment wiring this to a remote error-tracking service would only
// need to change this one function.

export function reportClientError(error: unknown, info?: { componentStack?: string | null }): void {
  console.error("[client-error]", error, info?.componentStack ?? "");
}
