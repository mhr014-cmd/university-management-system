// Shared searchable dropdown selector (Version 2.3 — Academic Setup).
// Client-side filtered combobox over an already-fetched option list —
// replaces raw-UUID text inputs across Admin forms with a type-to-filter,
// click-to-select control. No new backend search endpoint: this
// project's reference/user lists are fetched in full and filtered in the
// browser, matching the existing page_size=100 precedent already used
// elsewhere (e.g. useStudents(undefined, 1, 100) in Admin/Reports).
//
// Deliberately not a native <select> — the whole point is a type-ahead
// filter over lists too long to scan by eye (courses, rooms, students),
// which a native <select> doesn't support. Required-ness is left to the
// parent form's own submit-time check (this codebase's established
// pattern, e.g. FeeDashboard's disabled={!fsDepartmentId || ...}) rather
// than a native HTML `required` attribute, since there's no plain form
// control here for the browser to validate.
//
// Keyboard support (Version 2.3 polish pass): Escape closes, ArrowUp/Down
// move a virtual highlight over the filtered list, Enter selects the
// highlighted option. Focus deliberately stays on the search input rather
// than moving to individual option buttons — the highlight is tracked in
// state and exposed via aria-activedescendant, avoiding a separate
// roving-tabindex implementation for what is otherwise a small control.

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { inputClass } from "./classNames";

export interface SearchableSelectOption {
  value: string;
  label: string;
}

interface SearchableSelectProps {
  options: SearchableSelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  id?: string;
  disabled?: boolean;
}

function optionDomId(baseId: string | undefined, value: string): string {
  return `${baseId ?? "searchable-select"}-option-${value}`;
}

export function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = "Select...",
  id,
  disabled,
}: SearchableSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const selected = options.find((option) => option.value === value);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered =
    query.trim().length === 0
      ? options
      : options.filter((option) => option.label.toLowerCase().includes(query.trim().toLowerCase()));

  useEffect(() => {
    setHighlightedIndex(0);
  }, [query, open]);

  function openList() {
    setOpen(true);
  }

  function closeList() {
    setOpen(false);
    setQuery("");
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Enter") {
      event.preventDefault();
      openList();
    }
  }

  function handleSearchKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightedIndex((i) => (filtered.length === 0 ? 0 : Math.min(i + 1, filtered.length - 1)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightedIndex((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      const option = filtered[highlightedIndex];
      if (option) {
        onChange(option.value);
        closeList();
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      closeList();
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        id={id}
        disabled={disabled}
        onClick={() => (open ? closeList() : openList())}
        onKeyDown={handleTriggerKeyDown}
        className={`flex w-full items-center justify-between ${inputClass}`}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className={selected ? "" : "text-slate-400 dark:text-slate-500"}>
          {selected ? selected.label : placeholder}
        </span>
        <ChevronsUpDown className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
      </button>

      {open && (
        <div className="absolute z-20 mt-1 w-full rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Type to search..."
            role="combobox"
            aria-expanded={open}
            aria-controls="searchable-select-listbox"
            aria-activedescendant={filtered[highlightedIndex] ? optionDomId(id, filtered[highlightedIndex].value) : undefined}
            className={`m-1.5 w-[calc(100%-0.75rem)] ${inputClass}`}
          />
          <ul id="searchable-select-listbox" role="listbox" className="max-h-56 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <li className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">No matches</li>
            ) : (
              filtered.map((option, index) => (
                <li key={option.value}>
                  <button
                    type="button"
                    id={optionDomId(id, option.value)}
                    role="option"
                    aria-selected={option.value === value}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    onClick={() => {
                      onChange(option.value);
                      setQuery("");
                      setOpen(false);
                    }}
                    className={`flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-800 ${
                      index === highlightedIndex ? "bg-slate-100 dark:bg-slate-800" : ""
                    }`}
                  >
                    {option.label}
                    {option.value === value && (
                      <Check className="h-4 w-4 text-slate-900 dark:text-slate-100" aria-hidden="true" />
                    )}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
