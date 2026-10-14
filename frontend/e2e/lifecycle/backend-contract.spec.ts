import { expect, test } from "@playwright/test";

import { BACKEND_ROUTES, PROXIED_ROUTES, type BackendRoute } from "../../src/server/backend-routes";

/*
 * ADR-009 drift check: every backend route the BFF relies on must exist,
 * with that method, in the running backend's OpenAPI document. A backend
 * rename fails here, in CI, instead of silently switching a feature off.
 */

type OpenApi = { paths: Record<string, Record<string, unknown>> };

const routes: readonly BackendRoute[] = [...Object.values(BACKEND_ROUTES), ...PROXIED_ROUTES];

test("every backend route the BFF uses exists in the backend's OpenAPI", async ({ request }) => {
  const backend = process.env.BACKEND_URL;
  expect(backend, "run via `npm run test:e2e`, which starts the backend").toBeTruthy();

  const response = await request.get(`${backend}/openapi.json`);
  expect(response.ok()).toBe(true);
  const spec = (await response.json()) as OpenApi;

  const missing = routes
    .filter((route) => spec.paths[route.path]?.[route.method.toLowerCase()] === undefined)
    .map((route) => `${route.method} ${route.path}`);

  expect(missing, "routes in src/server/backend-routes.ts the backend doesn't serve").toEqual([]);
});
