import { z } from "zod";

import { apiRequest } from "@/core/api/http";
import {
  disputeSchema,
  jobOfferSchema,
  jobSchema,
  jobSearchResultSchema,
  matchCandidateSchema,
  conversationUnreadSchema,
  jobEligibilitySchema,
  messageSchema,
  myJobSchema,
  myOfferSchema,
  openJobSchema,
  recordEntrySchema,
  referenceSchema,
  serviceAreaSchema,
  skillSchema,
  skillSearchResultSchema,
  standingSchema,
  suburbSchema,
  userSchema,
  vouchSchema,
  workerHomeScreenSchema,
  workerProfileSchema,
  workerSummarySchema,
  workerVettingSchema,
  workerWorkScreenSchema,
  type Dispute,
  type Job,
  type JobOffer,
  type JobSearchResult,
  type MatchCandidate,
  type ConversationUnread,
  type JobEligibility,
  type Message,
  type MessageType,
  type MyJob,
  type MyOffer,
  type NeededBy,
  type OpenJob,
  type RecordEntry,
  type Reference,
  type ReviewTag,
  type ServiceArea,
  type Skill,
  type SkillSearchResult,
  type Standing,
  type Suburb,
  type Trade,
  type User,
  type Vouch,
  type WorkerHomeScreen,
  type WorkerProfile,
  type WorkerSummary,
  type WorkerVetting,
  type WorkerWorkScreen,
} from "@/core/api/schemas";

/* ---------- Request payloads ---------- */

export interface CreateJobInput {
  trade: Trade;
  suburb: string;
  address: string;
  problem_description: string;
  landmark_narrative?: string;
  latitude?: number;
  longitude?: number;
  budget_amount?: number;
  problem_photo_url?: string;
  needed_by?: NeededBy;
}

export interface SubmitOfferInput {
  jobId: string;
  quoted_amount: number;
  availability_note?: string;
}

export interface BookJobInput {
  jobId: string;
  worker_id: string;
  deposit_amount: number;
  currency: "USD" | "ECOCASH" | "ZWG";
}

export interface SubmitQuoteInput {
  jobId: string;
  labor_amount: number;
  materials_amount: number;
}

export interface CompleteJobInput {
  jobId: string;
  what_was_done: string;
  client_words?: string;
}

export interface SubmitReviewInput {
  jobId: string;
  rating: number;
  tags: ReviewTag[];
  comment?: string;
}

export interface RaiseDisputeInput {
  jobId: string;
  reason: string;
}

export interface RespondToDisputeInput {
  jobId: string;
  response: string;
}

export interface SendMessageInput {
  jobId: string;
  message_type: MessageType;
  body?: string;
  media_url?: string;
  duration_seconds?: number;
  latitude?: number;
  longitude?: number;
}

export interface RegisterServiceAreaInput {
  suburb: string;
  travel_means?: string;
}

export type RegisterSkillInput = Trade | { trade: Trade; proof_url?: string };

export interface UpdateUserProfileInput {
  display_name?: string;
  is_available?: boolean;
  travel_km?: number;
  home_suburb?: string;
  next_of_kin_phone?: string;
  role?: "BUYER" | "WORKER";
}

export interface SubmitIdPhotoInput {
  id_photo_url: string;
}

export interface AddReferenceInput {
  name: string;
  phone: string;
}

export interface VouchForWorkerInput {
  worker_id: string;
}

/* ---------- Jobs ---------- */

export function fetchMyJobs(): Promise<MyJob[]> {
  return apiRequest("/jobs/mine", { schema: z.array(myJobSchema) });
}

export function fetchJob(jobId: string): Promise<Job> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}`, { schema: jobSchema });
}

export function fetchMatches(jobId: string): Promise<MatchCandidate[]> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/matches`, {
    schema: z.array(matchCandidateSchema),
  });
}

