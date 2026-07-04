// Root error boundary (Milestone 11 hardening — see
// docs/System_Architecture.md §10). React error boundaries must be class
// components — there is no hooks-based equivalent for
// getDerivedStateFromError/componentDidCatch.

import { Component, type ErrorInfo, type ReactNode } from "react";
import { reportClientError } from "../lib/reportClientError";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: unknown, info: ErrorInfo): void {
    reportClientError(error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-white p-6 text-center dark:bg-slate-900">
          <div>
            <h1 className="mb-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
              Something went wrong.
            </h1>
            <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
              This has been reported. Try reloading the page.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white dark:bg-slate-100 dark:text-slate-900"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
