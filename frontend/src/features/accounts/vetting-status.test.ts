import { describe, expect, it } from "vitest";

import type { WorkerVetting } from "@/core/api/schemas";
import {
  formatPlainDate,
  idDocumentCopy,
  idDocumentState,
  policeClearanceCopy,
  policeClearanceState,
} from "@/features/accounts/vetting-status";

const BASE: WorkerVetting = {
  worker_id: "3f1c2a4e-1111-4222-8333-444455556666",
  id_photo_url: null,
  id_submitted_at: null,
  reference_count: 0,
  vouch_count: 0,
  grade: "REGISTERED",
};

function vetting(overrides: Partial<WorkerVetting>): WorkerVetting {
  return { ...BASE, ...overrides };
}

describe("idDocumentState", () => {
  it("is NONE until a photo is uploaded", () => {
    expect(idDocumentState(undefined)).toBe("NONE");
    expect(idDocumentState(BASE)).toBe("NONE");
  });

  it("treats an uploaded photo without a review as waiting, never verified", () => {
    expect(idDocumentState(vetting({ id_photo_url: "/media/a" }))).toBe("PENDING");
  });

  it("follows the review status", () => {
    expect(idDocumentState(vetting({ id_photo_url: "/media/a", id_status: "VERIFIED" }))).toBe(
      "VERIFIED",
    );
    expect(idDocumentState(vetting({ id_photo_url: "/media/a", id_status: "REJECTED" }))).toBe(
      "REJECTED",
    );
  });
});

describe("policeClearanceState", () => {
  it("is EXPIRED when approved but the badge has lapsed", () => {
    const lapsed = vetting({
      police_clearance_url: "/media/b",
      police_clearance_status: "VERIFIED",
      has_police_clearance: false,
    });
    expect(policeClearanceState(lapsed)).toBe("EXPIRED");
  });

  it("is VERIFIED only while the badge is live", () => {
    const live = vetting({
      police_clearance_url: "/media/b",
      police_clearance_status: "VERIFIED",
      has_police_clearance: true,
    });
    expect(policeClearanceState(live)).toBe("VERIFIED");
  });
});

describe("copy", () => {
  it("tells the worker the photo is private and waiting", () => {
    const copy = idDocumentCopy(vetting({ id_photo_url: "/media/a", id_status: "PENDING" }));
    expect(copy.label).toBe("Waiting for review");
    expect(copy.message).toContain("Only you and the Maritcho team can see the photo.");
  });

  it("shows the verified name", () => {
    const copy = idDocumentCopy(
      vetting({ id_photo_url: "/media/a", id_status: "VERIFIED", id_verified_name: "Tendai Moyo" }),
    );
    expect(copy.message).toContain("Tendai Moyo");
  });

  it("explains a rejection with the reviewer's reason", () => {
    const copy = idDocumentCopy(
      vetting({
        id_photo_url: "/media/a",
        id_status: "REJECTED",
        id_rejection_reason: "The photo is blurry",
      }),
    );
    expect(copy.label).toBe("Not accepted");
    expect(copy.message).toContain("Not accepted: The photo is blurry.");
    expect(copy.action).toBe("Upload a new photo");
  });

  it("says the ID is checked first when the certificate is waiting on it", () => {
    const copy = policeClearanceCopy(
      vetting({ police_clearance_url: "/media/b", police_clearance_status: "PENDING" }),
    );
    expect(copy.message).toContain("Your National ID is checked first");
  });

  it("shows when the Police Cleared badge runs out", () => {
    const copy = policeClearanceCopy(
      vetting({
        police_clearance_url: "/media/b",
        police_clearance_status: "VERIFIED",
        police_clearance_expires_on: "2027-10-27",
        has_police_clearance: true,
      }),
    );
    expect(copy.message).toContain("27 Oct 2027");
  });
});

describe("formatPlainDate", () => {
  it("formats a plain date without shifting the day", () => {
    expect(formatPlainDate("2027-01-01")).toBe("1 Jan 2027");
  });

  it("returns anything unexpected unchanged", () => {
    expect(formatPlainDate("soon")).toBe("soon");
  });
});
