import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { queryKeys } from "@/core/query/keys";
import { WorkerPublicProfileScreen } from "@/features/employer/WorkerPublicProfileScreen";
import { WorkersScreen } from "@/features/employer/WorkersScreen";

vi.mock("next/navigation", () => ({
  usePathname: () => "/employer/workers",
  useRouter: () => ({ back: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

describe("WorkersScreen & WorkerPublicProfileScreen", () => {
  it("renders the Workers sidebar navigation and nearby workers list", async () => {
    const user = userEvent.setup();
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    client.setQueryData(queryKeys.suburbs, [
      { name: "Hillside", latitude: -20.185, longitude: 28.63 },
      { name: "Nkulumane", latitude: -20.205, longitude: 28.53 },
    ]);
    client.setQueryData(queryKeys.nearbyWorkers("Hillside", "", ""), [
      {
        worker_id: "w-1",
        display_name: "Tendai Moyo",
        suburb: "Hillside",
        trades: ["PLUMBING", "SOLAR"],
        proof_urls: ["/media/work-1.jpg"],
        grade: "EXPERT",
        on_time_rate: 96,
        dispute_rate: 0,
        fill_rate: 95,
        jobs_completed: 24,
        rating_average: 4.8,
        rating_count: 12,
        is_available: true,
        travel_km: 15,
        travel_means: "COMBI",
        distance_band: "SAME_SUBURB",
        distance_km: 0,
      },
    ]);

    render(
      <QueryClientProvider client={client}>
        <WorkersScreen />
      </QueryClientProvider>,
    );

    const nav = screen.getByRole("navigation", { name: "Employer navigation" });
    expect(nav).toHaveTextContent("Workers");
    expect(screen.getByRole("heading", { name: "Workers near you" })).toBeInTheDocument();
    expect(screen.getByText("Tendai Moyo")).toBeInTheDocument();
    expect(screen.getByText(/Same suburb/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View profile" })).toHaveAttribute(
      "href",
      "/employer/workers/w-1?suburb=Hillside",
    );

    // Suburb combobox shows close matches as the user writes
    const suburbInput = screen.getByLabelText("Close to which suburb?");
    await user.clear(suburbInput);
    await user.type(suburbInput, "Nkul");
    const listbox = screen.getByRole("listbox", { name: "Suburb options" });
    expect(within(listbox).getByRole("button", { name: /Nkulumane/ })).toBeInTheDocument();
  });

  it("renders a worker's public profile and signed-off job history", () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    client.setQueryData(queryKeys.workerProfile("w-1", "Hillside"), {
      worker_id: "w-1",
      display_name: "Tendai Moyo",
      suburb: "Hillside",
      trades: ["PLUMBING"],
      proof_urls: [],
      grade: "EXPERT",
      on_time_rate: 98,
      dispute_rate: 0,
      fill_rate: 95,
      jobs_completed: 18,
      rating_average: 4.9,
      rating_count: 9,
      is_available: true,
      travel_km: 20,
      travel_means: "COMBI",
      distance_band: "SAME_SUBURB",
      distance_km: 0,
      service_areas: ["Hillside", "Kumalo"],
      reference_count: 2,
      recent_work: [
        {
          job_id: "j-1",
          what_was_done: "Plumber job: Replaced burst geyser valve",
          client_words: "★★★★☆ — On time, Quality work",
          before_photo_url: null,
          after_photo_url: null,
          signed_off_at: "2026-10-14T10:00:00Z",
        },
      ],
    });

    render(
      <QueryClientProvider client={client}>
        <WorkerPublicProfileScreen workerId="w-1" initialSuburb="Hillside" />
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: "Tendai Moyo" })).toBeInTheDocument();
    expect(screen.getByText(/Covers Hillside, Kumalo/)).toBeInTheDocument();
    expect(screen.getByText("2 references checked")).toBeInTheDocument();
    expect(screen.getByText("Plumber job: Replaced burst geyser valve")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Post plumber job" })).toHaveAttribute(
      "href",
      "/employer/post?trade=PLUMBING",
    );
  });
});
