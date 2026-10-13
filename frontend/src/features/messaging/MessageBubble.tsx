import { Icon } from "@/components/ui/Icon";
import type { Message } from "@/core/api/schemas";

type Props = {
  message: Pick<
    Message,
    "message_type" | "body" | "media_url" | "duration_seconds" | "latitude" | "longitude"
  >;
  isMine: boolean;
  isPending?: boolean;
};

const WAVE_HEIGHTS = [8, 16, 12, 20, 10, 14, 8, 16, 6, 12] as const;

function formatDuration(seconds: number | null): string {
  const total = seconds ?? 0;
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

export function MessageBubble({ message, isMine, isPending = false }: Props) {
  const classes = [
    "bubble",
    isMine ? "bubble--out" : "bubble--in",
    isPending ? "bubble--pending" : "",
  ]
    .filter(Boolean)
    .join(" ");

  if (
    message.message_type === "LOCATION" &&
    message.latitude !== null &&
    message.longitude !== null
  ) {
    const href = `https://www.google.com/maps?q=${message.latitude},${message.longitude}`;
    return (
      <a
        className={classes}
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        style={{ display: "flex", gap: 8, alignItems: "center", color: "inherit" }}
      >
        <Icon name="pin" size={18} />
        Shared a location — open map
      </a>
    );
  }

  if (message.message_type === "VOICE_NOTE") {
    return (
      <div
        className={classes}
        style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px" }}
      >
        {message.media_url ? (
          <audio controls preload="none" src={message.media_url} style={{ maxWidth: 200 }} />
        ) : (
          <div className="voice-wave" aria-hidden="true">
            {WAVE_HEIGHTS.map((height, index) => (
              <span key={index} style={{ height }} />
            ))}
          </div>
        )}
        <span className="meta">Voice note · {formatDuration(message.duration_seconds)}</span>
      </div>
    );
  }

  if (message.message_type === "PHOTO" && message.media_url) {
    return (
      <div className={classes} style={{ padding: 6 }}>
        {/* eslint-disable-next-line @next/next/no-img-element -- remote user media, size unknown */}
        <img src={message.media_url} alt="Photo sent in chat" loading="lazy" />
        {message.body && <div style={{ padding: "6px 8px 2px" }}>{message.body}</div>}
      </div>
    );
  }

  return <div className={classes}>{message.body}</div>;
}
