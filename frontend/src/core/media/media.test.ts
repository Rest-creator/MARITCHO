import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/core/api/http";
import { fitWithin } from "@/core/media/compress-image";
import {
  fetchMediaCapability,
  isUploadUnavailable,
  mediaSrc,
  uploadMedia,
} from "@/core/media/upload";
import { audioExtension } from "@/core/media/use-upload";
import { pickAudioType } from "@/core/media/use-voice-recorder";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fitWithin", () => {
  it("shrinks the long side to 1280 and keeps the shape", () => {
    expect(fitWithin(4000, 3000)).toEqual({ width: 1280, height: 960 });
    expect(fitWithin(3000, 4000)).toEqual({ width: 960, height: 1280 });
  });

  it("never enlarges a small photo", () => {
    expect(fitWithin(800, 600)).toEqual({ width: 800, height: 600 });
  });
});

describe("mediaSrc", () => {
  it("sends backend paths through the BFF and keeps full URLs", () => {
    expect(mediaSrc("/media/abc.jpg")).toBe("/api/media/abc.jpg");
    expect(mediaSrc("https://cdn.example/x.jpg?sig=1")).toBe("https://cdn.example/x.jpg?sig=1");
  });

  it("refuses anything else", () => {
    expect(mediaSrc(null)).toBeNull();
    expect(mediaSrc("")).toBeNull();
    expect(mediaSrc("javascript:alert(1)")).toBeNull();
    expect(mediaSrc("/api/session")).toBeNull();
  });
});

describe("uploadMedia", () => {
  it("posts the file as multipart with its idempotency key", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        Response.json(
          { url: "/media/p1.jpg", content_type: "image/jpeg", size_bytes: 1234 },
          { status: 201 },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const stored = await uploadMedia({
      file: new Blob(["x"], { type: "image/jpeg" }),
      kind: "photo",
      filename: "photo.jpg",
      idempotencyKey: "key-1",
    });

    expect(stored.url).toBe("/media/p1.jpg");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/media");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "idempotency-key": "key-1" });
    const form = init.body as FormData;
    expect(form.get("kind")).toBe("photo");
    expect((form.get("file") as File).name).toBe("photo.jpg");
  });

  it("reports a missing endpoint as 'not available yet'", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({}, { status: 404 })));
    const failure = await uploadMedia({
      file: new Blob(["x"]),
      kind: "photo",
      filename: "photo.jpg",
      idempotencyKey: "k",
    }).catch((error: unknown) => error);
    expect(isUploadUnavailable(failure)).toBe(true);
  });

  it("passes on the backend's reason for refusing a file", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json({ detail: "File too large" }, { status: 413 })),
    );
    await expect(
      uploadMedia({ file: new Blob(["x"]), kind: "photo", filename: "p.jpg", idempotencyKey: "k" }),
    ).rejects.toMatchObject({ message: "File too large", status: 413 });
  });

  it("treats a dropped connection as offline", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const failure = await uploadMedia({
      file: new Blob(["x"]),
      kind: "voice_note",
      filename: "v.webm",
      idempotencyKey: "k",
    }).catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(ApiError);
    expect((failure as ApiError).isNetwork).toBe(true);
    expect(isUploadUnavailable(failure)).toBe(false);
  });
});

describe("fetchMediaCapability", () => {
  it.each([
    [404, false],
    [405, true],
    [200, true],
  ])("GET /media answering %i means uploads available = %s", async (status, expected) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status })));
    await expect(fetchMediaCapability()).resolves.toBe(expected);
  });
});

describe("audio formats", () => {
  it("prefers Opus in WebM, then Ogg, then MP4", () => {
    expect(pickAudioType(() => true)).toBe("audio/webm;codecs=opus");
    expect(pickAudioType((type) => type.startsWith("audio/mp4"))).toBe("audio/mp4");
    expect(pickAudioType(() => false)).toBe("");
  });

  it("names the uploaded file to match", () => {
    expect(audioExtension("audio/webm;codecs=opus")).toBe(".webm");
    expect(audioExtension("audio/mp4")).toBe(".m4a");
    expect(audioExtension("")).toBe("");
  });
});
