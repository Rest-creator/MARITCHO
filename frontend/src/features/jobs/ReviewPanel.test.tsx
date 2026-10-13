import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ReviewPanel, type ReviewDraft } from "@/features/jobs/ReviewPanel";

function Harness() {
  const [value, setValue] = useState<ReviewDraft>({ stars: 5, tags: [], note: "" });
  return (
    <>
      <ReviewPanel value={value} onChange={setValue} />
      <output data-testid="state">{JSON.stringify(value)}</output>
    </>
  );
}

describe("ReviewPanel", () => {
  it("rates, tags and notes", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByRole("radio", { name: "3 stars" }));
    await user.click(screen.getByRole("button", { name: "On time" }));
    await user.click(screen.getByRole("button", { name: "Polite" }));
    await user.click(screen.getByRole("button", { name: "On time" }));
    await user.type(screen.getByLabelText("Add a few words"), "Neat");

    expect(screen.getByRole("radio", { name: "3 stars" })).toHaveAttribute("aria-checked", "true");
    expect(JSON.parse(screen.getByTestId("state").textContent ?? "{}")).toEqual({
      stars: 3,
      tags: ["Polite"],
      note: "Neat",
    });
  });
});
