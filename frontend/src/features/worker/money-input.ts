/** Parse a typed price ("35", "35.5") into a positive amount rounded to cents, or null. */
export function parseOfferAmount(raw: string): number | null {
  const amount = Number(raw);
  if (raw.trim() === "" || !Number.isFinite(amount) || amount <= 0) return null;
  return Math.round(amount * 100) / 100;
}
