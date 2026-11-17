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
const HAS_OFFSET = /(?:[zZ]|[+-]\d{2}(?::?\d{2})?)$/;
const IS_DATE_TIME = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;

/**
 * The API writes times in UTC, but some responses (a just-sent message, the
 * live chat socket, offline-cached data) arrived without an offset, e.g.
 * "2026-11-17T10:00:00". `new Date()` reads that as *local* time, so messages
 * showed 2 hours early in Zimbabwe. Date-times without an offset are UTC.
 */
export function normalizeIsoDate(value: string): string {
  return IS_DATE_TIME.test(value) && !HAS_OFFSET.test(value) ? `${value}Z` : value;
}

const isoDate = z.string().min(1).transform(normalizeIsoDate);

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
export const neededBySchema = z.enum(["TODAY", "THIS_WEEK", "FLEXIBLE"]);
export const reviewTagSchema = z.enum([
  "CLEAN",
  "ON_TIME",
  "PROFESSIONAL",
  "GOOD_COMMUNICATION",
  "QUALITY_WORK",
  "FAIR_PRICE",
  "RELIABLE",
]);

export const tokenSchema = z.object({
  access_token: z.string().min(1),
  token_type: z.string(),
});

export const userSchema = z.object({
  id: uuid,
  phone: z.string(),
  role: roleSchema,
  display_name: z.string().nullable().optional(),
  is_available: z.boolean().optional(),
  travel_km: z.number().int().optional(),
  home_suburb: z.string().nullable().optional(),
  next_of_kin_phone: z.string().nullable().optional(),
  created_at: isoDate.nullable().optional(),
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
  needed_by: neededBySchema.optional(),
  worker_display_name: z.string().nullable().optional(),
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
  needed_by: neededBySchema.optional(),
  similarity_score: z.number().nullable().optional(),
});

export const jobSearchResultSchema = z.object({
  job_id: uuid,
  trade: tradeSchema,
  suburb: z.string(),
  budget_amount: nullableDecimal,
  problem_description: z.string().nullable(),
  created_at: isoDate.nullable(),
  needed_by: neededBySchema.optional(),
  similarity_score: z.number(),
  matched_trade: tradeSchema.nullable().optional(),
});

export const skillSearchResultSchema = z.object({
  id: z.string(),
  label: z.string(),
  trade: tradeSchema.nullable(),
  category: z.string(),
  similarity_score: z.number(),
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
  needed_by: neededBySchema.optional(),
});

