import { readFile } from "node:fs/promises";
import path from "node:path";

import { NextResponse } from "next/server";

const DOWNLOADS_ROOT = path.resolve(process.cwd(), "public", "downloads");

type RouteContext = { params: Promise<{ filename: string }> };

export async function GET(_request: Request, context: RouteContext): Promise<Response> {
  const { filename } = await context.params;
  if (filename === "" || filename !== path.basename(filename)) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const filePath = path.join(DOWNLOADS_ROOT, filename);
  try {
    const file = await readFile(filePath);
    return new Response(new Uint8Array(file), {
      headers: {
        "cache-control": "public, max-age=3600",
        "content-disposition": `attachment; filename="${filename}"`,
        "content-type": "application/vnd.android.package-archive",
      },
    });
  } catch (error: unknown) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") {
      return NextResponse.json({ detail: "Not found" }, { status: 404 });
    }
    throw error;
  }
}
