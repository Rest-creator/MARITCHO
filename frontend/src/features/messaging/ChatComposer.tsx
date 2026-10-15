"use client";

import { useCallback, useState, type FormEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import { PhotoPicker } from "@/components/ui/PhotoPicker";
import type { SendMessageInput } from "@/core/api/endpoints";
import { isUploadUnavailable } from "@/core/media/upload";
import { useUpload } from "@/core/media/use-upload";
import { useVoiceRecorder, type VoiceRecording } from "@/core/media/use-voice-recorder";
import { formatCountdown } from "@/core/session/sign-in-code";

type Outgoing = Omit<SendMessageInput, "jobId">;

type Props = {
  /** Photos and voice notes can be sent (uploads exist and we're online). */
  canAttach: boolean;
  onSend: (message: Outgoing) => void;
};

/**
 * The chat input row: type a message, or — once uploads exist — send a
 * photo or hold a short voice note instead of typing. The mic replaces the
 * send button while the box is empty, as in WhatsApp.
 */
export function ChatComposer({ canAttach, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState<"photo" | "voice note" | null>(null);
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const { upload } = useUpload();

  const sendUpload = useCallback(
    async (file: Blob, kind: "photo" | "voice_note", extra: Partial<Outgoing>): Promise<void> => {
      setError(null);
      setSending(kind === "photo" ? "photo" : "voice note");
      try {
        const url = await upload(file, kind);
        onSend({
          message_type: kind === "photo" ? "PHOTO" : "VOICE_NOTE",
          media_url: url,
          ...extra,
        });
      } catch (failure: unknown) {
        setError(
          isUploadUnavailable(failure)
            ? "Photos and voice notes can't be sent yet."
            : failure instanceof Error
              ? `Didn't send: ${failure.message}`
              : "Didn't send. Please try again.",
        );
      } finally {
        setSending(null);
      }
    },
    [onSend, upload],
  );

  const handleRecorded = useCallback(
    (recording: VoiceRecording) =>
      void sendUpload(recording.blob, "voice_note", { duration_seconds: recording.seconds }),
    [sendUpload],
  );
  const recorder = useVoiceRecorder(handleRecorded);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const body = draft.trim();
    if (body === "") return;
    onSend({ message_type: "TEXT", body });
    setDraft("");
  }

  function handlePhotos(files: File[]): void {
    const [file] = files;
    if (file) void sendUpload(file, "photo", {});
  }

  const showMic = canAttach && recorder.isSupported && draft.trim() === "";
  const notice = error ?? recorder.error;

  return (
    <>
      {sending && (
        <p className="bubble__receipt" role="status" style={{ padding: "0 16px 6px" }}>
          Sending {sending}…
        </p>
      )}
      {notice && (
        <p className="field-error" role="alert" style={{ padding: "0 16px 8px" }}>
          {notice}
        </p>
      )}

      {recorder.isRecording ? (
        <div className="chat__composer" role="group" aria-label="Recording a voice note">
          <button
            type="button"
            className="round-btn round-btn--ghost"
            aria-label="Cancel voice note"
            onClick={recorder.cancel}
          >
            <Icon name="close" />
          </button>
          <div className="composer" aria-live="polite">
            <span className="status-dot status-dot--recording" aria-hidden="true" />
            <span style={{ marginLeft: 10, fontWeight: 600 }}>
              Recording {formatCountdown(recorder.seconds)}
            </span>
          </div>
          <button
            type="button"
            className="round-btn round-btn--recording"
            aria-label="Send voice note"
            onClick={recorder.finish}
          >
            <Icon name="send" />
          </button>
        </div>
      ) : (
        <form className="chat__composer" onSubmit={handleSubmit}>
          <label htmlFor="chat-msg" className="visually-hidden">
            Message
          </label>
          <div className="composer">
            <input
              id="chat-msg"
              type="text"
              placeholder="Type a message…"
              autoComplete="off"
              maxLength={2000}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
            />
            {canAttach && (
              <button
                type="button"
                className="round-btn round-btn--ghost"
                aria-label="Send a photo"
                disabled={sending !== null}
                onClick={() => setIsPickerOpen(true)}
              >
                <Icon name="camera" />
              </button>
            )}
          </div>
          {showMic ? (
            <button
              type="button"
              className="round-btn"
              aria-label="Record a voice note"
              disabled={sending !== null}
              onClick={() => void recorder.start()}
            >
              <Icon name="mic" />
            </button>
          ) : (
            <button
              type="submit"
              className="round-btn"
              aria-label="Send"
              disabled={draft.trim() === ""}
            >
              <Icon name="send" />
            </button>
          )}
          <PhotoPicker
            isOpen={isPickerOpen}
            onClose={() => setIsPickerOpen(false)}
            onPick={handlePhotos}
          />
        </form>
      )}
    </>
  );
}