export const jobOfferSchema = z.object({
  id: uuid,
  job_id: uuid,
  worker_id: uuid,
  quoted_amount: decimal,
  availability_note: z.string().nullable(),
  created_at: isoDate,
  updated_at: isoDate,
  worker_display_name: z.string().nullable().optional(),
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
  display_name: z.string().nullable().optional(),
  rating_average: nullableDecimal.optional(),
  rating_count: z.number().int().optional(),
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

export const jobEligibilitySchema = z.object({
  is_eligible: z.boolean(),
  required_trade: tradeSchema,
  matched_by: z.enum(["TRADE", "SIMILARITY"]).nullable(),
  similarity_score: z.number().nullable(),
  reason: z.string(),
});

export const conversationUnreadSchema = z.object({
  job_id: uuid,
  unread_count: z.number().int().nonnegative(),
  last_message_at: isoDate.nullable(),
  last_message_preview: z.string().nullable(),
  last_sender_id: uuid.nullable(),
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
  rating_average: nullableDecimal.optional(),
  rating_count: z.number().int().optional(),
});

export const referenceSchema = z.object({
  id: uuid,
  worker_id: uuid,
  name: z.string(),
  phone: z.string(),
  created_at: isoDate,
});

export const workerVettingSchema = z.object({
  worker_id: uuid,
  id_photo_url: z.string().nullable(),
  id_submitted_at: isoDate.nullable(),
  reference_count: z.number().int(),
  vouch_count: z.number().int(),
  grade: gradeSchema,
});

export const vouchSchema = z.object({
  id: uuid,
  worker_id: uuid,
  voucher_id: uuid,
  created_at: isoDate,
});

export const suburbSchema = z.object({
  name: z.string(),
  latitude: decimal,
  longitude: decimal,
});

export const workerWorkRecordSchema = z.object({
  job_id: uuid,
  what_was_done: z.string(),
  client_words: z.string().nullable().optional(),
  before_photo_url: z.string().nullable().optional(),
  after_photo_url: z.string().nullable().optional(),
  signed_off_at: isoDate.nullable().optional(),
});

export const workerSummarySchema = z.object({
  worker_id: uuid,
  display_name: z.string().nullable().optional(),
  suburb: z.string().nullable().optional(),
  trades: z.array(tradeSchema),
  proof_urls: z.array(z.string()).optional().default([]),
  grade: gradeSchema,
  on_time_rate: decimal,
  dispute_rate: decimal,
  fill_rate: decimal,
  jobs_completed: z.number().int(),
  rating_average: nullableDecimal.optional(),
  rating_count: z.number().int().optional(),
  is_available: z.boolean().optional().default(true),
  travel_km: z.number().int().optional().default(50),
  travel_means: z.string().nullable().optional(),
  distance_band: distanceBandSchema.nullable().optional(),
  distance_km: z.number().nullable().optional(),
  similarity_score: z.number().nullable().optional(),
});

export const workerProfileSchema = workerSummarySchema.extend({
  service_areas: z.array(z.string()).optional().default([]),
  reference_count: z.number().int().optional().default(0),
  recent_work: z.array(workerWorkRecordSchema).optional().default([]),
});

/* Screen bundles from the BFF (`/api/screens/*`, ADR-009 phase 2). */

export const workerWorkScreenSchema = z.object({
  standing: standingSchema,
  offers: z.array(myOfferSchema),
  assigned: z.array(jobSchema),
});

export const workerHomeScreenSchema = z.object({
  skills: z.array(skillSchema),
  open_jobs: z.array(openJobSchema),
  offers: z.array(myOfferSchema),
});

export type Role = z.infer<typeof roleSchema>;
export type Trade = z.infer<typeof tradeSchema>;
export type Grade = z.infer<typeof gradeSchema>;
export type DistanceBand = z.infer<typeof distanceBandSchema>;
export type JobStatus = z.infer<typeof jobStatusSchema>;
export type MessageType = z.infer<typeof messageTypeSchema>;
export type NeededBy = z.infer<typeof neededBySchema>;
export type ReviewTag = z.infer<typeof reviewTagSchema>;
export type User = z.infer<typeof userSchema>;
export type Job = z.infer<typeof jobSchema>;
export type MyJob = z.infer<typeof myJobSchema>;
export type OpenJob = z.infer<typeof openJobSchema>;
export type JobSearchResult = z.infer<typeof jobSearchResultSchema>;
export type SkillSearchResult = z.infer<typeof skillSearchResultSchema>;
export type MyOffer = z.infer<typeof myOfferSchema>;
export type JobOffer = z.infer<typeof jobOfferSchema>;
export type MatchCandidate = z.infer<typeof matchCandidateSchema>;
export type Dispute = z.infer<typeof disputeSchema>;
export type RecordEntry = z.infer<typeof recordEntrySchema>;
export type Message = z.infer<typeof messageSchema>;
export type ConversationUnread = z.infer<typeof conversationUnreadSchema>;
export type JobEligibility = z.infer<typeof jobEligibilitySchema>;
export type Skill = z.infer<typeof skillSchema>;
export type ServiceArea = z.infer<typeof serviceAreaSchema>;
export type Standing = z.infer<typeof standingSchema>;
export type Reference = z.infer<typeof referenceSchema>;
export type WorkerVetting = z.infer<typeof workerVettingSchema>;
export type Vouch = z.infer<typeof vouchSchema>;
export type Suburb = z.infer<typeof suburbSchema>;
export type WorkerWorkRecord = z.infer<typeof workerWorkRecordSchema>;
export type WorkerSummary = z.infer<typeof workerSummarySchema>;
export type WorkerProfile = z.infer<typeof workerProfileSchema>;
export type WorkerWorkScreen = z.infer<typeof workerWorkScreenSchema>;
export type WorkerHomeScreen = z.infer<typeof workerHomeScreenSchema>;
