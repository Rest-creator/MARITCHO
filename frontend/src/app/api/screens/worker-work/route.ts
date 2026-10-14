import type { NextRequest, NextResponse } from "next/server";

import { BACKEND_ROUTES } from "@/server/backend-routes";
import { screenBundle } from "@/server/screen-bundle";

/** Everything the worker's "My work" screen shows, in one request. */
export function GET(request: NextRequest): Promise<NextResponse> {
  return screenBundle(request, {
    standing: BACKEND_ROUTES.standing,
    offers: BACKEND_ROUTES.myOffers,
    assigned: BACKEND_ROUTES.assignedJobs,
  });
}
