import type { DistanceBand, Grade, JobStatus } from "@/core/api/schemas";

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

export function formatMoney(amount: number | null | undefined, currency: string = "USD"): string {
  if (amount === null || amount === undefined) {
    return "—";
  }
  const hasCents = Math.round(amount * 100) % 100 !== 0;
  const value = amount.toLocaleString("en-US", {
    minimumFractionDigits: hasCents ? 2 : 0,
    maximumFractionDigits: 2,
  });
  if (currency === "ZWG") return `ZWG ${value}`;
  return `$${value}`;
}

export function formatRelativeTime(iso: string | null | undefined, now: Date = new Date()): string {
  if (!iso) {
    return "";
  }
  const then = new Date(iso);
  const elapsed = now.getTime() - then.getTime();
  if (Number.isNaN(elapsed)) return "";
  if (elapsed < MINUTE) return "just now";
  if (elapsed < HOUR) return `${Math.floor(elapsed / MINUTE)} min ago`;
  if (elapsed < DAY) {
    const hours = Math.floor(elapsed / HOUR);
    return `${hours} ${hours === 1 ? "hour" : "hours"} ago`;
  }
  if (elapsed < 7 * DAY) {
    const days = Math.floor(elapsed / DAY);
    return `${days} ${days === 1 ? "day" : "days"} ago`;
  }
  return formatShortDate(iso);
}

export function formatShortDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export function formatClock(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export function formatDayLabel(iso: string, now: Date = new Date()): string {
  const date = new Date(iso);
  const sameDay = (a: Date, b: Date): boolean => a.toDateString() === b.toDateString();
  if (sameDay(date, now)) return "Today";
  const yesterday = new Date(now.getTime() - DAY);
  if (sameDay(date, yesterday)) return "Yesterday";
  return date.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
}

export function greeting(now: Date = new Date()): string {
  const hour = now.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? "") : "";
  return `${first}${last}`.toUpperCase();
}

export function firstName(name: string): string {
  return name.trim().split(/\s+/)[0] ?? "";
}

export function formatKm(km: number): string {
  return `${km < 10 ? km.toFixed(1) : Math.round(km)} km`;
}

export function formatPercent(rate: number): string {
  // Backend rates are 0–1 fractions.
  return `${Math.round(rate * 100)}%`;
}

const DISTANCE_BAND_LABELS: Record<DistanceBand, string> = {
  SAME_SUBURB: "Same suburb",
  NEARBY: "Nearby",
  MODERATE: "A short trip",
  FAR: "Further away",
};

export function distanceBandLabel(band: DistanceBand): string {
  return DISTANCE_BAND_LABELS[band];
}

const GRADE_LABELS: Record<Grade, string> = {
  REGISTERED: "New on Maricho",
  IDENTIFIED: "ID checked",
  APPRENTICE: "Apprentice",
  JOURNEYMAN: "Journeyman",
  EXPERT: "Expert",
};

export function gradeLabel(grade: Grade): string {
  return GRADE_LABELS[grade];
}

/** Grades at or above IDENTIFIED have passed Maricho's vetting. */
export function isVerifiedGrade(grade: Grade): boolean {
  return grade !== "REGISTERED";
}

const STATUS_LABELS: Record<JobStatus, string> = {
  REQUESTED: "Waiting for offers",
  MATCHED: "Offers in",
  BOOKED: "Hired",
  IN_PROGRESS: "Working",
  DISPUTED: "Being sorted out",
  COMPLETED: "Done",
  CANCELLED: "Cancelled",
};

export function jobStatusLabel(status: JobStatus): string {
  return STATUS_LABELS[status];
}

/** Normalise a Zimbabwean local number ("077 412 3089" / "77 412 3089") to "+263774123089". */
export function toInternationalPhone(local: string, countryCode: string = "263"): string {
  const digits = local.replace(/\D/g, "");
  if (digits.startsWith(countryCode)) return `+${digits}`;
  return `+${countryCode}${digits.replace(/^0+/, "")}`;
}

export function formatLocalPhone(international: string, countryCode: string = "263"): string {
  const digits = international.replace(/\D/g, "").replace(new RegExp(`^${countryCode}`), "");
  return digits.replace(/^(\d{2})(\d{3})(\d+)$/, "$1 $2 $3");
}
