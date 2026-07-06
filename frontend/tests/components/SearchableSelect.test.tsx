// Component test: shared SearchableSelect (Version 2.3 — Academic Setup).
// Verifies the type-to-filter dropdown behavior that replaces raw-UUID
// text inputs across Admin forms.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SearchableSelect } from "../../src/components/ui/SearchableSelect";

const options = [
  { value: "1", label: "Computer Science" },
  { value: "2", label: "Business Administration" },
  { value: "3", label: "Civil Engineering" },
];

describe("SearchableSelect", () => {
  it("shows the placeholder when no value is selected", () => {
    render(<SearchableSelect options={options} value="" onChange={vi.fn()} placeholder="Select Department" />);
    expect(screen.getByRole("button", { name: "Select Department" })).toBeInTheDocument();
  });

  it("shows the selected option's label when a value is set", () => {
    render(<SearchableSelect options={options} value="2" onChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Business Administration" })).toBeInTheDocument();
  });

  it("opens the option list on click and lists every option", async () => {
    const user = userEvent.setup();
    render(<SearchableSelect options={options} value="" onChange={vi.fn()} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));

    expect(screen.getByRole("option", { name: "Computer Science" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Business Administration" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Civil Engineering" })).toBeInTheDocument();
  });

  it("filters options by typed text", async () => {
    const user = userEvent.setup();
    render(<SearchableSelect options={options} value="" onChange={vi.fn()} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    await user.type(screen.getByPlaceholderText("Type to search..."), "civil");

    expect(screen.getByRole("option", { name: "Civil Engineering" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Computer Science" })).not.toBeInTheDocument();
  });

  it("shows a no-matches message when nothing filters through", async () => {
    const user = userEvent.setup();
    render(<SearchableSelect options={options} value="" onChange={vi.fn()} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    await user.type(screen.getByPlaceholderText("Type to search..."), "zzz-no-match");

    expect(screen.getByText("No matches")).toBeInTheDocument();
  });

  it("calls onChange and closes the list when an option is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SearchableSelect options={options} value="" onChange={onChange} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    await user.click(screen.getByRole("option", { name: "Civil Engineering" }));

    expect(onChange).toHaveBeenCalledWith("3");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("is disabled when the disabled prop is set", () => {
    render(<SearchableSelect options={options} value="" onChange={vi.fn()} disabled placeholder="Select Department" />);
    expect(screen.getByRole("button", { name: "Select Department" })).toBeDisabled();
  });

  it("opens the list when ArrowDown is pressed on the closed trigger", async () => {
    const user = userEvent.setup();
    render(<SearchableSelect options={options} value="" onChange={vi.fn()} placeholder="Select Department" />);

    screen.getByRole("button", { name: "Select Department" }).focus();
    await user.keyboard("{ArrowDown}");

    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });

  it("closes the list when Escape is pressed", async () => {
    const user = userEvent.setup();
    render(<SearchableSelect options={options} value="" onChange={vi.fn()} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    expect(screen.getByRole("listbox")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("selects the first option with Enter when the list first opens, without a click", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SearchableSelect options={options} value="" onChange={onChange} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    // Opening the list highlights the first option (Computer Science) by default.
    await user.keyboard("{Enter}");

    expect(onChange).toHaveBeenCalledWith("1");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("moves the highlight down with ArrowDown before selecting", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SearchableSelect options={options} value="" onChange={onChange} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    await user.keyboard("{ArrowDown}"); // highlight moves from Computer Science (0) to Business Administration (1)
    await user.keyboard("{Enter}");

    expect(onChange).toHaveBeenCalledWith("2");
  });

  it("moves the highlight down twice then up twice, ending back on the first option", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SearchableSelect options={options} value="" onChange={onChange} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    await user.keyboard("{ArrowDown}{ArrowDown}{ArrowUp}{ArrowUp}");
    await user.keyboard("{Enter}");

    expect(onChange).toHaveBeenCalledWith("1");
  });

  it("does not move the highlight above the first option", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SearchableSelect options={options} value="" onChange={onChange} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    await user.keyboard("{ArrowUp}{ArrowUp}"); // already at index 0; should clamp, not go negative
    await user.keyboard("{Enter}");

    expect(onChange).toHaveBeenCalledWith("1");
  });

  it("still supports mouse click to select after keyboard navigation", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SearchableSelect options={options} value="" onChange={onChange} placeholder="Select Department" />);

    await user.click(screen.getByRole("button", { name: "Select Department" }));
    await user.keyboard("{ArrowDown}");
    await user.click(screen.getByRole("option", { name: "Civil Engineering" }));

    expect(onChange).toHaveBeenCalledWith("3");
  });
});
