import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TradePickerSheet } from "@/features/jobs/TradePickerSheet";

describe("TradePickerSheet", () => {
  it("picks a skill and confirms it", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const onClose = vi.fn();
    render(<TradePickerSheet isOpen selectedId={null} onClose={onClose} onSelect={onSelect} />);

    expect(screen.getByRole("dialog", { name: "Who do you need?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pick a skill" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Electrician" }));
    await user.click(screen.getByRole("button", { name: "Done — Electrician" }));

    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: "electrician", trade: "ELECTRICAL" }),
    );
    expect(onClose).toHaveBeenCalled();
  });

  it("shows skills the backend can't match yet as unavailable", () => {
    render(<TradePickerSheet isOpen selectedId={null} onClose={vi.fn()} onSelect={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Gardener/ })).toBeDisabled();
  });

  it("filters by search", async () => {
    const user = userEvent.setup();
    render(<TradePickerSheet isOpen selectedId={null} onClose={vi.fn()} onSelect={vi.fn()} />);
    await user.type(screen.getByRole("searchbox", { name: "Search skills" }), "sol");
    expect(screen.getByRole("button", { name: "Solar installer" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Plumber" })).not.toBeInTheDocument();
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<TradePickerSheet isOpen selectedId="plumber" onClose={onClose} onSelect={vi.fn()} />);
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });
});
