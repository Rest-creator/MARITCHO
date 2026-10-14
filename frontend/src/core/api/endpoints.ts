import { z } from "zod";

import { apiRequest } from "@/core/api/http";
import {
  disputeSchema,
  jobOfferSchema,
  jobSchema,
  matchCandidateSchema,
  messageSchema,
  myJobSchema,
  myOfferSchema,
  openJobSchema,
  recordEntrySchema,
  referenceSchema,
  serviceAreaSchema,
  skillSchema,
  standingSchema,
  suburbSchema,
  type Dispute,
  type Job,
  type JobOffer,
  type MatchCandidate,
  type Message,
  type MessageType,
  type MyJob,
  type MyOffer,
  type OpenJob,
  type RecordEntry,
  type Reference,
  type ServiceArea,
  type Skill,
  type Standing,
  type Suburb,
  type Trade,
} from "@/core/api/schemas";

/* ---------- Request payloads ---------- */

export interface CreateJobInput {
  trade: Trade;
  suburb: string;
  address: string;
  problem_description: string;
  landmark_narrative?: string;
  budget_amount?: number;
  problem_photo_url?: string;
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

export function fetchOpenJobs(): Promise<OpenJob[]> {
  return apiRequest("/jobs/open", { schema: z.array(openJobSchema) });
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

/* ---------- Workers ---------- */

export function fetchSkills(): Promise<Skill[]> {
  return apiRequest("/workers/me/skills", { schema: z.array(skillSchema) });
}

export function registerSkill(trade: Trade): Promise<Skill> {
  return apiRequest("/workers/me/skills", {
    method: "POST",
    body: { trade },
    schema: skillSchema,
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

export function fetchReferences(): Promise<Reference[]> {
  return apiRequest("/workers/me/references", { schema: z.array(referenceSchema) });
}

/* ---------- Reference data ---------- */

export function fetchSuburbs(): Promise<Suburb[]> {
  return apiRequest("/suburbs", { schema: z.array(suburbSchema) });
}
