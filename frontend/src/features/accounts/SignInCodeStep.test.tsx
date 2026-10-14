import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { formatCountdown, normaliseCode } from "@/core/session/sign-in-code";
import { SignInCodeStep } from "@/features/accounts/SignInCodeStep";

function renderStep(overrides: Partial<Parameters<typeof SignInCodeStep>[0]> = {}) {
  const props = {
    phone: "+263774123089",
    resendAfterSeconds: 30,
    isVerifying: false,
    error: null,
    onVerify: vi.fn(),
    onResend: vi.fn().mockResolvedValue(30),
    onChangeNumber: vi.fn(),
    ...overrides,
  };
  render(<SignInCodeStep {...props} />);
  return props;
}

afterEach(() => {
  vi.useRealTimers();
});

describe("sign-in code helpers", () => {
  it("keeps only the first six digits of whatever was typed or pasted", () => {
    expect(normaliseCode("123 456")).toBe("123456");
    expect(normaliseCode("12-34-5678")).toBe("123456");
    expect(normaliseCode("abc")).toBe("");
  });

  it("formats the resend countdown", () => {
    expect(formatCountdown(30)).toBe("0:30");
    expect(formatCountdown(61.2)).toBe("1:02");
    expect(formatCountdown(-4)).toBe("0:00");
  });
});

describe("SignInCodeStep", () => {
  it("says where the code went and signs in as soon as six digits are in", async () => {
    const user = userEvent.setup();
    const props = renderStep();

    expect(screen.getByText("+263 77 412 3089")).toBeInTheDocument();
    const input = screen.getByLabelText("6-digit code");
    expect(input).toHaveAttribute("autocomplete", "one-time-code");
    await user.type(input, "12345");
    expect(props.onVerify).not.toHaveBeenCalled();
    await user.type(input, "6");
    expect(props.onVerify).toHaveBeenCalledExactlyOnceWith("123456");
  });

  it("accepts a pasted code with spaces", () => {
    const props = renderStep();
    fireEvent.change(screen.getByLabelText("6-digit code"), { target: { value: "482 913" } });
    expect(props.onVerify).toHaveBeenCalledWith("482913");
  });

  it("shows why a code was refused", () => {
    renderStep({ error: "That code isn't right, or it has expired." });
    expect(screen.getByRole("alert")).toHaveTextContent("That code isn't right");
    expect(screen.getByLabelText("6-digit code")).toHaveAttribute("aria-invalid", "true");
  });

  it("only offers a new code after the wait, then restarts it", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const props = renderStep({ resendAfterSeconds: 3 });

    expect(screen.getByText("New code in 0:03")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Send a new code" })).toBeNull();

    await act(async () => {
      vi.advanceTimersByTime(3_100);
    });
    fireEvent.click(screen.getByRole("button", { name: "Send a new code" }));
    expect(props.onResend).toHaveBeenCalledOnce();
    expect(await screen.findByText("New code sent.")).toBeInTheDocument();
    expect(screen.getByText(/New code in 0:(30|29)/)).toBeInTheDocument();
  });

  it("goes back to change the number", async () => {
    const user = userEvent.setup();
    const props = renderStep();
    await user.click(screen.getByRole("button", { name: "Change number" }));
    expect(props.onChangeNumber).toHaveBeenCalledOnce();
  });
});
