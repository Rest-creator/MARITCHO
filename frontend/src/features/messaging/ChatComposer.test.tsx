import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type * as UploadModule from "@/core/media/upload";

const uploadMedia = vi.fn();
vi.mock("@/core/media/upload", async (importOriginal) => ({
  ...(await importOriginal<typeof UploadModule>()),
  uploadMedia: (...args: unknown[]) => uploadMedia(...args),
}));
vi.mock("@/core/media/compress-image", () => ({
  compressImage: async (file: Blob) => file,
}));

const { ChatComposer } = await import("@/features/messaging/ChatComposer");
const { TapToLoadPhoto } = await import("@/components/ui/TapToLoadPhoto");

function choosePhoto(container: HTMLElement, name: string): void {
  const input = container.querySelector<HTMLInputElement>('input[type="file"]');
  if (input === null) throw new Error("No file input");
  fireEvent.change(input, { target: { files: [new File(["x"], name, { type: "image/jpeg" })] } });
}

describe("ChatComposer", () => {
  it("sends typed text and offers no attachments before uploads exist", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatComposer canAttach={false} onSend={onSend} />);

    expect(screen.queryByRole("button", { name: "Send a photo" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Record a voice note" })).toBeNull();
    await user.type(screen.getByLabelText("Message"), "On my way");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(onSend).toHaveBeenCalledWith({ message_type: "TEXT", body: "On my way" });
  });

  it("uploads a chosen photo and sends it as a PHOTO message", async () => {
    uploadMedia.mockResolvedValueOnce({
      url: "/media/p1.jpg",
      content_type: "image/jpeg",
      size_bytes: 10,
    });
    const onSend = vi.fn();
    const { container } = render(<ChatComposer canAttach onSend={onSend} />);

    expect(screen.getByRole("button", { name: "Send a photo" })).toBeInTheDocument();
    choosePhoto(container, "leak.jpg");

    await waitFor(() =>
      expect(onSend).toHaveBeenCalledWith({ message_type: "PHOTO", media_url: "/media/p1.jpg" }),
    );
    expect(uploadMedia).toHaveBeenCalledWith(
      expect.objectContaining({ kind: "photo", filename: "photo.jpg" }),
    );
  });

  it("explains a failed photo instead of losing it silently", async () => {
    uploadMedia.mockRejectedValueOnce(new Error("Connection lost"));
    const onSend = vi.fn();
    const { container } = render(<ChatComposer canAttach onSend={onSend} />);
    choosePhoto(container, "a.jpg");
    expect(await screen.findByRole("alert")).toHaveTextContent("Didn't send: Connection lost");
    expect(onSend).not.toHaveBeenCalled();
  });
});

describe("TapToLoadPhoto", () => {
  it("downloads nothing until tapped", async () => {
    const user = userEvent.setup();
    render(<TapToLoadPhoto url="/media/p1.jpg" label="Photo of the problem" />);
    expect(screen.queryByRole("img")).toBeNull();
    await user.click(screen.getByRole("button", { name: /Photo of the problem · tap to load/ }));
    expect(screen.getByRole("img", { name: "Photo of the problem" })).toHaveAttribute(
      "src",
      "/api/media/p1.jpg",
    );
  });
});
