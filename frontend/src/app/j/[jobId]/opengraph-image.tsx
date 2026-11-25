import { ImageResponse } from "next/og";

import { shareFacts, shareHeadline, shareTradeLabel } from "@/features/jobs/job-share";
import { getJobShare } from "@/server/job-share";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "A job on Maritcho";

type Props = { params: Promise<{ jobId: string }> };

/** The picture in a shared job link's preview card: the job and the suburb, nothing else. */
export default async function Image({ params }: Props) {
  const { jobId } = await params;
  const result = await getJobShare(jobId);
  const job = result.kind === "found" ? result.job : null;
  const headline = job ? shareHeadline(job) : "Jobs near you on Maritcho";
  const facts = job ? (job.is_open ? shareFacts(job) : ["This job has been filled"]) : [];

  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "64px 72px",
        color: "#ffffff",
        background: "linear-gradient(135deg, #222576 0%, #2d2e83 55%, #34519f 100%)",
        fontFamily: "sans-serif",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: 18,
            background: "#00abe3",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 40,
            fontWeight: 800,
          }}
        >
          m
        </div>
        <div style={{ fontSize: 40, fontWeight: 700, letterSpacing: -1 }}>maritcho</div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        {job && (
          <div style={{ display: "flex", fontSize: 32, color: "#7dd3fc", fontWeight: 600 }}>
            {`${shareTradeLabel(job.trade)} · ${job.suburb}`}
          </div>
        )}
        <div style={{ fontSize: 76, fontWeight: 800, lineHeight: 1.05, letterSpacing: -2 }}>
          {headline}
        </div>
        {facts.length > 0 && (
          <div style={{ display: "flex", gap: 14 }}>
            {facts.map((fact) => (
              <div
                key={fact}
                style={{
                  display: "flex",
                  fontSize: 28,
                  padding: "10px 22px",
                  borderRadius: 999,
                  background: "rgba(255,255,255,0.14)",
                  border: "2px solid rgba(255,255,255,0.28)",
                }}
              >
                {fact}
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: "flex", fontSize: 30, color: "#dbeafe" }}>
        See the details and send your price on Maritcho →
      </div>
    </div>,
    size,
  );
}
