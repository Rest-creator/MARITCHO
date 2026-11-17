import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { queryKeys } from "@/core/query/keys";
import { createQueryClient } from "@/core/query/query-client";
import { SessionProvider } from "@/core/session/SessionProvider";
import { WorkerSkillsScreen } from "@/features/worker/WorkerSkillsScreen";

vi.mock("next/navigation", () => ({
  usePathname: () => "/worker/skills",
  useRouter: () => ({ back: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

function renderWithSavedDistance(travelKm: number) {
  const client = createQueryClient();
  client.setQueryData(queryKeys.session, {
    id: "w-1",
    phone: "+263771234567",
    role: "WORKER",
    display_name: "Tendai",
    is_available: true,
    travel_km: travelKm,
    home_suburb: "Hillside",
  });
  client.setQueryData(queryKeys.skills, []);
  client.setQueryData(queryKeys.serviceAreas, []);
  client.setQueryData(queryKeys.suburbs, [{ name: "Hillside", latitude: -20.17, longitude: 28.6 }]);
  return render(
    <QueryClientProvider client={client}>
      <SessionProvider>
        <WorkerSkillsScreen />
      </SessionProvider>
    </QueryClientProvider>,
  );
}

describe("WorkerSkillsScreen travel distance", () => {
  it("shows the saved distance instead of snapping it back to 25 km", () => {
    renderWithSavedDistance(40);
    const slider = screen.getByLabelText("How far can you travel?");

    expect(slider).toHaveAttribute("max", "50");
    expect(slider).toHaveValue("40");
    expect(screen.getByText("40 km")).toBeInTheDocument();
  });

  it("lets the worker pick anything up to 50 km", () => {
    renderWithSavedDistance(10);
    const slider = screen.getByLabelText("How far can you travel?");

    fireEvent.change(slider, { target: { value: "45" } });
    expect(screen.getByText("45 km")).toBeInTheDocument();
  });
});
