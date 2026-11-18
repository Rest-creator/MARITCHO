import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HowItWorks } from "@/features/onboarding/HowItWorks";

/*
 * jsdom has no matchMedia, so these run the no-download path (reduced
 * motion / Data Saver / old WebView): same scene and captions, no Theatre.
 */

function jobCardTransform(container: HTMLElement): string | null | undefined {
  return container.querySelector(".hiw-card")?.parentElement?.getAttribute("transform");
}

function stage(container: HTMLElement): Element {
  const element: Element | null = container.querySelector(".hiw-stage");
  if (element === null) throw new Error("stage missing");
  return element;
}

describe("HowItWorks (static)", () => {
  it("starts on the first chapter with the job card centred", () => {
    const { container } = render(<HowItWorks />);

    expect(screen.getByText("Post the job")).toBeInTheDocument();
    expect(screen.getByText("1 of 4")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Back" })).toBeDisabled();
    expect(jobCardTransform(container)).toBe("translate(160 64) scale(1)");
  });

  it("steps forward with Next and poses the scene for that chapter", () => {
    const { container } = render(<HowItWorks />);
    fireEvent.click(screen.getByRole("button", { name: /Next/ }));

    expect(screen.getByText("Get prices")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Step 2: Get prices" })).toHaveAttribute(
      "aria-current",
      "step",
    );
    expect(jobCardTransform(container)).toBe("translate(92 40) scale(0.72)");
  });

  it("jumps straight to a chapter from its dot", () => {
    render(<HowItWorks />);
    fireEvent.click(screen.getByRole("button", { name: "Step 4: Sign off" }));

    expect(
      screen.getByText("Confirm and pay. Every job builds the worker's record."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Next/ })).toBeDisabled();
  });

  it("changes chapter with a swipe, and ignores a small wobble", () => {
    const { container } = render(<HowItWorks />);
    const target: Element = stage(container);

    fireEvent.pointerDown(target, { pointerId: 1, clientX: 200, button: 0 });
    fireEvent.pointerUp(target, { pointerId: 1, clientX: 190 });
    expect(screen.getByText("Post the job")).toBeInTheDocument();

    fireEvent.pointerDown(target, { pointerId: 2, clientX: 200, button: 0 });
    fireEvent.pointerUp(target, { pointerId: 2, clientX: 100 });
    expect(screen.getByText("Get prices")).toBeInTheDocument();

    fireEvent.pointerDown(target, { pointerId: 3, clientX: 100, button: 0 });
    fireEvent.pointerUp(target, { pointerId: 3, clientX: 220 });
    expect(screen.getByText("Post the job")).toBeInTheDocument();
  });

  it("announces captions politely and hides the decorative scene from screen readers", () => {
    const { container } = render(<HowItWorks />);
    expect(container.querySelector(".hiw-caption")).toHaveAttribute("aria-live", "polite");
    expect(container.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  });
});
