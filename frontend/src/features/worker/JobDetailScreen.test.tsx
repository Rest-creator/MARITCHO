import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { queryKeys } from "@/core/query/keys";
import { createQueryClient } from "@/core/query/query-client";
import { JobDetailScreen } from "@/features/worker/JobDetailScreen";

vi.mock("next/navigation", () => ({
  usePathname: () => "/worker/jobs/x",
  useRouter: () => ({ back: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

const JOB_ID = "6b1d2a52-6d0e-4b8f-9d3f-1f3c2c2b9a10";

function renderWithEligibility(eligibility: Record<string, unknown> | undefined) {
  const client = createQueryClient();
  client.setQueryData(queryKeys.openJobs, []);
  client.setQueryData(queryKeys.myOffers, []);
  if (eligibility) client.setQueryData(queryKeys.jobEligibility(JOB_ID), eligibility);
  return render(
    <QueryClientProvider client={client}>
      <JobDetailScreen jobId={JOB_ID} />
    </QueryClientProvider>,
  );
}

describe("JobDetailScreen skill matching", () => {
  it("explains a skills mismatch and offers to add the skill", () => {
    renderWithEligibility({
      is_eligible: false,
      required_trade: "PLUMBING",
      matched_by: null,
      similarity_score: null,
      reason:
        "This job needs plumbing, which isn't one of your skills (solar installation). Add it to your skills if it's work you do.",
    });

    expect(screen.getByText("This job isn't a match for your skills")).toBeInTheDocument();
    expect(screen.getByText(/needs plumbing/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Add a skill" })).toHaveAttribute(
      "href",
      "/worker/skills",
    );
    expect(screen.queryByText("This job has been filled")).toBeNull();
  });

  it("says the job was filled when the worker would have matched", () => {
    renderWithEligibility({
      is_eligible: true,
      required_trade: "PLUMBING",
      matched_by: "TRADE",
      similarity_score: null,
      reason: "Matches your plumbing skill.",
    });

    expect(screen.getByText("This job has been filled")).toBeInTheDocument();
  });
});
