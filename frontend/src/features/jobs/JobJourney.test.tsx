import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { JobJourney } from "@/features/jobs/JobJourney";

describe("JobJourney", () => {
  it("falls back to static bars marking done and current steps", () => {
    const { container } = render(<JobJourney done={1} />);
    const bars: Element[] = [...container.querySelectorAll(".stepper__bar")];

    expect(bars).toHaveLength(4);
    expect(bars[0]).toHaveClass("stepper__bar--done");
    expect(bars[1]).toHaveClass("stepper__bar--current");
    expect(bars[2]).not.toHaveClass("stepper__bar--done");
    expect(container.querySelector(".journey")).toHaveAttribute("aria-hidden", "true");
  });

  it("shows every bar done once the job is signed off", () => {
    const { container } = render(<JobJourney done={4} />);
    expect(container.querySelectorAll(".stepper__bar--done")).toHaveLength(4);
    expect(container.querySelector(".stepper__bar--current")).toBeNull();
  });
});
