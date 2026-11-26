import type { WorkerVetting } from "@/core/api/schemas";

/*
 * Identity documents (ADR-010). The photos are private — only the worker
 * and the Maritcho team can open them — and a badge appears only after the
 * team has checked the document, never just because a photo was uploaded.
 */

export type DocumentState = "NONE" | "PENDING" | "VERIFIED" | "REJECTED" | "EXPIRED";

export interface DocumentCopy {
  state: DocumentState;
  /** Short status next to the heading. */
  label: string;
  /** One or two plain sentences under it. */
  message: string;
  /** Upload button text. */
  action: string;
}

const PRIVATE = "Only you and the Maritcho team can see the photo.";

export function idDocumentState(vetting: WorkerVetting | undefined): DocumentState {
  if (!vetting?.id_photo_url) return "NONE";
  // A backend from before ADR-010 sends no status: the photo is unchecked.
  return vetting.id_status ?? "PENDING";
}

export function policeClearanceState(vetting: WorkerVetting | undefined): DocumentState {
  if (!vetting?.police_clearance_url) return "NONE";
  const status = vetting.police_clearance_status ?? "PENDING";
  if (status === "VERIFIED" && vetting.has_police_clearance !== true) return "EXPIRED";
  return status;
}

/** "27 Oct 2027" from a plain `YYYY-MM-DD` date, without a time-zone shift. */
export function formatPlainDate(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) return value;
  return new Date(Date.UTC(year, month - 1, day)).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function idDocumentCopy(vetting: WorkerVetting | undefined): DocumentCopy {
  const state = idDocumentState(vetting);
  switch (state) {
    case "PENDING":
      return {
        state,
        label: "Waiting for review",
        message: `We have your ID photo. The Maritcho team will check it, and your ID checked badge appears once it's approved. ${PRIVATE}`,
        action: "Replace ID photo",
      };
    case "VERIFIED":
      return {
        state,
        label: "Verified",
        message: vetting?.id_verified_name
          ? `Checked by Maritcho as ${vetting.id_verified_name}. Clients see your ID checked badge.`
          : "Checked by Maritcho. Clients see your ID checked badge.",
        action: "Replace ID photo",
      };
    case "REJECTED":
      return {
        state,
        label: "Not accepted",
        message: `${reasonSentence(vetting?.id_rejection_reason)} Please upload a new, clear photo of your National ID.`,
        action: "Upload a new photo",
      };
    default:
      return {
        state: "NONE",
        label: "Required",
        message: `Take a clear photo of your National ID to get the ID checked badge. ${PRIVATE}`,
        action: "Upload ID photo",
      };
  }
}

export function policeClearanceCopy(vetting: WorkerVetting | undefined): DocumentCopy {
  const state = policeClearanceState(vetting);
  switch (state) {
    case "PENDING":
      return {
        state,
        label: "Waiting for review",
        message:
          idDocumentState(vetting) === "VERIFIED"
            ? `We have your certificate. The Maritcho team will check it against your ID. ${PRIVATE}`
            : `We have your certificate. Your National ID is checked first, then the certificate. ${PRIVATE}`,
        action: "Replace certificate",
      };
    case "VERIFIED":
      return {
        state,
        label: "Verified",
        message: vetting?.police_clearance_expires_on
          ? `Checked by Maritcho. Employers see the Police Cleared badge until ${formatPlainDate(vetting.police_clearance_expires_on)}.`
          : "Checked by Maritcho. Employers see the Police Cleared badge.",
        action: "Replace certificate",
      };
    case "EXPIRED":
      return {
        state,
        label: "Expired",
        message:
          "Your certificate is more than a year old, so the Police Cleared badge is off. Upload a new certificate to get it back.",
        action: "Upload a new certificate",
      };
    case "REJECTED":
      return {
        state,
        label: "Not accepted",
        message: `${reasonSentence(vetting?.police_clearance_rejection_reason)} Please upload a new, clear photo of the certificate.`,
        action: "Upload a new photo",
      };
    default:
      return {
        state: "NONE",
        label: "Optional",
        message: `Upload a clear photo of your ZRP police clearance certificate to get the Police Cleared badge. ${PRIVATE}`,
        action: "Upload certificate",
      };
  }
}

function reasonSentence(reason: string | null | undefined): string {
  const text = reason?.trim();
  if (!text) return "The Maritcho team couldn't accept this photo.";
  return `Not accepted: ${/[.!?]$/.test(text) ? text : `${text}.`}`;
}
