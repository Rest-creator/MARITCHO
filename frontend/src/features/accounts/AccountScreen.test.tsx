import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { queryKeys } from "@/core/query/keys";
import { createQueryClient } from "@/core/query/query-client";
import { SessionProvider } from "@/core/session/SessionProvider";
import { AccountScreen } from "@/features/accounts/AccountScreen";
import { EmployerTabBar } from "@/features/employer/EmployerTabBar";
import { WorkerTabBar } from "@/features/worker/WorkerTabBar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/worker/account",
  useRouter: () => ({ back: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

describe("AccountScreen", () => {
  it("renders worker standing, earnings, availability reach, vetting progression, and safety details", async () => {
    const user = userEvent.setup();
    const client = createQueryClient();

    client.setQueryData(queryKeys.session, {
      id: "w-100",
      phone: "+263771234567",
      role: "WORKER",
      display_name: "Tendai Moyo",
      is_available: true,
      travel_km: 15,
      home_suburb: "Nkulumane",
      next_of_kin_phone: "+263772111222",
      created_at: "2026-10-01T10:00:00Z",
    });
    client.setQueryData(queryKeys.standing, {
      worker_id: "w-100",
      grade: "JOURNEYMAN",
      on_time_rate: 98,
      dispute_rate: 0,
      fill_rate: 96,
      jobs_completed: 14,
      is_frozen: false,
      rating_average: 4.9,
      rating_count: 11,
    });
    client.setQueryData(queryKeys.vetting, {
      worker_id: "w-100",
      id_photo_url: "https://maritcho.co.zw/id-proof/08-123456A08",
      id_submitted_at: "2026-10-02T10:00:00Z",
      reference_count: 1,
      vouch_count: 1,
      grade: "JOURNEYMAN",
    });
    client.setQueryData(queryKeys.references, [
      {
        id: "ref-1",
        worker_id: "w-100",
        name: "Mai Ncube",
        phone: "+263774000999",
        created_at: "2026-10-03T10:00:00Z",
      },
    ]);
    client.setQueryData(queryKeys.skills, [
      {
        id: "sk-1",
        worker_id: "w-100",
        trade: "PLUMBING",
        grade: "JOURNEYMAN",
        proof_url: null,
      },
    ]);
    client.setQueryData(queryKeys.serviceAreas, [
      {
        id: "sa-1",
        worker_id: "w-100",
        suburb: "Nkulumane",
        travel_means: "Kombi / bus",
      },
    ]);
    client.setQueryData(queryKeys.assignedJobs, []);
    client.setQueryData(queryKeys.myOffers, []);
    client.setQueryData(queryKeys.suburbs, [
      { name: "Nkulumane", latitude: -20.2, longitude: 28.5 },
      { name: "Hillside", latitude: -20.18, longitude: 28.63 },
    ]);

    render(
      <QueryClientProvider client={client}>
        <SessionProvider>
          <AccountScreen tabBar={<WorkerTabBar />} />
        </SessionProvider>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: "My profile" })).toBeInTheDocument();
    expect(screen.getByText("Tendai Moyo")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Standing & earnings/ })).toBeInTheDocument();
    expect(screen.getByText("98%")).toBeInTheDocument();
    expect(screen.getByText("★ 4.9")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Availability & travel reach/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Vetting & trust tier/ })).toBeInTheDocument();
    expect(screen.getByText("Mai Ncube")).toBeInTheDocument();
    expect(screen.getByLabelText("Fellow worker ID")).toBeInTheDocument();

    const kinInput = screen.getByLabelText("Next of kin / emergency phone (+263)");
    await user.clear(kinInput);
    await user.type(kinInput, "077 888 9999");
    expect(kinInput).toHaveValue("077 888 9999");
  });

  it("renders employer hiring overview, saved job location defaults, and payment currency preferences", async () => {
    const user = userEvent.setup();
    const client = createQueryClient();

    client.setQueryData(queryKeys.session, {
      id: "b-200",
      phone: "+263779998887",
      role: "BUYER",
      display_name: "Rudo Kanengoni",
      home_suburb: "Hillside",
      next_of_kin_phone: null,
      created_at: "2026-10-05T10:00:00Z",
    });
    client.setQueryData(queryKeys.myJobs, [
      {
        id: "j-1",
        buyer_id: "b-200",
        worker_id: null,
        status: "MATCHED",
        trade: "PLUMBING",
        suburb: "Hillside",
        address: "14 Cecil Ave",
        landmark_narrative: "Green gate",
        latitude: null,
        longitude: null,
        problem_description: "Fix burst geyser pipe",
        problem_photo_url: null,
        budget_amount: 45,
        currency: "USD",
        labor_amount: null,
        materials_amount: null,
        quote_amount: null,
        created_at: "2026-10-12T10:00:00Z",
        updated_at: "2026-10-12T10:00:00Z",
        offer_count: 3,
      },
      {
        id: "j-2",
        buyer_id: "b-200",
        worker_id: "w-100",
        status: "COMPLETED",
        trade: "SOLAR",
        suburb: "Hillside",
        address: "14 Cecil Ave",
        landmark_narrative: null,
        latitude: null,
        longitude: null,
        problem_description: "Install inverter",
        problem_photo_url: null,
        budget_amount: 120,
        currency: "USD",
        labor_amount: 80,
        materials_amount: 40,
        quote_amount: 120,
        created_at: "2026-10-10T10:00:00Z",
        updated_at: "2026-10-11T10:00:00Z",
        offer_count: 1,
      },
    ]);
    client.setQueryData(queryKeys.suburbs, [
      { name: "Hillside", latitude: -20.18, longitude: 28.63 },
      { name: "Suburbs", latitude: -20.15, longitude: 28.6 },
    ]);

    render(
      <QueryClientProvider client={client}>
        <SessionProvider>
          <AccountScreen tabBar={<EmployerTabBar />} />
        </SessionProvider>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: "Account" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Hiring overview" })).toBeInTheDocument();
    expect(screen.getByText("$120")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Saved job location & payment defaults/ }),
    ).toBeInTheDocument();

    const ecoCashBtn = screen.getByRole("button", { name: "EcoCash" });
    await user.click(ecoCashBtn);
    expect(ecoCashBtn).toHaveAttribute("aria-pressed", "true");

    const saveDefaultsBtn = screen.getByRole("button", { name: "Save hiring defaults" });
    await user.click(saveDefaultsBtn);
    expect(
      screen.getByText("Default job location and payment preferences saved."),
    ).toBeInTheDocument();
  });
});
