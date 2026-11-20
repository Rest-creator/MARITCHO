import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { queryKeys } from "@/core/query/keys";
import { LocationSheet } from "@/features/jobs/LocationSheet";

function renderSheet(onSave = vi.fn(), onClose = vi.fn()) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  client.setQueryData(queryKeys.suburbs, [
    { name: "Entumbane", latitude: -20.22, longitude: 28.55 },
    { name: "Hillside", latitude: -20.185, longitude: 28.63 },
    { name: "Kumalo", latitude: -20.175, longitude: 28.645 },
    { name: "Luveve", latitude: -20.155, longitude: 28.53 },
    { name: "Njube", latitude: -20.197, longitude: 28.542 },
    { name: "Nkulumane", latitude: -20.205, longitude: 28.53 },
  ]);

  return render(
    <QueryClientProvider client={client}>
      <LocationSheet
        isOpen
        value={{ suburb: "", address: "", landmark: "" }}
        onClose={onClose}
        onSave={onSave}
      />
    </QueryClientProvider>,
  );
}

describe("LocationSheet", () => {
  it("supports picking a suburb from the dropdown list", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderSheet(onSave);

    await user.click(screen.getByRole("button", { name: "Show the list" }));
    const listbox = screen.getByRole("listbox", { name: "Suburb options" });
    await user.click(within(listbox).getByRole("button", { name: /Hillside/ }));
    await user.type(screen.getByLabelText("Street address"), "14 Harrow Rd");
    await user.click(screen.getByRole("button", { name: "Use this place" }));

    expect(onSave).toHaveBeenCalledWith({
      suburb: "Hillside",
      address: "14 Harrow Rd",
      landmark: "",
    });
  });

  it("shows close-match autofill predictions on the dropdown as the user types", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderSheet(onSave);

    const input = screen.getByLabelText("Suburb");
    await user.type(input, "N");
    const listbox = screen.getByRole("listbox", { name: "Suburb options" });
    expect(within(listbox).getByRole("button", { name: /Njube/ })).toBeInTheDocument();
    expect(within(listbox).getByRole("button", { name: /Nkulumane/ })).toBeInTheDocument();

    // Continue typing to narrow down to the right match
    await user.type(input, "kulu");
    expect(within(listbox).getByRole("button", { name: /Nkulumane/ })).toBeInTheDocument();
    expect(within(listbox).queryByRole("button", { name: /Njube/ })).not.toBeInTheDocument();

    // Autofill via Enter key
    await user.keyboard("{Enter}");
    expect(input).toHaveValue("Nkulumane");
  });

  it("allows custom write-in suburbs", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderSheet(onSave);

    await user.type(screen.getByLabelText("Suburb"), "Burnside");
    await user.type(screen.getByLabelText("Street address"), "22 Cecil Ave");
    await user.click(screen.getByRole("button", { name: "Use this place" }));

    expect(onSave).toHaveBeenCalledWith({
      suburb: "Burnside",
      address: "22 Cecil Ave",
      landmark: "",
    });
  });

  it("clears a pre-selected suburb when tapping 'Type another suburb…' in the options list", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    client.setQueryData(queryKeys.suburbs, [
      { name: "Hillside", latitude: -20.185, longitude: 28.63 },
      { name: "Kumalo", latitude: -20.175, longitude: 28.645 },
    ]);

    render(
      <QueryClientProvider client={client}>
        <LocationSheet
          isOpen
          value={{ suburb: "Hillside", address: "14 Harrow Rd", landmark: "" }}
          onClose={vi.fn()}
          onSave={onSave}
        />
      </QueryClientProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Show the list" }));
    const listbox = screen.getByRole("listbox", { name: "Suburb options" });
    await user.click(within(listbox).getByRole("button", { name: /Type another suburb/ }));

    const input = screen.getByLabelText("Suburb");
    expect(input).toHaveValue("");
    await user.type(input, "Bradfield");
    await user.click(screen.getByRole("button", { name: "Use this place" }));

    expect(onSave).toHaveBeenCalledWith({
      suburb: "Bradfield",
      address: "14 Harrow Rd",
      landmark: "",
    });
  });

  it("detects nearest suburb and attaches GPS coordinates when choosing 'Use my current location'", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    const getCurrentPosition = vi.fn((success: PositionCallback) => {
      success({
        coords: {
          latitude: -20.1748,
          longitude: 28.6449,
          accuracy: 15,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
          toJSON: () => ({}),
        },
        timestamp: Date.now(),
        toJSON: () => ({}),
      });
    });
    Object.defineProperty(globalThis.navigator, "geolocation", {
      value: { getCurrentPosition },
      configurable: true,
    });

    renderSheet(onSave);

    await user.click(screen.getByRole("button", { name: "Show the list" }));
    const listbox = screen.getByRole("listbox", { name: "Suburb options" });
    await user.click(within(listbox).getByRole("button", { name: /Use my current location/ }));

    expect(getCurrentPosition).toHaveBeenCalledOnce();
    expect(screen.getByLabelText("Suburb")).toHaveValue("Kumalo");
    expect(screen.getByRole("status")).toHaveTextContent(/Nearest suburb: Kumalo/);

    await user.click(screen.getByRole("button", { name: "Use this place" }));

    expect(onSave).toHaveBeenCalledWith({
      suburb: "Kumalo",
      address: "Pinned location (Kumalo)",
      landmark: "",
      latitude: -20.1748,
      longitude: 28.6449,
    });
  });
});
