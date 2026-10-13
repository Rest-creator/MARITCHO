import { z } from "zod";

/*
 * Runtime contracts for every backend response the app reads. They mirror
 * the Pydantic schemas in backend/app/apps/<app>/interface_adapters/schemas.py;
 * parsing at the boundary turns a silent backend drift into a visible error.
 */

/** Pydantic serialises `Decimal` as a JSON string. */
const decimal = z.union([z.string(), z.number()]).transform((value, ctx) => {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) {
    ctx.addIssue({ code: "custom", message: "Expected a decimal" });
    return z.NEVER;
  }
  return parsed;
});
const nullableDecimal = decimal.nullable();
const uuid = z.string().min(1);
const isoDate = z.string().min(1);

export const roleSchema = z.enum(["BUYER", "WORKER", "OPS", "AGGREGATOR"]);
export const tradeSchema = z.enum([
  "PLUMBING",
  "ELECTRICAL",
  "SOLAR",
  "WELDING",
  "BUILDING",
  "APPLIANCE_REPAIR",
]);
export const gradeSchema = z.enum([
  "REGISTERED",
  "IDENTIFIED",
  "APPRENTICE",
  "JOURNEYMAN",
  "EXPERT",
]);
export const currencySchema = z.enum(["USD", "ECOCASH", "ZWG"]);
export const distanceBandSchema = z.enum(["SAME_SUBURB", "NEARBY", "MODERATE", "FAR"]);
export const jobStatusSchema = z.enum([
  "REQUESTED",
  "MATCHED",
  "BOOKED",
  "IN_PROGRESS",
  "DISPUTED",
  "COMPLETED",
  "CANCELLED",
]);
export const messageTypeSchema = z.enum(["TEXT", "VOICE_NOTE", "PHOTO", "LOCATION"]);

export const tokenSchema = z.object({
  access_token: z.string().min(1),
  token_type: z.string(),
});

export const userSchema = z.object({
  id: uuid,
  phone: z.string(),
  role: roleSchema,
});

export const jobSchema = z.object({
  id: uuid,
  buyer_id: uuid,
  worker_id: uuid.nullable(),
  status: jobStatusSchema,
  trade: tradeSchema,
  suburb: z.string(),
  address: z.string(),
  landmark_narrative: z.string().nullable(),
  latitude: nullableDecimal,
  longitude: nullableDecimal,
  problem_description: z.string().nullable(),
  problem_photo_url: z.string().nullable(),
  budget_amount: nullableDecimal,
  currency: currencySchema.nullable(),
  labor_amount: nullableDecimal,
  materials_amount: nullableDecimal,
  quote_amount: nullableDecimal,
  created_at: isoDate,
  updated_at: isoDate,
});

export const myJobSchema = jobSchema.extend({ offer_count: z.number().int() });

export const openJobSchema = z.object({
  job_id: uuid,
  trade: tradeSchema,
  suburb: z.string(),
  budget_amount: nullableDecimal,
  problem_description: z.string().nullable(),
  created_at: isoDate.nullable(),
  distance_band: distanceBandSchema,
  distance_km: z.number(),
});

export const myOfferSchema = z.object({
  id: uuid,
  job_id: uuid,
  quoted_amount: decimal,
  availability_note: z.string().nullable(),
  created_at: isoDate,
  updated_at: isoDate,
  job_trade: tradeSchema,
  job_suburb: z.string(),
  job_status: jobStatusSchema,
});

export const jobOfferSchema = z.object({
  id: uuid,
  job_id: uuid,
  worker_id: uuid,
  quoted_amount: decimal,
  availability_note: z.string().nullable(),
  created_at: isoDate,
  updated_at: isoDate,
});

export const matchCandidateSchema = z.object({
  worker_id: uuid,
  suburb: z.string(),
  travel_means: z.string().nullable(),
  distance_band: distanceBandSchema,
  distance_km: z.number(),
  grade: gradeSchema,
  on_time_rate: decimal,
  dispute_rate: decimal,
  fill_rate: decimal,
  jobs_completed: z.number().int(),
  reason: z.string(),
  quoted_amount: nullableDecimal,
  availability_note: z.string().nullable(),
  quoted_at: isoDate.nullable(),
});

export const disputeSchema = z.object({
  id: uuid,
  job_id: uuid,
  raised_by_id: uuid,
  reason: z.string(),
  status: z.string(),
  worker_response: z.string().nullable(),
  before_photo_url: z.string().nullable(),
  after_photo_url: z.string().nullable(),
  created_at: isoDate,
  responded_at: isoDate.nullable(),
});

export const recordEntrySchema = z.object({
  id: uuid,
  job_id: uuid,
  worker_id: uuid,
  what_was_done: z.string(),
  client_words: z.string().nullable(),
  before_photo_url: z.string().nullable(),
  after_photo_url: z.string().nullable(),
  signed_off_at: isoDate,
});

export const messageSchema = z.object({
  id: uuid,
  job_id: uuid,
  sender_id: uuid,
  message_type: messageTypeSchema,
  body: z.string().nullable(),
  media_url: z.string().nullable(),
  duration_seconds: z.number().int().nullable(),
  latitude: nullableDecimal,
  longitude: nullableDecimal,
  created_at: isoDate,
  read_at: isoDate.nullable(),
});

export const skillSchema = z.object({
  id: uuid,
  worker_id: uuid,
  trade: tradeSchema,
  grade: gradeSchema.nullable(),
  proof_url: z.string().nullable(),
});

export const serviceAreaSchema = z.object({
  id: uuid,
  worker_id: uuid,
  suburb: z.string(),
  travel_means: z.string().nullable(),
});

export const standingSchema = z.object({
  worker_id: uuid,
  grade: gradeSchema,
  on_time_rate: decimal,
  dispute_rate: decimal,
  fill_rate: decimal,
  jobs_completed: z.number().int(),
  is_frozen: z.boolean(),
});

export const referenceSchema = z.object({
  id: uuid,
  worker_id: uuid,
  name: z.string(),
  phone: z.string(),
  created_at: isoDate,
});

export const suburbSchema = z.object({
  name: z.string(),
  latitude: decimal,
  longitude: decimal,
});

export type Role = z.infer<typeof roleSchema>;
export type Trade = z.infer<typeof tradeSchema>;
export type Grade = z.infer<typeof gradeSchema>;
export type DistanceBand = z.infer<typeof distanceBandSchema>;
export type JobStatus = z.infer<typeof jobStatusSchema>;
export type MessageType = z.infer<typeof messageTypeSchema>;
export type User = z.infer<typeof userSchema>;
export type Job = z.infer<typeof jobSchema>;
export type MyJob = z.infer<typeof myJobSchema>;
export type OpenJob = z.infer<typeof openJobSchema>;
export type MyOffer = z.infer<typeof myOfferSchema>;
export type JobOffer = z.infer<typeof jobOfferSchema>;
export type MatchCandidate = z.infer<typeof matchCandidateSchema>;
export type Dispute = z.infer<typeof disputeSchema>;
export type RecordEntry = z.infer<typeof recordEntrySchema>;
export type Message = z.infer<typeof messageSchema>;
export type Skill = z.infer<typeof skillSchema>;
export type ServiceArea = z.infer<typeof serviceAreaSchema>;
export type Standing = z.infer<typeof standingSchema>;
export type Reference = z.infer<typeof referenceSchema>;
export type Suburb = z.infer<typeof suburbSchema>;
