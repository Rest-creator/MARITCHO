import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { queryKeys } from "@/core/query/keys";
import { createQueryClient } from "@/core/query/query-client";
import { SessionProvider, type SignInRole } from "@/core/session/SessionProvider";
import { SignUpScreen, validateSignUpDetails } from "@/features/accounts/SignUpScreen";
import { WelcomeScreen } from "@/features/accounts/WelcomeScreen";

vi.mock("next/navigation", () => ({
  usePathname: () => "/signup",
  useRouter: () => ({ back: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

function renderScreen(ui: React.ReactElement) {
  const client = createQueryClient();
  client.setQueryData(queryKeys.session, null);
  client.setQueryData(queryKeys.suburbs, [
    { name: "Hillside", latitude: -20.17, longitude: 28.6 },
    { name: "Nkulumane", latitude: -20.2, longitude: 28.53 },
  ]);
  return render(
    <QueryClientProvider client={client}>
      <SessionProvider>{ui}</SessionProvider>
    </QueryClientProvider>,
  );
}

function renderSignUp(isLogin: boolean, role: SignInRole = "BUYER") {
  return renderScreen(<SignUpScreen initialRole={role} isLogin={isLogin} isExpired={false} />);
}

describe("WelcomeScreen", () => {
  it("sends both role choices to log in, and offers account creation underneath", () => {
    renderScreen(<WelcomeScreen />);

    expect(screen.getByRole("link", { name: /I need work done/ })).toHaveAttribute(
      "href",
      "/signup?mode=login&role=buyer",
    );
    expect(screen.getByRole("link", { name: /looking for work/ })).toHaveAttribute(
      "href",
      "/signup?mode=login&role=worker",
    );
    expect(screen.getByText(/Don't have an account\?/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create account" })).toHaveAttribute("href", "/signup");
    expect(screen.queryByText(/Already have an account/)).toBeNull();
  });
});

describe("SignUpScreen", () => {
  it("logs in with just phone and password, linking to account creation for that role", async () => {
    const user = userEvent.setup();
    renderSignUp(true);

    expect(screen.getByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Your full name")).toBeNull();
    expect(screen.queryByLabelText(/Emergency contact/)).toBeNull();
    expect(screen.getByRole("button", { name: "Log in" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create account" })).toHaveAttribute(
      "href",
      "/signup?role=buyer",
    );

    await user.click(screen.getByRole("button", { name: "I find work" }));
    expect(screen.getByRole("link", { name: "Create account" })).toHaveAttribute(
      "href",
      "/signup?role=worker",
    );
  });

  it("asks a new employer where work is needed, an optional address and an emergency contact", () => {
    renderSignUp(false, "BUYER");

    expect(screen.getByLabelText("Your full name")).toBeInTheDocument();
    expect(screen.getByLabelText("Where do you usually need work done?")).toBeInTheDocument();
    expect(screen.getByLabelText("House number or street (optional)")).toBeInTheDocument();
    expect(screen.getByLabelText("Emergency contact number (optional)")).toBeInTheDocument();
    expect(screen.queryByText("How do you get to jobs?")).toBeNull();
    expect(screen.getByRole("link", { name: "Log in" })).toHaveAttribute(
      "href",
      "/signup?mode=login&role=buyer",
    );
  });

  it("asks a new worker where they're based and how they travel", async () => {
    const user = userEvent.setup();
    renderSignUp(false, "WORKER");

    expect(screen.getByLabelText("Where are you based?")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Nkulumane" })).toBeInTheDocument();
    expect(screen.queryByLabelText("House number or street (optional)")).toBeNull();

    const kombi = screen.getByRole("button", { name: "Kombi / bus" });
    await user.click(kombi);
    expect(kombi).toHaveAttribute("aria-pressed", "true");
    await user.click(kombi);
    expect(kombi).toHaveAttribute("aria-pressed", "false");
  });

  it("won't create an account without a suburb", async () => {
    const user = userEvent.setup();
    renderSignUp(false, "BUYER");

    await user.type(screen.getByLabelText("Your full name"), "Rudo Ncube");
    await user.type(screen.getByLabelText("Phone number"), "77 412 3089");
    await user.type(screen.getByLabelText("Password"), "correct-horse");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(screen.getByRole("alert")).toHaveTextContent(/suburb/);
  });
});

describe("validateSignUpDetails", () => {
  const base = { role: "WORKER" as const, suburb: "Hillside", phone: "77 412 3089" };

  it("requires a suburb, worded for the role", () => {
    expect(validateSignUpDetails({ ...base, suburb: " ", emergencyPhone: "" })).toMatch(/based in/);
    expect(
      validateSignUpDetails({ ...base, role: "BUYER", suburb: "", emergencyPhone: "" }),
    ).toMatch(/need work done/);
  });

  it("treats the emergency contact as optional but checks it when given", () => {
    expect(validateSignUpDetails({ ...base, emergencyPhone: "" })).toBeNull();
    expect(validateSignUpDetails({ ...base, emergencyPhone: "0772000111" })).toBeNull();
    expect(validateSignUpDetails({ ...base, emergencyPhone: "772" })).toMatch(/mobile number/);
  });

  it("rejects your own number as your emergency contact", () => {
    expect(validateSignUpDetails({ ...base, emergencyPhone: "0774123089" })).toMatch(
      /someone else/,
    );
  });
});
