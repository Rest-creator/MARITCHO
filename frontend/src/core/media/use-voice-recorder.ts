import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

/*
 * Voice notes for chat (WEB-004), for people who would rather talk than
 * type. Recorded as low-bitrate Opus where the phone supports it, so two
 * minutes is roughly 360 KB.
 */

export const MAX_VOICE_SECONDS = 120;
const AUDIO_BITS_PER_SECOND = 24_000;
const PREFERRED_TYPES = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"] as const;

export interface VoiceRecording {
  blob: Blob;
  seconds: number;
}

interface VoiceRecorder {
  isSupported: boolean;
  isRecording: boolean;
  seconds: number;
  error: string | null;
  start: () => Promise<void>;
  /** Stop and hand the recording to `onRecorded`. */
  finish: () => void;
  /** Stop and throw the recording away. */
  cancel: () => void;
}

/** The best audio format this browser can record, or "" for its default. */
export function pickAudioType(isTypeSupported: (type: string) => boolean): string {
  return PREFERRED_TYPES.find((type) => isTypeSupported(type)) ?? "";
}

function canRecord(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.MediaRecorder !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function"
  );
}

const noopSubscribe = (): (() => void) => () => undefined;

export function useVoiceRecorder(onRecorded: (recording: VoiceRecording) => void): VoiceRecorder {
  const isSupported = useSyncExternalStore(noopSubscribe, canRecord, () => false);
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const startedAtRef = useRef(0);
  const isDiscardRef = useRef(false);
  const onRecordedRef = useRef(onRecorded);

  useEffect(() => {
    onRecordedRef.current = onRecorded;
  }, [onRecorded]);

  const release = useCallback((): void => {
    clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    recorderRef.current = null;
    setIsRecording(false);
  }, []);

  const stop = useCallback((isDiscard: boolean): void => {
    const recorder = recorderRef.current;
    if (recorder === null) return;
    isDiscardRef.current = isDiscard;
    if (recorder.state !== "inactive") recorder.stop();
  }, []);

  const start = useCallback(async (): Promise<void> => {
    if (!canRecord() || recorderRef.current !== null) return;
    setError(null);
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Microphone is off. Allow it in your phone settings to send voice notes.");
      return;
    }
    const mimeType = pickAudioType((type) => MediaRecorder.isTypeSupported(type));
    const recorder = new MediaRecorder(stream, {
      ...(mimeType === "" ? {} : { mimeType }),
      audioBitsPerSecond: AUDIO_BITS_PER_SECOND,
    });
    const chunks: Blob[] = [];
    recorder.ondataavailable = (event: BlobEvent) => {
      if (event.data.size > 0) chunks.push(event.data);
    };
    recorder.onstop = () => {
      const elapsed = Math.max(1, Math.round((Date.now() - startedAtRef.current) / 1000));
      const discard = isDiscardRef.current;
      release();
      if (!discard && chunks.length > 0) {
        const blob = new Blob(chunks, { type: recorder.mimeType || mimeType || "audio/webm" });
        onRecordedRef.current({ blob, seconds: Math.min(elapsed, MAX_VOICE_SECONDS) });
      }
    };

    streamRef.current = stream;
    recorderRef.current = recorder;
    isDiscardRef.current = false;
    startedAtRef.current = Date.now();
    setSeconds(0);
    setIsRecording(true);
    recorder.start();
    timerRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startedAtRef.current) / 1000);
      setSeconds(elapsed);
      if (elapsed >= MAX_VOICE_SECONDS) stop(false);
    }, 250);
  }, [release, stop]);

  // Leaving the screen mid-recording discards it and frees the microphone.
  useEffect(
    () => () => {
      isDiscardRef.current = true;
      const recorder = recorderRef.current;
      if (recorder !== null && recorder.state !== "inactive") recorder.stop();
      clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
    },
    [],
  );

  return {
    isSupported,
    isRecording,
    seconds,
    error,
    start,
    finish: useCallback(() => stop(false), [stop]),
    cancel: useCallback(() => stop(true), [stop]),
  };
}
