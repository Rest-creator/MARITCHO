import type { Page, Route } from "@playwright/test";

import type {
  MatchCandidate,
  Message,
  MyJob,
  MyOffer,
  OpenJob,
  ServiceArea,
  Skill,
  Standing,
  Suburb,
  User,
} from "../../src/core/api/schemas";

/*
 * A small, fixed world for screenshots: one buyer, one worker, a few jobs
 * in Bulawayo. Every id and time is a constant, so a screenshot only
 * changes when the UI does.
 */

/** Tuesday 14 Oct 2026, 09:30 in Harare — "Good morning". */
export const NOW = new Date("2026-10-14T07:30:00Z");

function minutesAgo(minutes: number): string {
  return new Date(NOW.getTime() - minutes * 60_000).toISOString();
}

export const BUYER: User = { id: "buyer-1", phone: "+263771234567", role: "BUYER" };
export const WORKER: User = { id: "worker-1", phone: "+263782345678", role: "WORKER" };

export const PROFILE = {
  BUYER: { name: "Rudo Ncube", phone: BUYER.phone, lastSuburb: "Hillside", lastAddress: "" },
  WORKER: { name: "Tendai Moyo", phone: WORKER.phone, homeSuburb: "Hillside", travelKm: 10 },
} as const;

const SUBURBS: Suburb[] = [
  { name: "Hillside", latitude: -20.185, longitude: 28.63 },
  { name: "Kumalo", latitude: -20.175, longitude: 28.645 },
  { name: "Njube", latitude: -20.197, longitude: 28.542 },
  { name: "Suburbs", latitude: -20.145, longitude: 28.6 },
];

function job(overrides: Partial<MyJob> & Pick<MyJob, "id" | "status">): MyJob {
  return {
    buyer_id: BUYER.id,
    worker_id: null,
    trade: "PLUMBING",
    suburb: "Hillside",
    address: "14 Harrow Rd",
    landmark_narrative: "Blue gate opposite the church",
    latitude: null,
    longitude: null,
    problem_description: "Kitchen sink is leaking under the basin\nNeeded: Today",
    problem_photo_url: null,
    budget_amount: 40,
    currency: "USD",
    labor_amount: null,
    materials_amount: null,
    quote_amount: null,
    created_at: minutesAgo(25),
    updated_at: minutesAgo(25),
    offer_count: 0,
    ...overrides,
  };
}

export const OPEN_JOB_ID = "job-open";
export const LIVE_JOB_ID = "job-live";
export const EXPERT_ID = "worker-expert";

const OPEN_JOB = job({ id: OPEN_JOB_ID, status: "MATCHED", offer_count: 2 });
const LIVE_JOB = job({
  id: LIVE_JOB_ID,
  status: "IN_PROGRESS",
  worker_id: WORKER.id,
  trade: "ELECTRICAL",
  suburb: "Kumalo",
  address: "7 Fife St",
  landmark_narrative: null,
  problem_description: "Lights keep tripping in the lounge\nNeeded: This week",
  budget_amount: null,
  labor_amount: 35,
  materials_amount: 10,
  quote_amount: 45,
  created_at: minutesAgo(60 * 26),
  updated_at: minutesAgo(40),
});
const BOOKED_JOB = job({
  id: "job-booked",
  status: "BOOKED",
  worker_id: WORKER.id,
  trade: "PLUMBING",
  suburb: "Njube",
  address: "22 Lobengula St",
  problem_description: "Geyser is dripping from the overflow pipe\nNeeded: Today",
  budget_amount: 60,
  created_at: minutesAgo(90),
  updated_at: minutesAgo(15),
});
const DONE_JOB = job({
  id: "job-done",
  status: "COMPLETED",
  worker_id: WORKER.id,
  trade: "SOLAR",
  suburb: "Suburbs",
  problem_description: "Solar inverter keeps beeping at night",
  labor_amount: 50,
  materials_amount: 0,
  quote_amount: 50,
  created_at: minutesAgo(60 * 24 * 5),
  updated_at: minutesAgo(60 * 24 * 4),
});

const MATCHES: MatchCandidate[] = [
  {
    worker_id: EXPERT_ID,
    suburb: "Hillside",
    travel_means: "Kombi",
    distance_band: "SAME_SUBURB",
    distance_km: 0.8,
    grade: "EXPERT",
    on_time_rate: 96,
    dispute_rate: 2,
    fill_rate: 91,
    jobs_completed: 48,
    reason: "SAME_SUBURB; grade EXPERT",
    quoted_amount: 40,
    availability_note: "Can come at 2pm",
    quoted_at: minutesAgo(10),
  },
  {
    worker_id: "worker-journeyman",
    suburb: "Kumalo",
    travel_means: null,
    distance_band: "NEARBY",
    distance_km: 2.4,
    grade: "JOURNEYMAN",
    on_time_rate: 88,
    dispute_rate: 5,
    fill_rate: 80,
    jobs_completed: 12,
    reason: "NEARBY; grade JOURNEYMAN",
    quoted_amount: 35,
    availability_note: "Tomorrow morning",
    quoted_at: minutesAgo(5),
  },
  {
    worker_id: "worker-new",
    suburb: "Njube",
    travel_means: null,
    distance_band: "MODERATE",
    distance_km: 6.1,
    grade: "REGISTERED",
    on_time_rate: 0,
    dispute_rate: 0,
    fill_rate: 0,
    jobs_completed: 0,
    reason: "MODERATE; grade REGISTERED",
    quoted_amount: null,
    availability_note: null,
    quoted_at: null,
  },
];

