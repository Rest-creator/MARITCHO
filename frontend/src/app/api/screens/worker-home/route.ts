import type { NextRequest, NextResponse } from "next/server";

import { BACKEND_ROUTES } from "@/server/backend-routes";
import { screenBundle } from "@/server/screen-bundle";

/** Everything the worker's "Jobs near you" screen shows, in one request. */
export function GET(request: NextRequest): Promise<NextResponse> {
  return screenBundle(request, {
    skills: BACKEND_ROUTES.skills,
    open_jobs: BACKEND_ROUTES.openJobs,
    offers: BACKEND_ROUTES.myOffers,
  });
}