export function fetchRecord(jobId: string): Promise<RecordEntry> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/record`, { schema: recordEntrySchema });
}

export function fetchOpenJobs(query?: string, signal?: AbortSignal): Promise<OpenJob[]> {
  const trimmed = query?.trim() ?? "";
  const search = trimmed === "" ? "" : `?q=${encodeURIComponent(trimmed)}`;
  return apiRequest(`/jobs/open${search}`, { schema: z.array(openJobSchema), signal });
}

export interface SearchJobsParams {
  q: string;
  trade?: Trade;
  suburb?: string;
  limit?: number;
}

export function searchOpenJobs(
  params: SearchJobsParams,
  signal?: AbortSignal,
): Promise<JobSearchResult[]> {
  const query = new URLSearchParams({ q: params.q.trim() });
  if (params.trade) query.set("trade", params.trade);
  if (params.suburb) query.set("suburb", params.suburb);
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  return apiRequest(`/jobs/search?${query.toString()}`, {
    schema: z.array(jobSearchResultSchema),
    signal,
  });
}

export function searchSkillsVector(
  query: string,
  signal?: AbortSignal,
): Promise<SkillSearchResult[]> {
  const params = new URLSearchParams({ q: query.trim() });
  return apiRequest(`/jobs/search/skills?${params.toString()}`, {
    schema: z.array(skillSearchResultSchema),
    signal,
  });
}

export function fetchAssignedJobs(): Promise<Job[]> {
  return apiRequest("/jobs/assigned", { schema: z.array(jobSchema) });
}

export function fetchMyOffers(): Promise<MyOffer[]> {
  return apiRequest("/jobs/my-offers", { schema: z.array(myOfferSchema) });
}

export function createJob(input: CreateJobInput): Promise<Job> {
  return apiRequest("/jobs/request", { method: "POST", body: input, schema: jobSchema });
}

export function submitOffer({ jobId, ...body }: SubmitOfferInput): Promise<JobOffer> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/offers`, {
    method: "POST",
    body,
    schema: jobOfferSchema,
  });
}

export function bookJob({ jobId, ...body }: BookJobInput): Promise<Job> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/book`, {
    method: "POST",
    body,
    schema: jobSchema,
  });
}

export function submitQuote({ jobId, ...body }: SubmitQuoteInput): Promise<Job> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/quote`, {
    method: "POST",
    body,
    schema: jobSchema,
  });
}

export function completeJob({ jobId, ...body }: CompleteJobInput): Promise<Job> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/complete`, {
    method: "POST",
    body,
    schema: jobSchema,
  });
}

export function submitReview({ jobId, ...body }: SubmitReviewInput): Promise<void> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/review`, {
    method: "POST",
    body,
  });
}

export function raiseDispute({ jobId, ...body }: RaiseDisputeInput): Promise<Dispute> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/dispute`, {
    method: "POST",
    body,
    schema: disputeSchema,
  });
}

export function fetchDisputes(jobId: string): Promise<Dispute[]> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/disputes`, {
    schema: z.array(disputeSchema),
  });
}

export function respondToDispute({ jobId, ...body }: RespondToDisputeInput): Promise<Dispute> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/dispute/respond`, {
    method: "POST",
    body,
    schema: disputeSchema,
  });
}

/* ---------- Messaging ---------- */

export function fetchMessages(jobId: string): Promise<Message[]> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/messages`, {
    schema: z.array(messageSchema),
  });
}

export function sendMessage({ jobId, ...body }: SendMessageInput): Promise<Message> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/messages`, {
    method: "POST",
    body,
    schema: messageSchema,
  });
}

export function markMessagesRead(jobId: string): Promise<void> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/messages/read`, { method: "POST" });
}

/** Whether the signed-in worker's skills match this job, and why not. */
export function fetchJobEligibility(jobId: string): Promise<JobEligibility> {
  return apiRequest(`/jobs/${encodeURIComponent(jobId)}/eligibility`, {
    schema: jobEligibilitySchema,
  });
}

/** Unread counts and last message for every conversation, newest first. */
export function fetchUnreadSummary(signal?: AbortSignal): Promise<ConversationUnread[]> {
  return apiRequest("/messages/unread", {
    schema: z.array(conversationUnreadSchema),
    signal,
  });
}

