// Shared Tailwind class fragments (production-polish pass). For pages that
// keep a plain <input>/<select>/<label> rather than adopting a full
// component, importing these keeps focus/placeholder/disabled treatment
// consistent across the app without a page-by-page one-off className.

export const inputClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-400 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-slate-500 dark:disabled:bg-slate-800/50 dark:disabled:text-slate-600";

export const labelClass = "mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300";

export const helperTextClass = "mt-1 text-xs text-slate-500 dark:text-slate-400";

export const errorTextClass = "mt-1 text-xs text-red-600 dark:text-red-400";
