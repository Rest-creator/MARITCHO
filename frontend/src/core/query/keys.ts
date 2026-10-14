/** Central query-key factory so invalidation never drifts from the reads. */
export const queryKeys = {
  session: ["session"] as const,
  myJobs: ["jobs", "mine"] as const,
  job: (jobId: string) => ["jobs", "detail", jobId] as const,
  matches: (jobId: string) => ["jobs", "matches", jobId] as const,
  record: (jobId: string) => ["jobs", "record", jobId] as const,
  disputes: (jobId: string) => ["jobs", "disputes", jobId] as const,
  openJobs: ["jobs", "open"] as const,
  assignedJobs: ["jobs", "assigned"] as const,
  myOffers: ["jobs", "my-offers"] as const,
  messages: (jobId: string) => ["messages", jobId] as const,
  skills: ["workers", "skills"] as const,
  serviceAreas: ["workers", "service-areas"] as const,
  standing: ["workers", "standing"] as const,
  references: ["workers", "references"] as const,
  suburbs: ["suburbs"] as const,
  mediaUploads: ["media", "uploads-available"] as const,
  /** Screen bundles; under "jobs" so any job change can refresh them too. */
  screens: ["jobs", "screen"] as const,
  workerWorkScreen: ["jobs", "screen", "worker-work"] as const,
  workerHomeScreen: ["jobs", "screen", "worker-home"] as const,
};

/**
 * Mutation keys double as the registry for offline replay: a mutation
 * queued while offline is persisted with its key and re-run on reload
 * using the default mutationFn registered for that key.
 */
export const mutationKeys = {
  createJob: ["createJob"] as const,
  submitOffer: ["submitOffer"] as const,
  bookJob: ["bookJob"] as const,
  submitQuote: ["submitQuote"] as const,
  completeJob: ["completeJob"] as const,
  raiseDispute: ["raiseDispute"] as const,
  respondToDispute: ["respondToDispute"] as const,
  sendMessage: ["sendMessage"] as const,
  registerSkill: ["registerSkill"] as const,
  registerServiceArea: ["registerServiceArea"] as const,
};