const OPEN_JOBS: OpenJob[] = [
  {
    job_id: OPEN_JOB_ID,
    trade: "PLUMBING",
    suburb: "Hillside",
    budget_amount: 40,
    problem_description: OPEN_JOB.problem_description,
    created_at: OPEN_JOB.created_at,
    distance_band: "SAME_SUBURB",
    distance_km: 0.8,
  },
  {
    job_id: "job-open-2",
    trade: "ELECTRICAL",
    suburb: "Kumalo",
    budget_amount: null,
    problem_description: "Plug points in the kitchen stopped working\nNeeded: This week",
    created_at: minutesAgo(120),
    distance_band: "NEARBY",
    distance_km: 2.4,
  },
];

const MY_OFFERS: MyOffer[] = [
  {
    id: "offer-1",
    job_id: "job-open-2",
    quoted_amount: 25,
    availability_note: "Tomorrow at 9am",
    created_at: minutesAgo(30),
    updated_at: minutesAgo(30),
    job_trade: "ELECTRICAL",
    job_suburb: "Kumalo",
    job_status: "MATCHED",
  },
];

function message(id: string, sender: User, minutes: number, body: string): Message {
  return {
    id,
    job_id: LIVE_JOB_ID,
    sender_id: sender.id,
    message_type: "TEXT",
    body,
    media_url: null,
    duration_seconds: null,
    latitude: null,
    longitude: null,
    created_at: minutesAgo(minutes),
    read_at: minutesAgo(minutes - 1),
  };
}

const MESSAGES: Message[] = [
  message("m1", BUYER, 50, "Hi, the gate code is 1234. Dogs are friendly."),
  message("m2", WORKER, 48, "Thanks. I'll be there in 20 minutes."),
  message(
    "m3",
    WORKER,
    41,
    "Found it — a burnt wire on the lounge circuit. $35 labour + $10 parts.",
  ),
  message("m4", BUYER, 40, "Okay, go ahead."),
];

const SKILLS: Skill[] = [
  { id: "skill-1", worker_id: WORKER.id, trade: "PLUMBING", grade: "JOURNEYMAN", proof_url: null },
  { id: "skill-2", worker_id: WORKER.id, trade: "ELECTRICAL", grade: null, proof_url: null },
];

const SERVICE_AREAS: ServiceArea[] = [
  { id: "area-1", worker_id: WORKER.id, suburb: "Hillside", travel_means: null },
];

const STANDING: Standing = {
  worker_id: WORKER.id,
  grade: "JOURNEYMAN",
  on_time_rate: 92,
  dispute_rate: 3,
  fill_rate: 85,
  jobs_completed: 14,
  is_frozen: false,
};

type Who = "BUYER" | "WORKER" | null;

function responsesFor(who: Who): Record<string, unknown> {
  const user = who === "BUYER" ? BUYER : who === "WORKER" ? WORKER : null;
  return {
    "GET session": user,
    "GET suburbs": SUBURBS,
    "GET jobs/mine": [OPEN_JOB, LIVE_JOB, DONE_JOB],
    [`GET jobs/${OPEN_JOB_ID}`]: OPEN_JOB,
    [`GET jobs/${LIVE_JOB_ID}`]: LIVE_JOB,
    [`GET jobs/${OPEN_JOB_ID}/matches`]: MATCHES,
    [`GET jobs/${LIVE_JOB_ID}/messages`]: MESSAGES,
    [`POST jobs/${LIVE_JOB_ID}/messages/read`]: null,
    "GET jobs/open": OPEN_JOBS,
    "GET jobs/assigned": [BOOKED_JOB, LIVE_JOB, DONE_JOB],
    "GET jobs/my-offers": MY_OFFERS,
    "GET workers/me/skills": SKILLS,
    "GET workers/me/service-areas": SERVICE_AREAS,
    "GET workers/me/standing": STANDING,
    "GET workers/me/references": [],
  };
}

/**
 * Answer every `/api/*` call from the fixed world above, signed in as
 * `who` (or nobody). Anything unexpected fails loudly rather than letting
 * a screenshot capture an error state by accident.
 */
export async function stubWorld(page: Page, who: Who): Promise<string[]> {
  const unexpected: string[] = [];
  const responses = responsesFor(who);

  await page.clock.setFixedTime(NOW);
  if (who !== null) {
    const profile = { ...PROFILE[who] };
    await page.addInitScript((value: string) => {
      window.localStorage.setItem("maricho-profile", value);
    }, JSON.stringify(profile));
  }

  await page.route("**/api/**", async (route: Route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace(/^\/api\//, "");
    if (path === "session/socket-token") {
      // No live socket in screenshots: the chat shows its polling state.
      await route.fulfill({ status: 401, json: { detail: "No socket in visual tests" } });
      return;
    }
    const key = `${request.method()} ${path}`;
    if (key in responses) {
      const body = responses[key];
      await route.fulfill(
        body === null && request.method() === "POST" ? { status: 204 } : { json: body },
      );
      return;
    }
    unexpected.push(key);
    await route.fulfill({ status: 404, json: { detail: `No fixture for ${key}` } });
  });

  return unexpected;
}
