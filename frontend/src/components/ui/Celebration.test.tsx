import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Celebration } from "@/components/ui/Celebration";

afterEach(() => {
  vi.useRealTimers();
});

describe("Celebration", () => {
  it("announces the milestone and dismisses once on tap", () => {
    const onDone = vi.fn();
    render(<Celebration title="You're now ID checked" detail="Clients see it" onDone={onDone} />);

    expect(screen.getByRole("status")).toHaveTextContent("You're now ID checked");
    fireEvent.click(screen.getByRole("button", { name: /ID checked/ }));
    fireEvent.click(screen.getByRole("button", { name: /ID checked/ }));
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  it("dismisses itself so it never lingers over the screen", () => {
    vi.useFakeTimers();
    const onDone = vi.fn();
    render(<Celebration title="Job signed off" detail="Thanks" onDone={onDone} />);

    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  it("shows a static badge when motion is unavailable", () => {
    const { container } = render(<Celebration title="Done" detail="" onDone={() => undefined} />);
    expect(container.querySelector(".celebration__badge")).not.toBeNull();
  });
});