/* ---------- Workers ---------- */

export function fetchSkills(): Promise<Skill[]> {
  return apiRequest("/workers/me/skills", { schema: z.array(skillSchema) });
}

export function registerSkill(input: RegisterSkillInput): Promise<Skill> {
  const body = typeof input === "string" ? { trade: input } : input;
  return apiRequest("/workers/me/skills", {
    method: "POST",
    body,
    schema: skillSchema,
  });
}

export function updateUserProfile(input: UpdateUserProfileInput): Promise<User> {
  return apiRequest("/users/me", {
    method: "PATCH",
    body: input,
    schema: userSchema,
  });
}

export function fetchServiceAreas(): Promise<ServiceArea[]> {
  return apiRequest("/workers/me/service-areas", { schema: z.array(serviceAreaSchema) });
}

export function registerServiceArea(input: RegisterServiceAreaInput): Promise<ServiceArea> {
  return apiRequest("/workers/me/service-areas", {
    method: "POST",
    body: input,
    schema: serviceAreaSchema,
  });
}

export function fetchStanding(): Promise<Standing> {
  return apiRequest("/workers/me/standing", { schema: standingSchema });
}

export function fetchWorkerVetting(): Promise<WorkerVetting> {
  return apiRequest("/workers/me/vetting", { schema: workerVettingSchema });
}

export function submitIdPhoto(input: SubmitIdPhotoInput): Promise<WorkerVetting> {
  return apiRequest("/workers/me/vetting/id-photo", {
    method: "POST",
    body: input,
    schema: workerVettingSchema,
  });
}

export function fetchReferences(): Promise<Reference[]> {
  return apiRequest("/workers/me/references", { schema: z.array(referenceSchema) });
}

export function addReference(input: AddReferenceInput): Promise<Reference> {
  return apiRequest("/workers/me/references", {
    method: "POST",
    body: input,
    schema: referenceSchema,
  });
}

export function vouchForWorker(input: VouchForWorkerInput): Promise<Vouch> {
  return apiRequest("/workers/me/vouches", {
    method: "POST",
    body: input,
    schema: vouchSchema,
  });
}

export interface FetchNearbyWorkersParams {
  suburb?: string;
  trade?: Trade;
  q?: string;
}

export function fetchNearbyWorkers(
  params: FetchNearbyWorkersParams = {},
  signal?: AbortSignal,
): Promise<WorkerSummary[]> {
  const query = new URLSearchParams();
  if (params.suburb && params.suburb.trim() !== "") query.set("suburb", params.suburb.trim());
  if (params.trade) query.set("trade", params.trade);
  if (params.q && params.q.trim() !== "") query.set("q", params.q.trim());
  const qs = query.toString();
  return apiRequest(`/workers${qs ? `?${qs}` : ""}`, {
    schema: z.array(workerSummarySchema),
    signal,
  });
}

export function fetchWorkerProfile(
  workerId: string,
  suburb?: string,
  signal?: AbortSignal,
): Promise<WorkerProfile> {
  const qs = suburb && suburb.trim() !== "" ? `?suburb=${encodeURIComponent(suburb.trim())}` : "";
  return apiRequest(`/workers/${encodeURIComponent(workerId)}${qs}`, {
    schema: workerProfileSchema,
    signal,
  });
}

/* ---------- Screens (one request per screen, ADR-009 phase 2) ---------- */

export function fetchWorkerWorkScreen(): Promise<WorkerWorkScreen> {
  return apiRequest("/screens/worker-work", { schema: workerWorkScreenSchema });
}

export function fetchWorkerHomeScreen(): Promise<WorkerHomeScreen> {
  return apiRequest("/screens/worker-home", { schema: workerHomeScreenSchema });
}

/* ---------- Reference data ---------- */

export function fetchSuburbs(): Promise<Suburb[]> {
  return apiRequest("/suburbs", { schema: z.array(suburbSchema) });
}
